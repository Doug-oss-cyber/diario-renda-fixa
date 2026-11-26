import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from helpers.auxiliar import (
    CHAVE_FALSA, ENV_VALIDO, REGISTRO_CDB, ambiente, corpo_api,
    resposta_falsa, servidor_pronto,
)
from diario_rf import cli
from diario_rf.registro import configurar_registro, encerrar_registro

POST = "diario_rf.llm_client.requests.post"
RELATO = "RELATO-FICTICIO-XYZ aplicei 777 num CDB do Banco Zeta"


class TestRegistro(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(encerrar_registro)  # roda antes da limpeza da pasta (ordem inversa)
        self.log = Path(self.tmp.name) / "logs" / "diario.log"

    def rodar_cli(self, argv, resposta=None, **env):
        with ambiente(**{**ENV_VALIDO, "LOG_ARQUIVO": str(self.log), **env}), \
                mock.patch("sys.argv", ["cli", *argv]), \
                servidor_pronto(), \
                mock.patch(POST, return_value=resposta), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return cli.main()

    def conteudo(self) -> str:
        return self.log.read_text(encoding="utf-8")

    def test_cria_a_pasta_e_escreve(self):
        configurar_registro(str(self.log)).info("ola")
        self.assertIn("ola", self.conteudo())

    def test_sucesso_registra_so_metadados(self):
        resp = resposta_falsa(200, corpo_api(json.dumps(REGISTRO_CDB)))
        self.assertEqual(self.rodar_cli([RELATO], resp), 0)
        log = self.conteudo()
        for esperado in ("execucao_iniciada", "sucesso", "operacoes=1", "modelo=modelo-teste"):
            self.assertIn(esperado, log)
        # nada sensível: chave, relato do usuário, conteúdo devolvido pelo modelo
        for proibido in (CHAVE_FALSA, "RELATO-FICTICIO-XYZ", "Banco Zeta", "Banco Inter"):
            self.assertNotIn(proibido, log)

    def test_credencial_invalida_registra_so_o_tipo(self):
        self.assertEqual(self.rodar_cli([RELATO], resposta_falsa(401, {})), 1)
        log = self.conteudo()
        self.assertIn("CredencialInvalida", log)
        self.assertNotIn("recusou", log)  # a mensagem ao usuário não vai para o log
        self.assertNotIn(CHAVE_FALSA, log)
        self.assertNotIn("RELATO-FICTICIO-XYZ", log)

    def test_credencial_ausente_e_registrada(self):
        env = {k: v for k, v in ENV_VALIDO.items() if k != "LLM_API_KEY"}
        with ambiente(**env, LOG_ARQUIVO=str(self.log)), \
                mock.patch("sys.argv", ["cli", RELATO]), \
                servidor_pronto(), \
                mock.patch(POST, return_value=resposta_falsa(401, {})), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(), 1)
        self.assertIn("CredencialAusente", self.conteudo())

    def test_entrada_vazia_e_registrada(self):
        self.assertEqual(self.rodar_cli(["  "]), 1)
        self.assertIn("EntradaVazia", self.conteudo())

    def test_falha_ao_criar_o_log_nao_derruba_o_programa(self):
        bloqueio = Path(self.tmp.name) / "bloqueio.txt"
        bloqueio.write_text("sou um arquivo, não uma pasta")
        impossivel = str(bloqueio / "diario.log")
        configurar_registro(impossivel).info("não deve falhar")
        resp = resposta_falsa(200, corpo_api(json.dumps(REGISTRO_CDB)))
        self.assertEqual(self.rodar_cli([RELATO], resp, LOG_ARQUIVO=impossivel), 0)


if __name__ == "__main__":
    unittest.main()