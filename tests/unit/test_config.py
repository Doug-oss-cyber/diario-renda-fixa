import unittest

from helpers.auxiliar import CHAVE_FALSA, ENV_VALIDO, ambiente
from diario_rf.config import carregar_config
from diario_rf.erros import ConfiguracaoInvalida, CredencialAusente


class TestConfig(unittest.TestCase):
    def test_credencial_ausente(self):
        with ambiente():
            with self.assertRaises(CredencialAusente):
                carregar_config()

    def test_credencial_so_com_espacos(self):
        with ambiente(LLM_API_KEY="   "):
            with self.assertRaises(CredencialAusente):
                carregar_config()

    def test_modelo_e_url_ausentes(self):
        with ambiente(LLM_API_KEY=CHAVE_FALSA):
            with self.assertRaises(ConfiguracaoInvalida) as ctx:
                carregar_config()
        self.assertIn("LLM_BASE_URL", ctx.exception.mensagem)
        self.assertIn("LLM_MODEL", ctx.exception.mensagem)

    def test_url_sem_protocolo(self):
        with ambiente(**{**ENV_VALIDO, "LLM_BASE_URL": "api.exemplo.test"}):
            with self.assertRaises(ConfiguracaoInvalida):
                carregar_config()

    def test_numeros_invalidos(self):
        for nome, valor in [("LLM_TEMPERATURE", "quente"), ("LLM_MAX_TOKENS", "muitos"),
                            ("LLM_TIMEOUT_SEGUNDOS", "1.5"), ("LLM_MAX_TOKENS", "0"),
                            ("LLM_TIMEOUT_SEGUNDOS", "-3")]:
            with self.subTest(nome=nome, valor=valor):
                with ambiente(**{**ENV_VALIDO, nome: valor}):
                    with self.assertRaises(ConfiguracaoInvalida):
                        carregar_config()

    def test_valores_padrao(self):
        with ambiente(**ENV_VALIDO):
            cfg = carregar_config()
        self.assertEqual((cfg.temperature, cfg.max_tokens, cfg.timeout), (0.0, 2048, 30))

    def test_valores_personalizados(self):
        extra = {"LLM_TEMPERATURE": "0.2", "LLM_MAX_TOKENS": "500", "LLM_TIMEOUT_SEGUNDOS": "60"}
        with ambiente(**ENV_VALIDO, **extra):
            cfg = carregar_config()
        self.assertEqual((cfg.temperature, cfg.max_tokens, cfg.timeout), (0.2, 500, 60))
        self.assertEqual(cfg.api_key, CHAVE_FALSA)


if __name__ == "__main__":
    unittest.main()