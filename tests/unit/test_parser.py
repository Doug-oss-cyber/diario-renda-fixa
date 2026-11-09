import json
import unittest

from helpers.auxiliar import REGISTRO_CDB, REGISTRO_INVALIDO, registro_com_operacao
from diario_rf.erros import RespostaInvalida
from diario_rf.parser import interpretar_resposta


class TestParserAceita(unittest.TestCase):
    def test_registro_valido(self):
        r = interpretar_resposta(json.dumps(REGISTRO_CDB))
        self.assertTrue(r["operacao_valida"])
        self.assertEqual(r["operacoes"][0]["valor"], 10000.0)

    def test_anotacao_sem_operacao(self):
        r = interpretar_resposta(json.dumps(REGISTRO_INVALIDO))
        self.assertFalse(r["operacao_valida"])
        self.assertEqual(r["operacoes"], [])

    def test_cercas_de_markdown_sao_removidas(self):
        texto = "```json\n" + json.dumps(REGISTRO_INVALIDO) + "\n```"
        self.assertFalse(interpretar_resposta(texto)["operacao_valida"])

    def test_campos_ausentes_sao_recalculados_pelo_codigo(self):
        # o modelo declara lista vazia, mas emissor e data_operacao estão nulos
        r = interpretar_resposta(registro_com_operacao(emissor=None, campos_ausentes=[]))
        self.assertEqual(r["operacoes"][0]["campos_ausentes"], ["data_operacao", "emissor"])

    def test_motivo_declarado_nao_conta_como_ausente(self):
        r = interpretar_resposta(registro_com_operacao(motivo_declarado=None))
        self.assertNotIn("motivo_declarado", r["operacoes"][0]["campos_ausentes"])

    def test_campos_faltando_viram_nulo(self):
        bruto = {"operacao_valida": True, "operacoes": [{"tipo_operacao": "resgate"}]}
        op = interpretar_resposta(json.dumps(bruto))["operacoes"][0]
        self.assertIsNone(op["valor"])
        self.assertEqual(op["ambiguidades"], [])

    def test_texto_vazio_vira_nulo_e_valor_inteiro_vira_float(self):
        op = interpretar_resposta(registro_com_operacao(emissor="  ", valor=500))["operacoes"][0]
        self.assertIsNone(op["emissor"])
        self.assertEqual(op["valor"], 500.0)
        self.assertIsInstance(op["valor"], float)

    def test_vencimento_so_com_ano(self):
        op = interpretar_resposta(registro_com_operacao(data_vencimento="2040"))["operacoes"][0]
        self.assertEqual(op["data_vencimento"], "2040")


class TestParserRejeita(unittest.TestCase):
    def test_respostas_defeituosas(self):
        valido = json.dumps(REGISTRO_CDB)
        casos = {
            "texto qualquer": "Claro! Aqui está o seu registro.",
            "json cortado": valido[:60],
            "vazio": "",
            "lista no topo": "[]",
            "sem operacao_valida": '{"operacoes": []}',
            "operacao_valida texto": '{"operacao_valida": "sim", "operacoes": []}',
            "operacoes nao e lista": '{"operacao_valida": true, "operacoes": "x"}',
            "valida sem operacoes": '{"operacao_valida": true, "operacoes": []}',
            "invalida com operacoes": valido.replace('"operacao_valida": true', '"operacao_valida": false'),
            "operacao nao e objeto": '{"operacao_valida": true, "operacoes": ["x"]}',
            "tipo_operacao invalido": registro_com_operacao(tipo_operacao="compra"),
            "tipo_operacao ausente": registro_com_operacao(tipo_operacao=None),
            "taxa_tipo invalido": registro_com_operacao(taxa_tipo="fixa"),
            "valor texto": registro_com_operacao(valor="1500"),
            "valor negativo": registro_com_operacao(valor=-5),
            "valor booleano": registro_com_operacao(valor=True),
            "data_operacao errada": registro_com_operacao(data_operacao="15/10"),
            "data_vencimento errada": registro_com_operacao(data_vencimento="jan/2029"),
            "ambiguidades nao lista": registro_com_operacao(ambiguidades="x"),
            "campo texto com numero": registro_com_operacao(produto=123),
        }
        for nome, texto in casos.items():
            with self.subTest(nome):
                with self.assertRaises(RespostaInvalida):
                    interpretar_resposta(texto)


if __name__ == "__main__":
    unittest.main()