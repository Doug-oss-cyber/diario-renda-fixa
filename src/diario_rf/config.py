"""Leitura e validação das configurações a partir de variáveis de ambiente (.env)."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

from .erros import ConfiguracaoInvalida, CredencialAusente


@dataclass(frozen=True)
class Config:
    api_key: str
    base_url: str
    model: str
    temperature: float
    max_tokens: int
    timeout: int


def _ler(nome: str) -> str:
    return (os.getenv(nome) or "").strip()


def carregar_config() -> Config:
    load_dotenv()

    api_key = _ler("LLM_API_KEY")
    if not api_key:
        raise CredencialAusente()

    faltando = [n for n in ("LLM_BASE_URL", "LLM_MODEL") if not _ler(n)]
    if faltando:
        raise ConfiguracaoInvalida(
            "Variáveis ausentes no .env: " + ", ".join(faltando) + ". Veja o .env.example."
        )

    base_url = _ler("LLM_BASE_URL")
    if not base_url.startswith(("http://", "https://")):
        raise ConfiguracaoInvalida("LLM_BASE_URL deve começar com http:// ou https://.")

    try:
        temperature = float(_ler("LLM_TEMPERATURE") or "0")
        max_tokens = int(_ler("LLM_MAX_TOKENS") or "2048")
        timeout = int(_ler("LLM_TIMEOUT_SEGUNDOS") or "30")
    except ValueError:
        raise ConfiguracaoInvalida(
            "LLM_TEMPERATURE, LLM_MAX_TOKENS e LLM_TIMEOUT_SEGUNDOS devem ser números."
        ) from None
    if max_tokens <= 0 or timeout <= 0:
        raise ConfiguracaoInvalida("LLM_MAX_TOKENS e LLM_TIMEOUT_SEGUNDOS devem ser maiores que zero.")

    return Config(api_key, base_url, _ler("LLM_MODEL"), temperature, max_tokens, timeout)