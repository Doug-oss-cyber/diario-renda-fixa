"""Interface de terminal: captura a entrada e apresenta o resultado ou o erro."""
import argparse
import json
import os
import sys

from .config import carregar_config
from .erros import EntradaVazia, ErroDiario
from .llm_client import extrair_registro
from .parser import interpretar_resposta


def _ler_entrada(argumento):
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
    ap = argparse.ArgumentParser(description="Diário de operações de renda fixa")
    ap.add_argument("anotacao", nargs="?", help="texto da anotação (opcional)")
    args = ap.parse_args()

    try:
        texto = _ler_entrada(args.anotacao)
        if not texto.strip():
            raise EntradaVazia()
        cfg = carregar_config()
        resposta = extrair_registro(texto, cfg)
        registro = interpretar_resposta(resposta)
    except ErroDiario as e:
        print(f"Erro: {e.mensagem}", file=sys.stderr)
        return 1

    print(json.dumps(registro, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())