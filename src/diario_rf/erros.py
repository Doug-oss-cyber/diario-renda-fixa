"""Exceções do programa. A mensagem de cada uma é legível para o usuário"""

class ErroDiario(Exception):
    """Base de todos os erros previstos. Nunca inclua
    segredos na mensagem."""

    mensagem_padrao = "Ocorreu um erro inesperado."

    def __init__(self, mensagem: str |  None = None):
        self.mensagem = mensagem or self.mensagem_padrao
        super().__init__(self.mensagem)

class EntradaVazia(ErroDiario):
    mensagem_padrao = "A anotação está vazia. Escreva o relato da operação."


class ConfiguracaoInvalida(ErroDiario):
    mensagem_padrao = "Configuração inválida. Confira o arquivo .env (veja o .env.example)."


class CredencialAusente(ErroDiario):
    mensagem_padrao = "Credencial ausente: defina LLM_API_KEY no arquivo .env (veja o .env.example)."


class CredencialInvalida(ErroDiario):
    mensagem_padrao = (
        "A API recusou a credencial (chave inválida ou sem permissão). "
        "Confira o valor de LLM_API_KEY."
    )


class ServicoIndisponivel(ErroDiario):
    mensagem_padrao = (
        "O serviço do modelo está indisponível ou sobrecarregado. "
        "Tente novamente em alguns minutos."
    )


class FalhaComunicacao(ErroDiario):
    mensagem_padrao = "Não foi possível conectar ao serviço. Verifique sua conexão com a internet."


class TempoEsgotado(ErroDiario):
    mensagem_padrao = (
        "O modelo demorou demais para responder. "
        "Tente novamente ou aumente LLM_TIMEOUT_SEGUNDOS no .env."
    )


class RespostaInvalida(ErroDiario):
    mensagem_padrao = "O modelo devolveu uma resposta vazia ou em formato inesperado."