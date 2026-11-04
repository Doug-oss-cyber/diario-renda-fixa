"""Leitura das configurações a partir de variáveis de ambiente (.env)."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

class ConfigError(Exception):
    """Configuração ausente ou inválida."""

@dataclass(frozen=True)
class Config:
    api_key: str
    base_url: str
    model: str
    temperature: float
    max_tokens: int
    timeout: int


def carregar_config() -> Config:
    load_dotenv()

    obrigatorias = ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL")
    faltando = [nome for nome in obrigatorias if not os.getenv(nome)]
    if faltando:
        raise ConfigError(
            "Variáveis ausentes no .env: " + ", ".join(faltando)
            + ". Veja o .env.example."
        )

    try:
        return Config(
            api_key=os.environ["LLM_API_KEY"],
            base_url=os.environ["LLM_BASE_URL"],
            model=os.environ["LLM_MODEL"],
            temperature=float(os.getenv("LLM_TEMPERATURE", "0")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1500")),
            timeout=int(os.getenv("LLM_TIMEOUT_SEGUNDOS", "30")),
        )
    except ValueError as e:
        raise ConfigError(f"Valor numérico inválido no .env: {e}") from e