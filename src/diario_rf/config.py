"""Leitura e validação das configurações a partir de variáveis de ambiente (.env)."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

from .erros import ConfiguracaoInvalida

@dataclass(frozen=True)
class Config:
    api_key: str
    base_url: str
    model: str
    temperature: float
    max_tokens: int
    timeout: int
    espera_prontidao: int
    verificar_ssl: bool | str = True  # True, False ou caminho de um certificado (CA)

def _ler(nome: str) -> str:
    return (os.getenv(nome) or "").strip()

def carregar_config() -> Config:
    load_dotenv()

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
        timeout = int(_ler("LLM_TIMEOUT_SEGUNDOS") or "120")
        espera_prontidao = int(_ler("LLM_ESPERA_PRONTIDAO_SEGUNDOS") or "180")
    except ValueError:
        raise ConfiguracaoInvalida(
            "LLM_TEMPERATURE, LLM_MAX_TOKENS e LLM_TIMEOUT_SEGUNDOS devem ser números."
        ) from None
    if max_tokens <= 0 or timeout <= 0:
        raise ConfiguracaoInvalida("LLM_MAX_TOKENS e LLM_TIMEOUT_SEGUNDOS devem ser maiores que zero.")

    if espera_prontidao < 0:
        raise ConfiguracaoInvalida("LLM_ESPERA_PRONTIDAO_SEGUNDOS não pode ser negativo.")

    ca = _ler("LLM_CA_BUNDLE")
    modo = _ler("LLM_VERIFICAR_SSL").lower()
    if ca:
        if not os.path.isfile(ca):
            raise ConfiguracaoInvalida("LLM_CA_BUNDLE aponta para um arquivo que não existe.")
        verificar_ssl = ca
    elif modo in ("false", "0", "nao", "não"):
        verificar_ssl = False
    elif modo in ("", "true", "1", "sim"):
        verificar_ssl = True
    else:
        raise ConfiguracaoInvalida("LLM_VERIFICAR_SSL deve ser true ou false.")

    return Config(
        api_key=_ler("LLM_API_KEY"),
        base_url=base_url,
        model=_ler("LLM_MODEL"),
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        espera_prontidao=espera_prontidao,
        verificar_ssl=verificar_ssl
    )

