"""Tratamento da resposta do modelo: JSON, estrutura, valores aceitos e campos ausentes."""
import json
import re

from .erros import RespostaInvalida

TIPOS_OPERACAO = {"aplicacao", "resgate", "resgate_parcial", "vencimento"}
TIPOS_TAXA = {"percentual_do_indexador", "indexador_mais_spread", "prefixada"}

# Campos que, se estiverem nulos, entram em campos_ausentes
# (motivo_declarado fica de fora, como definido no prompt).
CAMPOS_ESPERADOS = (
    "data_operacao", "produto", "emissor", "valor", "indexador",
    "taxa_tipo", "taxa_valor", "data_vencimento", "liquidez",
)

RE_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_VENCIMENTO = re.compile(r"^\d{4}(-\d{2})?$")


def _remover_cercas(texto: str) -> str:
    """Tira os ```json ... ``` que alguns modelos colocam ao redor do JSON."""
    t = texto.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    return t.strip()


def _texto_ou_nulo(valor, nome: str):
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise RespostaInvalida(f"O campo '{nome}' deveria ser texto ou nulo.")
    return valor.strip() or None


def _validar_operacao(op, posicao: int) -> dict:
    n = posicao + 1
    if not isinstance(op, dict):
        raise RespostaInvalida(f"A operação {n} não é um objeto JSON.")

    tipo = op.get("tipo_operacao")
    if tipo not in TIPOS_OPERACAO:
        raise RespostaInvalida(f"Operação {n}: 'tipo_operacao' ausente ou fora dos valores aceitos.")

    taxa_tipo = op.get("taxa_tipo")
    if taxa_tipo is not None and taxa_tipo not in TIPOS_TAXA:
        raise RespostaInvalida(f"Operação {n}: 'taxa_tipo' fora dos valores aceitos.")

    valor = op.get("valor")
    if valor is not None:
        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor < 0:
            raise RespostaInvalida(f"Operação {n}: 'valor' deveria ser um número não negativo ou nulo.")
        valor = float(valor)

    data_operacao = _texto_ou_nulo(op.get("data_operacao"), "data_operacao")
    if data_operacao is not None and not RE_DATA.match(data_operacao):
        raise RespostaInvalida(f"Operação {n}: 'data_operacao' fora do formato AAAA-MM-DD.")

    data_vencimento = _texto_ou_nulo(op.get("data_vencimento"), "data_vencimento")
    if data_vencimento is not None and not RE_VENCIMENTO.match(data_vencimento):
        raise RespostaInvalida(f"Operação {n}: 'data_vencimento' fora do formato AAAA ou AAAA-MM.")

    ambiguidades = op.get("ambiguidades", [])
    if not isinstance(ambiguidades, list) or not all(isinstance(a, str) for a in ambiguidades):
        raise RespostaInvalida(f"Operação {n}: 'ambiguidades' deveria ser uma lista de textos.")

    registro = {
        "tipo_operacao": tipo,
        "data_operacao": data_operacao,
        "produto": _texto_ou_nulo(op.get("produto"), "produto"),
        "emissor": _texto_ou_nulo(op.get("emissor"), "emissor"),
        "valor": valor,
        "indexador": _texto_ou_nulo(op.get("indexador"), "indexador"),
        "taxa_tipo": taxa_tipo,
        "taxa_valor": _texto_ou_nulo(op.get("taxa_valor"), "taxa_valor"),
        "data_vencimento": data_vencimento,
        "liquidez": _texto_ou_nulo(op.get("liquidez"), "liquidez"),
        "motivo_declarado": _texto_ou_nulo(op.get("motivo_declarado"), "motivo_declarado"),
    }
    # Calculado aqui, e não pelo modelo: a lista tem de refletir os campos realmente nulos.
    registro["campos_ausentes"] = [c for c in CAMPOS_ESPERADOS if registro[c] is None]
    registro["ambiguidades"] = ambiguidades
    return registro


def interpretar_resposta(texto: str) -> dict:
    """Converte o texto do modelo num registro validado e normalizado."""
    try:
        dados = json.loads(_remover_cercas(texto))
    except json.JSONDecodeError:
        raise RespostaInvalida("O modelo devolveu algo que não é um JSON válido.") from None
    if not isinstance(dados, dict):
        raise RespostaInvalida("O JSON do modelo não tem o formato esperado (objeto).")

    valida = dados.get("operacao_valida")
    if not isinstance(valida, bool):
        raise RespostaInvalida("O campo 'operacao_valida' está ausente ou não é verdadeiro/falso.")

    brutas = dados.get("operacoes")
    if not isinstance(brutas, list):
        raise RespostaInvalida("O campo 'operacoes' está ausente ou não é uma lista.")
    operacoes = [_validar_operacao(op, i) for i, op in enumerate(brutas)]

    if valida and not operacoes:
        raise RespostaInvalida("O modelo marcou a anotação como válida, mas não listou operações.")
    if not valida and operacoes:
        raise RespostaInvalida("O modelo marcou a anotação como inválida, mas listou operações.")

    return {
        "operacao_valida": valida,
        "motivo_invalida": _texto_ou_nulo(dados.get("motivo_invalida"), "motivo_invalida"),
        "operacoes": operacoes,
        "observacoes": _texto_ou_nulo(dados.get("observacoes"), "observacoes"),
    }