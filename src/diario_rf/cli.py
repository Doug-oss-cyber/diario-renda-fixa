"""Interface de terminal: captura a entrada e apresenta o resultado ou o erro."""
import argparse
import json
import logging
import os
import sys
import time

from .config import carregar_config
from .erros import EntradaVazia, ErroDiario
from .llm_client import extrair_registro
from .parser import interpretar_resposta
from .registro import configurar_registro

log = logging.getLogger("diario_rf")


def _ler_entrada(argumento: str | None) -> str:
    """Ordem: argumento da linha de comando, variável DIARIO_ANOTACAO, terminal."""
    if argumento is not None:
        return argumento
    do_ambiente = os.getenv("DIARIO_ANOTACAO")
    if do_ambiente is not None:
        return do_ambiente
    try:
        return input("Anotação: ")
    except EOFError:
        return ""


def main() -> int:
    configurar_registro()
    ap = argparse.ArgumentParser(description="Diário de operações de renda fixa")
    ap.add_argument("anotacao", nargs="?", help="texto da anotação (opcional)")
    args = ap.parse_args()
    inicio = time.monotonic()

    try:
        texto = _ler_entrada(args.anotacao)
        if not texto.strip():
            raise EntradaVazia()
        log.info("execucao_iniciada entrada_caracteres=%d", len(texto))
        cfg = carregar_config()
        log.info("config_carregada modelo=%s", cfg.model)
        resposta = extrair_registro(texto, cfg)
        registro = interpretar_resposta(resposta)
    except ErroDiario as e:
        log.warning("erro tipo=%s", type(e).__name__)
        print(f"Erro: {e.mensagem}", file=sys.stderr)
        return 1
    except Exception as e:
        log.error("erro_inesperado tipo=%s", type(e).__name__)
        print("Erro: ocorreu um problema inesperado. Veja o registro de execução.", file=sys.stderr,)
        return 2

    log.info(
        "sucesso operacoes=%d duracao_s=%.1f",
        len(registro["operacoes"]), time.monotonic() - inicio,
                                    )
    print(json.dumps(registro, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())