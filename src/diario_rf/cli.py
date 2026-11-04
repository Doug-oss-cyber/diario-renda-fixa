"""Interface de terminal: lê uma anotação e imprime o registro estruturado."""
import argparse
import json
import sys

from .config import ConfigError, carregar_config
from .llm_client import LLMError, extrair_registro


def main() -> int:
    ap = argparse.ArgumentParser(description="Diário de operações de renda fixa")
    ap.add_argument("anotacao", nargs="?", help="texto da anotação (opcional)")
    args = ap.parse_args()

    texto = args.anotacao or input("Anotação: ")
    if not texto.strip():
        print("Erro: a anotação está vazia.", file=sys.stderr)
        return 1

    try:
        cfg = carregar_config()
        resposta = extrair_registro(texto, cfg)
    except (ConfigError, LLMError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1

    # No Básico só exibimos; a validação do JSON fica para o Intermediário.
    try:
        print(json.dumps(json.loads(resposta), ensure_ascii=False, indent=2))
    except json.JSONDecodeError:
        print(resposta)
    return 0


if __name__ == "__main__":
    sys.exit(main())