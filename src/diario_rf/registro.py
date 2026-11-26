"""Registro simples de execução, sem dados sensíveis.

Saída no console (stderr), que aparece nos Logs da plataforma e, se LOG_ARQUIVO
estiver definida, também em arquivo.

Entram apenas metadados: tamanho da entrada, modelo, duração, tipo de erro e
quantidade de operações. Nunca entram: chave, relato do usuário, resposta do
modelo nem mensagens de erro de terceiros.
"""
import logging
import os
import sys
from pathlib import Path

from . import config

NOME = "diario_rf"
FORMATO = "%(asctime)s %(levelname)s %(message)s"


def encerrar_registro() -> None:
    logger = logging.getLogger(NOME)
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)


def configurar_registro(arquivo: str | None = None) -> logging.Logger:
    if arquivo is None:
        # Via config (e não direto do dotenv) para que os testes, que isolam
        # o .env nesse ponto, valham também aqui.
        config.load_dotenv()
        arquivo = os.getenv("LOG_ARQUIVO") or None

    encerrar_registro()
    logger = logging.getLogger(NOME)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    formato = logging.Formatter(FORMATO)

    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(formato)
    logger.addHandler(console)

    if arquivo:
        try:
            caminho = Path(arquivo)
            caminho.parent.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(caminho, encoding="utf-8")
        except OSError:
            # falha ao registrar nunca derruba o programa
            logger.warning("arquivo_de_registro_indisponivel seguindo_so_com_console")
        else:
            handler.setFormatter(formato)
            logger.addHandler(handler)
    return logger