import json
import unittest
from dataclasses import replace
from unittest import mock

import requests

from helpers.auxiliar import (
    CHAVE_FALSA, REGISTRO_CDB, corpo_api, resposta_falsa, servidor_pronto,
)
from diario_rf.config import Config
from diario_rf.erros import (
    ConfiguracaoInvalida, CredencialAusente, CredencialInvalida, FalhaComunicacao,
    RespostaInvalida, ServicoIndisponivel, TempoEsgotado,
)
from diario_rf.llm_client import (
    aguardar_prontidao, chamar_modelo, extrair_registro, extrair_texto, montar_requisicao,
)

CFG = Config(api_key=CHAVE_FALSA, base_url="https://llm.exemplo.test:9001/",
             model="modelo-teste", temperature=0.0, max_tokens=100, timeout=5,
             espera_prontidao=0)
POST = "diario_rf.llm_client.requests.post"
GET = "diario_rf.llm_client.requests.get"
COM_CHAVE = {"Authorization": f"Bearer {CHAVE_FALSA}"}
SEM_CHAVE = {"Content-Type": "application/json"}


def chamar(cabecalhos=None):
    cab = COM_CHAVE if cabecalhos is None else cabecalhos
    return chamar_modelo("https://x.test", cab, {}, 5)


class Relogio:
    """Relógio falso: dormir só avança o tempo, sem esperar de verdade."""

    def __init__(self):
        self.t = 0

    def agora(self):
        return self.t

    def dormir(self, segundos):
        self.t += segundos


class TestMontarRequisicao(unittest.TestCase):
    def setUp(self):
        self.url, self.cabecalhos, self.corpo = montar_requisicao("relato", CFG)

    def test_url_montada_sem_barra_duplicada(self):
        self.assertEqual(self.url, "https://llm.exemplo.test:9001/api/chat")

    def test_chave_so_no_cabecalho(self):
        self.assertEqual(self.cabecalhos["Authorization"], f"Bearer {CHAVE_FALSA}")
        self.assertNotIn(CHAVE_FALSA, self.url)
        self.assertNotIn(CHAVE_FALSA, json.dumps(self.corpo))

    def test_sem_chave_nao_envia_authorization(self):
        _, cabecalhos, _ = montar_requisicao("relato", replace(CFG, api_key=""))
        self.assertNotIn("Authorization", cabecalhos)

    def test_parametros_no_corpo(self):
        self.assertEqual(self.corpo["model"], "modelo-teste")
        self.assertIs(self.corpo["stream"], False)
        self.assertEqual(self.corpo["format"], "json")
        self.assertIs(self.corpo["think"], False)
        self.assertEqual(self.corpo["options"]["temperature"], 0.0)
        self.assertEqual(self.corpo["options"]["num_predict"], 100)

    def test_prompt_de_sistema_vem_antes_do_relato(self):
        self.assertEqual(self.corpo["messages"][0]["role"], "system")
        self.assertEqual(self.corpo["messages"][1]["role"], "user")

    def test_relato_vai_entre_tags(self):
        texto = self.corpo["messages"][1]["content"]
        self.assertTrue(texto.startswith("<anotacao>") and texto.endswith("</anotacao>"))


class TestChamarModelo(unittest.TestCase):
    def test_sucesso_devolve_o_json(self):
        with mock.patch(POST, return_value=resposta_falsa(200, {"ok": 1})):
            self.assertEqual(chamar(), {"ok": 1})

    def test_status_http_viram_a_excecao_certa(self):
        casos = [
            (401, {}, CredencialInvalida), (403, {}, CredencialInvalida),
            (400, {"error": "outra"}, FalhaComunicacao),
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

    def test_401_ou_403_sem_chave_vira_credencial_ausente(self):
        for status in (401, 403):
            with self.subTest(status=status):
                with mock.patch(POST, return_value=resposta_falsa(status, {})):
                    with self.assertRaises(CredencialAusente):
                        chamar(SEM_CHAVE)

    def test_mensagens_de_erro_nao_expoem_a_chave(self):
        for status in (400, 401, 403, 404, 429, 503, 418):
            for cabecalhos in (COM_CHAVE, SEM_CHAVE):
                with self.subTest(status=status, com_chave=cabecalhos is COM_CHAVE):
                    corpo = {"error": f"invalid token {CHAVE_FALSA}"}
                    with mock.patch(POST, return_value=resposta_falsa(status, corpo)):
                        with self.assertRaises(Exception) as ctx:
                            chamar(cabecalhos)
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
        for nome, dados in [("sem message", {}), ("message vazio", {"message": {}}),
                            ("message nao é dict", {"message": "x"}),
                            ("texto vazio", corpo_api("   ")), ("texto nao string", corpo_api(123)),
                            ("nao é dict", [])]:
            with self.subTest(nome):
                with self.assertRaises(RespostaInvalida):
                    extrair_texto(dados)

    def test_resposta_cortada_pede_mais_tokens(self):
        dados = {"message": {"content": '{"operacao_valida"'}, "done_reason": "length"}
        with self.assertRaises(RespostaInvalida) as ctx:
            extrair_texto(dados)
        self.assertIn("LLM_MAX_TOKENS", ctx.exception.mensagem)


class TestAguardarProntidao(unittest.TestCase):
    def test_espera_ate_ficar_pronto(self):
        rel = Relogio()
        efeitos = [requests.ConnectionError(), resposta_falsa(503, {}), resposta_falsa(200, {})]
        with mock.patch(GET, side_effect=efeitos) as get:
            aguardar_prontidao(replace(CFG, espera_prontidao=60), rel.dormir, rel.agora)
        self.assertEqual(get.call_count, 3)

    def test_esgota_a_espera(self):
        rel = Relogio()
        with mock.patch(GET, side_effect=requests.ConnectionError()):
            with self.assertRaises(ServicoIndisponivel) as ctx:
                aguardar_prontidao(replace(CFG, espera_prontidao=30), rel.dormir, rel.agora)
        self.assertIn("ainda não respondeu", ctx.exception.mensagem)

    def test_resposta_http_que_nao_seja_5xx_conta_como_pronto(self):
        with mock.patch(GET, return_value=resposta_falsa(404, {})) as get:
            aguardar_prontidao(CFG)
        self.assertEqual(get.call_count, 1)

    def test_espera_zero_tenta_uma_vez_so(self):
        with mock.patch(GET, side_effect=requests.ConnectionError()) as get:
            with self.assertRaises(ServicoIndisponivel):
                aguardar_prontidao(CFG, lambda s: None)
        self.assertEqual(get.call_count, 1)


class TestFluxoCompleto(unittest.TestCase):
    def test_extrair_registro_devolve_o_texto_do_modelo(self):
        texto = json.dumps(REGISTRO_CDB)
        with servidor_pronto(), \
                mock.patch(POST, return_value=resposta_falsa(200, corpo_api(texto))) as post:
            self.assertEqual(extrair_registro("relato", CFG), texto)
        self.assertEqual(post.call_args.kwargs["timeout"], 5)

    def test_servidor_fora_do_ar_nao_chega_a_chamar_o_modelo(self):
        with mock.patch(GET, side_effect=requests.ConnectionError()), \
                mock.patch(POST) as post:
            with self.assertRaises(ServicoIndisponivel):
                extrair_registro("relato", CFG)
        post.assert_not_called()


if __name__ == "__main__":
    unittest.main()