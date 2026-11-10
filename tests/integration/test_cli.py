import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from helpers.auxiliar import (
    CHAVE_FALSA, ENV_VALIDO, REGISTRO_CDB, ambiente, corpo_api, resposta_falsa, servidor_pronto
)
from diario_rf import cli

POST = "diario_rf.llm_client.requests.post"


def rodar(argv, resposta=None):
    saida, erro = io.StringIO(), io.StringIO()
    with mock.patch("sys.argv", ["cli", *argv]), \
            servidor_pronto(), \
            mock.patch(POST, return_value=resposta), \
            redirect_stdout(saida), redirect_stderr(erro):
        codigo = cli.main()
    return codigo, saida.getvalue(), erro.getvalue()


class TestCli(unittest.TestCase):
    def conferir_erro(self, codigo, saida, erro, trecho):
        self.assertEqual(codigo, 1)
        self.assertEqual(saida, "")
        self.assertIn(trecho, erro)
        self.assertNotIn("Traceback", erro)
        self.assertNotIn(CHAVE_FALSA, erro)

    def test_sucesso(self):
        resp = resposta_falsa(200, corpo_api(json.dumps(REGISTRO_CDB)))
        with ambiente(**ENV_VALIDO):
            codigo, saida, erro = rodar(["Apliquei 10 mil num CDB"], resp)
        self.assertEqual(codigo, 0)
        self.assertEqual(erro, "")
        self.assertTrue(json.loads(saida)["operacao_valida"])

    def test_entrada_vazia_nao_chama_a_api(self):
        for entrada in ("", "   "):
            with self.subTest(entrada=repr(entrada)):
                with ambiente(**ENV_VALIDO), mock.patch(POST) as post:
                    with mock.patch("sys.argv", ["cli", entrada]), \
                            redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as erro:
                        codigo = cli.main()
                self.assertEqual(codigo, 1)
                self.assertIn("vazia", erro.getvalue())
                post.assert_not_called()

    def test_credencial_ausente(self):
        env = {k: v for k, v in ENV_VALIDO.items() if k != "LLM_API_KEY"}
        with ambiente(**env):
            self.conferir_erro(*rodar(["oi"], resposta_falsa(401, {})), "Credencial ausente")

    def test_credencial_invalida(self):
        with ambiente(**ENV_VALIDO):
            self.conferir_erro(*rodar(["oi"], resposta_falsa(401, {})), "recusou a credencial")

    def test_servico_indisponivel(self):
        with ambiente(**ENV_VALIDO):
            self.conferir_erro(*rodar(["oi"], resposta_falsa(503, {})), "indisponível")

    def test_resposta_que_nao_e_json(self):
        resp = resposta_falsa(200, corpo_api("Desculpe, não posso ajudar."))
        with ambiente(**ENV_VALIDO):
            self.conferir_erro(*rodar(["oi"], resp), "JSON válido")

    def test_resposta_vazia(self):
        with ambiente(**ENV_VALIDO):
            self.conferir_erro(*rodar(["oi"], resposta_falsa(200, {"message": {}})),
                               "vazia ou em formato inesperado")

    def test_anotacao_pela_variavel_de_ambiente(self):
        resp = resposta_falsa(200, corpo_api(json.dumps(REGISTRO_CDB)))
        with ambiente(**ENV_VALIDO, DIARIO_ANOTACAO="Apliquei 10 mil num CDB"):
            codigo, saida, erro = rodar([], resp)
        self.assertEqual(codigo, 0)

if __name__ == "__main__":
    unittest.main()