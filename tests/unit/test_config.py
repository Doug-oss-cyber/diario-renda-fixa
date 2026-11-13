import unittest
import tempfile

from helpers.auxiliar import CHAVE_FALSA, ENV_VALIDO, ambiente
from diario_rf.config import carregar_config
from diario_rf.erros import ConfiguracaoInvalida


class TestConfig(unittest.TestCase):
    def test_credencial_e_opcional(self):
        with ambiente(LLM_BASE_URL=ENV_VALIDO["LLM_BASE_URL"], LLM_MODEL="m"):
            self.assertEqual(carregar_config().api_key, "")

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
                            ("LLM_TIMEOUT_SEGUNDOS", "-3"),
                            ("LLM_ESPERA_PRONTIDAO_SEGUNDOS", "abc"), ("LLM_ESPERA_PRONTIDAO_SEGUNDOS", "-1")]:
            with self.subTest(nome=nome, valor=valor):
                with ambiente(**{**ENV_VALIDO, nome: valor}):
                    with self.assertRaises(ConfiguracaoInvalida):
                        carregar_config()

    def test_valores_padrao(self):
        with ambiente(**ENV_VALIDO):
            cfg = carregar_config()
        self.assertEqual((cfg.temperature, cfg.max_tokens, cfg.timeout, cfg.espera_prontidao), (0.0, 2048, 120, 180))

    def test_valores_personalizados(self):
        extra = {"LLM_TEMPERATURE": "0.2", "LLM_MAX_TOKENS": "500", "LLM_TIMEOUT_SEGUNDOS": "150", "LLM_ESPERA_PRONTIDAO_SEGUNDOS": "210"}
        with ambiente(**ENV_VALIDO, **extra):
            cfg = carregar_config()
        self.assertEqual((cfg.temperature, cfg.max_tokens, cfg.timeout, cfg.espera_prontidao), (0.2, 500, 150, 210))
        self.assertEqual(cfg.api_key, CHAVE_FALSA)

    def test_ssl_padrao_verifica(self):
        with ambiente(**ENV_VALIDO):
            self.assertIs(carregar_config().verificar_ssl, True)

    def test_ssl_pode_ser_desativado_explicitamente(self):
        with ambiente(**ENV_VALIDO, LLM_VERIFICAR_SSL="false"):
            self.assertIs(carregar_config().verificar_ssl, False)

    def test_ssl_valor_invalido(self):
        with ambiente(**ENV_VALIDO, LLM_VERIFICAR_SSL="talvez"):
            with self.assertRaises(ConfiguracaoInvalida):
                carregar_config()

    def test_ca_bundle_existente_tem_precedencia(self):
        with tempfile.NamedTemporaryFile(suffix=".pem") as f:
            with ambiente(**ENV_VALIDO, LLM_CA_BUNDLE=f.name, LLM_VERIFICAR_SSL="false"):
                self.assertEqual(carregar_config().verificar_ssl, f.name)

    def test_ca_bundle_inexistente(self):
        with ambiente(**ENV_VALIDO, LLM_CA_BUNDLE="/nao/existe.pem"):
            with self.assertRaises(ConfiguracaoInvalida):
                carregar_config()


if __name__ == "__main__":
    unittest.main()