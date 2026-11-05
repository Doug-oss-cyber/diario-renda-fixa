"""Cliente REST do LLM (formato Gemini generateContent).

Responsabilidades separadas: montar a requisição, chamar o modelo e extrair
o texto da resposta. Todo erro vira uma exceção de erros.py, sem expor a chave.
"""
import requests

from .config import Config
from .erros import (
    ConfiguracaoInvalida,
    CredencialInvalida,
    FalhaComunicacao,
    RespostaInvalida,
    ServicoIndisponivel,
    TempoEsgotado,
)
from .prompts import PROMPT_SISTEMA, montar_entrada

STATUS_INDISPONIVEL = {500, 502, 503, 504}


def montar_requisicao(texto: str, cfg: Config) -> tuple[str, dict, dict]:
    """Prepara URL, cabeçalhos e corpo. A chave vai no cabeçalho, nunca na URL."""
    url = f"{cfg.base_url.rstrip('/')}/models/{cfg.model}:generateContent"
    cabecalhos = {"x-goog-api-key": cfg.api_key, "Content-Type": "application/json"}
    corpo = {
        "system_instruction": {"parts": [{"text": PROMPT_SISTEMA}]},
        "contents": [{"role": "user", "parts": [{"text": montar_entrada(texto)}]}],
        "generationConfig": {
            "temperature": cfg.temperature,
            "maxOutputTokens": cfg.max_tokens,
            "responseMimeType": "application/json",
        },
    }
    return url, cabecalhos, corpo


def _detalhe_erro(resp: requests.Response) -> str:
    try:
        return str(resp.json().get("error", {}).get("message", "")).lower()
    except (ValueError, AttributeError):
        return ""


def _levantar_por_status(resp: requests.Response) -> None:
    status = resp.status_code
    if status in (401, 403) or (status == 400 and "api key" in _detalhe_erro(resp)):
        raise CredencialInvalida()
    if status == 404:
        raise ConfiguracaoInvalida(
            "Modelo ou endereço não encontrado. Confira LLM_MODEL e LLM_BASE_URL no .env."
        )
    if status == 429:
        raise ServicoIndisponivel(
            "Limite de uso do serviço atingido. Aguarde um pouco e tente novamente."
        )
    if status in STATUS_INDISPONIVEL:
        raise ServicoIndisponivel()
    raise FalhaComunicacao(f"A API recusou a solicitação (status HTTP {status}).")


def chamar_modelo(url: str, cabecalhos: dict, corpo: dict, timeout: int) -> dict:
    """Faz o POST e devolve o JSON da resposta, traduzindo as falhas previstas."""
    try:
        resp = requests.post(url, headers=cabecalhos, json=corpo, timeout=timeout)
    except requests.Timeout as e:
        raise TempoEsgotado() from e
    except requests.ConnectionError as e:
        raise FalhaComunicacao() from e
    except requests.RequestException as e:
        raise FalhaComunicacao("Falha inesperada ao chamar o serviço.") from e

    if not resp.ok:
        _levantar_por_status(resp)
    try:
        return resp.json()
    except ValueError as e:
        raise RespostaInvalida() from e


def extrair_texto(dados: dict) -> str:
    """Pega o texto gerado dentro do envelope da API."""
    try:
        texto = dados["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        bloqueio = dados.get("promptFeedback", {}).get("blockReason") if isinstance(dados, dict) else None
        if bloqueio:
            raise RespostaInvalida("O serviço bloqueou a resposta para esta entrada.") from None
        raise RespostaInvalida() from None
    if not isinstance(texto, str) or not texto.strip():
        raise RespostaInvalida()
    return texto


def extrair_registro(texto: str, cfg: Config) -> str:
    """Fluxo completo: monta, chama e extrai o texto bruto do modelo."""
    url, cabecalhos, corpo = montar_requisicao(texto, cfg)
    dados = chamar_modelo(url, cabecalhos, corpo, cfg.timeout)
    return extrair_texto(dados)