"""Sanidade do próprio gabarito: formato das linhas e valores aceitos."""
import json
import unittest
from pathlib import Path

from diario_rf.parser import TIPOS_OPERACAO, TIPOS_TAXA

CAMINHO = Path(__file__).parent / "gabarito.jsonl"


@unittest.skipUnless(CAMINHO.exists(), "tests/gabarito.jsonl não encontrado")
class TestGabarito(unittest.TestCase):
    def setUp(self):
        linhas = [l for l in CAMINHO.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.casos = [json.loads(l) for l in linhas]

    def test_estrutura_e_ids_unicos(self):
        self.assertTrue(self.casos)
        ids = [c["id"] for c in self.casos]
        self.assertEqual(len(ids), len(set(ids)))
        for c in self.casos:
            with self.subTest(id=c["id"]):
                for chave in ("id", "nome", "entrada", "esperado"):
                    self.assertIn(chave, c)
                self.assertTrue(c["entrada"].strip())

    def test_esperado_e_coerente_com_o_schema(self):
        for c in self.casos:
            with self.subTest(id=c["id"]):
                esp = c["esperado"]
                self.assertIsInstance(esp["operacao_valida"], bool)
                if esp["operacao_valida"]:
                    self.assertGreaterEqual(len(esp["operacoes"]), 1)
                else:
                    self.assertEqual(esp["operacoes"], [])
                for op in esp["operacoes"]:
                    self.assertIn(op["tipo_operacao"], TIPOS_OPERACAO)
                    self.assertTrue(op.get("taxa_tipo") is None or op["taxa_tipo"] in TIPOS_TAXA)


if __name__ == "__main__":
    unittest.main()