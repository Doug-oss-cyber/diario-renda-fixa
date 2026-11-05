"""Interface de terminal: captura a entrada e apresenta o resultado ou o erro."""
import argparse
import json
import sys

from .config import carregar_config
from .erros import EntradaVazia, ErroDiario
from .llm_client import extrair_registro


def _ler_entrada(argumento: str | None) -> str:
    if argumento is not None:
        return argumento
    try:
        return input("Anotação: ")
    except EOFError:
        return ""


def _apresentar(resposta: str) -> None:
    # A validação estrutural do JSON entra com o parser.py.
    try:
        print(json.dumps(json.loads(resposta), ensure_ascii=False, indent=2))
    except json.JSONDecodeError:
        print(resposta)


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
    except ErroDiario as e:
        print(f"Erro: {e.mensagem}", file=sys.stderr)
        return 1

    _apresentar(resposta)
    return 0


if __name__ == "__main__":
    sys.exit(main())