"""Chamada REST ao LLM (formato da API Gemini: generateContent)."""
import requests

from .config import Config
from .prompts import PROMPT_SISTEMA, montar_entrada


class LLMError(Exception):
    """Falha na comunicação com o LLM ou resposta inesperada."""


def extrair_registro(texto: str, cfg: Config) -> str:
    """Envia a anotação ao modelo e devolve o texto bruto da resposta."""
    url = f"{cfg.base_url.rstrip('/')}/models/{cfg.model}:generateContent"
    # A chave vai no cabeçalho (e não na URL) para não vazar em logs.
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

    try:
        resp = requests.post(url, headers=cabecalhos, json=corpo, timeout=cfg.timeout)
        resp.raise_for_status()
        dados = resp.json()
        return dados["candidates"][0]["content"]["parts"][0]["text"]
    except requests.RequestException as e:
        raise LLMError(f"Falha na chamada à API: {e}") from e
    except (KeyError, IndexError, ValueError) as e:
        raise LLMError("A API respondeu num formato inesperado.") from e