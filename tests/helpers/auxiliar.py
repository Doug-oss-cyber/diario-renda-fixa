"""Apoio comum aos testes: ambiente isolado, respostas simuladas e registros de exemplo.

Todos os testes desta pasta são SIMULADOS (sem chamada real ao LLM).
Os testes reais ficam documentados no README (seção de evidências).
"""
import json
import os
from contextlib import contextmanager
from copy import deepcopy
from unittest import mock

CHAVE_FALSA = "AIzaChaveDeTesteNaoReal"
ENV_VALIDO = {
    "LLM_API_KEY": CHAVE_FALSA,
    "LLM_BASE_URL": "https://api.exemplo.test/v1beta",
    "LLM_MODEL": "modelo-teste",
}

OPERACAO_CDB = {
    "tipo_operacao": "aplicacao", "data_operacao": None, "produto": "CDB",
    "emissor": "Banco Inter", "valor": 10000.0, "indexador": "CDI",
    "taxa_tipo": "percentual_do_indexador", "taxa_valor": "105%",
    "data_vencimento": "2029-01", "liquidez": "no vencimento",
    "motivo_declarado": None, "campos_ausentes": ["data_operacao"], "ambiguidades": [],
}
REGISTRO_CDB = {
    "operacao_valida": True, "motivo_invalida": None,
    "operacoes": [OPERACAO_CDB], "observacoes": None,
}
REGISTRO_INVALIDO = {
    "operacao_valida": False, "motivo_invalida": "Intenção; nenhuma operação realizada.",
    "operacoes": [], "observacoes": None,
}


@contextmanager
def ambiente(**variaveis):
    """Só as variáveis informadas existem e o .env real nunca é lido."""
    with mock.patch.dict(os.environ, variaveis, clear=True), \
            mock.patch("diario_rf.config.load_dotenv"):
        yield


def resposta_falsa(status=200, corpo=None):
    """Simula um requests.Response. corpo=None simula uma resposta sem JSON."""
    r = mock.Mock()
    r.status_code = status
    r.ok = status < 400
    if corpo is None:
        r.json.side_effect = ValueError("sem json")
    else:
        r.json.return_value = corpo
    return r


def corpo_api(texto):
    """Envelope de sucesso no formato da API (generateContent)."""
    return {"candidates": [{"content": {"parts": [{"text": texto}]}}]}


def registro_com_operacao(**mudancas) -> str:
    """JSON do registro de exemplo com campos da operação alterados."""
    r = deepcopy(REGISTRO_CDB)
    r["operacoes"][0].update(mudancas)
    return json.dumps(r)