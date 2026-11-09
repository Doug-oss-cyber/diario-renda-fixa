import json
import unittest
from unittest import mock

import requests

from helpers.auxiliar import CHAVE_FALSA, REGISTRO_CDB, corpo_api, resposta_falsa
from diario_rf.config import Config
from diario_rf.erros import (
    ConfiguracaoInvalida, CredencialInvalida, FalhaComunicacao,
    RespostaInvalida, ServicoIndisponivel, TempoEsgotado,
)
from diario_rf.llm_client import (
    chamar_modelo, extrair_registro, extrair_texto, montar_requisicao,
)

CFG = Config(api_key=CHAVE_FALSA, base_url="https://api.exemplo.test/v1beta/",
             model="modelo-teste", temperature=0.0, max_tokens=100, timeout=5)
POST = "diario_rf.llm_client.requests.post"


def chamar():
    return chamar_modelo("https://x.test", {"x-goog-api-key": CHAVE_FALSA}, {}, 5)


class TestMontarRequisicao(unittest.TestCase):
    def setUp(self):
        self.url, self.cabecalhos, self.corpo = montar_requisicao("relato", CFG)

    def test_url_montada_sem_barra_duplicada(self):
        self.assertEqual(self.url, "https://api.exemplo.test/v1beta/models/modelo-teste:generateContent")

    def test_chave_so_no_cabecalho(self):
        self.assertEqual(self.cabecalhos["x-goog-api-key"], CHAVE_FALSA)
        self.assertNotIn(CHAVE_FALSA, self.url)
        self.assertNotIn(CHAVE_FALSA, json.dumps(self.corpo))

    def test_parametros_no_corpo(self):
        cfg_ger = self.corpo["generationConfig"]
        self.assertEqual(cfg_ger["temperature"], 0.0)
        self.assertEqual(cfg_ger["maxOutputTokens"], 100)

    def test_relato_vai_entre_tags(self):
        texto = self.corpo["contents"][0]["parts"][0]["text"]
        self.assertTrue(texto.startswith("<anotacao>") and texto.endswith("</anotacao>"))


class TestChamarModelo(unittest.TestCase):
    def test_sucesso_devolve_o_json(self):
        with mock.patch(POST, return_value=resposta_falsa(200, {"ok": 1})):
            self.assertEqual(chamar(), {"ok": 1})

    def test_status_http_viram_a_excecao_certa(self):
        chave_msg = {"error": {"message": "API key not valid. Please pass a valid API key."}}
        casos = [
            (401, {}, CredencialInvalida), (403, {}, CredencialInvalida),
            (400, chave_msg, CredencialInvalida), (400, {"error": {"message": "outra"}}, FalhaComunicacao),
            (404, {}, ConfiguracaoInvalida), (429, {}, ServicoIndisponivel),
            (500, {}, ServicoIndisponivel), (502, {}, ServicoIndisponivel),
            (503, {}, ServicoIndisponivel), (504, {}, ServicoIndisponivel),
            (418, None, FalhaComunicacao),
        ]
        for status, corpo, esperada in casos:
            with self.subTest(status=status):
                with mock.patch(POST, return_value=resposta_falsa(status, corpo)):
                    with self.assertRaises(esperada):
                        chamar()

    def test_mensagens_de_erro_nao_expoem_a_chave(self):
        for status in (400, 401, 403, 404, 429, 503, 418):
            with self.subTest(status=status):
                corpo = {"error": {"message": f"API key not valid: {CHAVE_FALSA}"}}
                with mock.patch(POST, return_value=resposta_falsa(status, corpo)):
                    with self.assertRaises(Exception) as ctx:
                        chamar()
                self.assertNotIn(CHAVE_FALSA, ctx.exception.mensagem)
                self.assertNotIn(CHAVE_FALSA, str(ctx.exception))

    def test_timeout(self):
        with mock.patch(POST, side_effect=requests.Timeout("lento")):
            with self.assertRaises(TempoEsgotado):
                chamar()

    def test_sem_rede(self):
        with mock.patch(POST, side_effect=requests.ConnectionError("caiu")):
            with self.assertRaises(FalhaComunicacao):
                chamar()

    def test_falha_inesperada_de_requests(self):
        with mock.patch(POST, side_effect=requests.RequestException("?")):
            with self.assertRaises(FalhaComunicacao):
                chamar()

    def test_resposta_200_sem_json(self):
        with mock.patch(POST, return_value=resposta_falsa(200, None)):
            with self.assertRaises(RespostaInvalida):
                chamar()


class TestExtrairTexto(unittest.TestCase):
    def test_texto_valido(self):
        self.assertEqual(extrair_texto(corpo_api("abc")), "abc")

    def test_formatos_inesperados(self):
        for nome, dados in [("sem candidates", {}), ("candidates vazio", {"candidates": []}),
                            ("sem parts", {"candidates": [{"content": {}}]}),
                            ("texto vazio", corpo_api("   ")), ("texto nao string", corpo_api(123)),
                            ("nao é dict", [])]:
            with self.subTest(nome):
                with self.assertRaises(RespostaInvalida):
                    extrair_texto(dados)

    def test_resposta_bloqueada_tem_mensagem_propria(self):
        with self.assertRaises(RespostaInvalida) as ctx:
            extrair_texto({"promptFeedback": {"blockReason": "SAFETY"}})
        self.assertIn("bloqueou", ctx.exception.mensagem)


class TestFluxoCompleto(unittest.TestCase):
    def test_extrair_registro_devolve_o_texto_do_modelo(self):
        texto = json.dumps(REGISTRO_CDB)
        with mock.patch(POST, return_value=resposta_falsa(200, corpo_api(texto))) as post:
            self.assertEqual(extrair_registro("relato", CFG), texto)
        self.assertEqual(post.call_args.kwargs["timeout"], 5)


if __name__ == "__main__":
    unittest.main()