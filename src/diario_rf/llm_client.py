"""Cliente REST do LLM (API de chat do Ollama, /api/chat).

Responsabilidades separadas: montar a requisição, esperar o servidor ficar
pronto, chamar o modelo e extrair o texto da resposta. Todo erro vira uma
exceção de erros.py, sem expor a chave.
"""
import time
import logging

import requests

from .config import Config
from .erros import (
    ConfiguracaoInvalida,
    CredencialAusente,
    CredencialInvalida,
    FalhaComunicacao,
    RespostaInvalida,
    ServicoIndisponivel,
    TempoEsgotado,
)
from .prompts import PROMPT_SISTEMA, montar_entrada

STATUS_INDISPONIVEL = {500, 502, 503, 504}

log = logging.getLogger("diario_rf")


def montar_requisicao(texto: str, cfg: Config) -> tuple[str, dict, dict]:
    """Prepara URL, cabeçalhos e corpo."""
    url = f"{cfg.base_url.rstrip('/')}/api/chat"
    cabecalhos = {"Content-Type": "application/json"}
    if cfg.api_key:
        cabecalhos["Authorization"] = f"Bearer {cfg.api_key}"
    corpo = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": montar_entrada(texto)},
        ],
        "stream": False,
        "format": "json",
        "think": False,
        "options": {"temperature": cfg.temperature, "num_predict": cfg.max_tokens},
    }
    return url, cabecalhos, corpo


def _levantar_por_status(resp: requests.Response, com_chave: bool) -> None:
    status = resp.status_code
    if status in (401, 403):
        raise CredencialInvalida() if com_chave else CredencialAusente()
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
    except requests.exceptions.SSLError as e:
        raise FalhaComunicacao(
            "Não foi possível validar o certificado HTTPS do servidor da LLM."
        ) from e
    except requests.ConnectionError as e:
        raise FalhaComunicacao() from e
    except requests.RequestException as e:
        raise FalhaComunicacao("Falha inesperada ao chamar o serviço.") from e

    if not resp.ok:
        _levantar_por_status(resp, com_chave="Authorization" in cabecalhos)
    try:
        return resp.json()
    except ValueError as e:
        raise RespostaInvalida() from e


def extrair_texto(dados: dict) -> str:
    """Pega o texto gerado dentro do envelope da API do Ollama."""
    if not isinstance(dados, dict):
        raise RespostaInvalida()
    try:
        texto = dados["message"]["content"]
    except (KeyError, TypeError):
        raise RespostaInvalida() from None
    if dados.get("done_reason") == "length":
        raise RespostaInvalida(
            "A resposta foi cortada pelo limite de tokens. Aumente LLM_MAX_TOKENS no .env."
        )
    if not isinstance(texto, str) or not texto.strip():
        raise RespostaInvalida()
    return texto


def aguardar_prontidao(cfg: Config, dormir=time.sleep, agora=time.monotonic) -> None:
    """Espera o servidor responder (a LLM leva 1 a 2 min após o container iniciar).

    Qualquer resposta HTTP, exceto 502/503/504, conta como servidor pronto.
    """
    limite = agora() + cfg.espera_prontidao
    url = f"{cfg.base_url.rstrip('/')}/api/tags"
    ultima_falha = "sem resposta"
    while True:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code not in STATUS_INDISPONIVEL:
                return
            ultima_falha = f"HTTP {r.status_code}"
        except requests.exceptions.SSLError as e:
            log.error("Detalhe do erro de certificado: %s", e)
            raise FalhaComunicacao(
                "Não foi possível validar o certificado HTTPS do servidor da LLM."
            ) from e
        except requests.RequestException as e:
            ultima_falha = type(e).__name__
        log.info("LLM ainda indisponível (%s)", ultima_falha)
        if agora() >= limite:
            raise ServicoIndisponivel(
                f"A LLM ainda não respondeu (último erro: {ultima_falha}). "
                "Se o container acabou de iniciar, aguarde 1 a 2 minutos e tente novamente."
            )
        dormir(10)


def extrair_registro(texto: str, cfg: Config) -> str:
    """Fluxo completo: espera, monta, chama e extrai o texto bruto do modelo."""
    log.info("Aguardando a LLM (até %d s)", cfg.espera_prontidao)
    aguardar_prontidao(cfg)
    log.info("LLM disponível; enviando solicitação ao modelo %s", cfg.model)
    url, cabecalhos, corpo = montar_requisicao(texto, cfg)
    dados = chamar_modelo(url, cabecalhos, corpo, cfg.timeout)
    log.info("Resposta recebida")
    return extrair_texto(dados)