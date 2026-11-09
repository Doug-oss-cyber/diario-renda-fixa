# Diário de operações de renda fixa

Transforma anotações livres de investimentos de renda fixa em registros
estruturados (JSON) para um diário de operações.

O programa **só organiza o que a pessoa relatou**: não recomenda, não sugere e
não avalia investimentos. Projeto P0 (TrendsIA), em Python, com chamada REST a um
LLM (Gemini).

## Pré-requisitos

- Python 3.10 ou superior (testado com Python **PREENCHER: sua versão, veja `python --version`**)
- Uma chave de API do Google AI Studio (aistudio.google.com), plano gratuito
- Conexão com a internet

## Instalação

```bash
git clone https://github.com/Doug-oss-cyber/diario-renda-fixa.git
cd diario-renda-fixa
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
pip install -r requirements.txt
```

No Windows (PowerShell), ative o ambiente com `.venv\Scripts\Activate.ps1`.

## Configuração do acesso ao LLM

```bash
cp .env.example .env
```

Edite o `.env`. Ele guarda a chave e **nunca vai para o Git** (está no `.gitignore`).

| Variável | Obrigatória | Padrão | O que é |
|---|---|---|---|
| `LLM_API_KEY` | sim | — | Chave de API gerada no Google AI Studio (segredo) |
| `LLM_BASE_URL` | sim | — | Endereço base da API: `https://generativelanguage.googleapis.com/v1beta` |
| `LLM_MODEL` | sim | — | Nome do modelo, por exemplo `gemini-3.1-flash-lite` (o usado nos testes). Confira os nomes disponíveis no AI Studio |
| `LLM_TEMPERATURE` | não | `0` | Baixa, para respostas consistentes na extração |
| `LLM_MAX_TOKENS` | não | `2048` | Limite de saída. Relatos com mais de uma operação geram JSON longo |
| `LLM_TIMEOUT_SEGUNDOS` | não | `30` | Tempo máximo de espera pela resposta |

O cliente (`llm_client.py`) usa o formato REST do Gemini (`generateContent`).
Usar outro provedor exige adaptar esse arquivo.

## Execução

```bash
PYTHONPATH=src python -m diario_rf.cli "Tirei 1500 do CDB de liquidez diária do Nubank, ficaram uns 6 mil lá."
```

Sem argumento, o programa pede a anotação no terminal. No PowerShell, defina antes
`$env:PYTHONPATH="src"`.

## Exemplos

**1. Relato com operação**

Entrada:

> Tirei 1500 do CDB de liquidez diária do Nubank, ficaram uns 6 mil lá.

Saída:

```json
{
  "operacao_valida": true,
  "motivo_invalida": null,
  "operacoes": [
    {
      "tipo_operacao": "resgate_parcial",
      "data_operacao": null,
      "produto": "CDB",
      "emissor": "Nubank",
      "valor": 1500.0,
      "indexador": null,
      "taxa_tipo": null,
      "taxa_valor": null,
      "data_vencimento": null,
      "liquidez": "diária",
      "motivo_declarado": null,
      "campos_ausentes": [
        "data_operacao",
        "indexador",
        "taxa_tipo",
        "taxa_valor",
        "data_vencimento"
      ],
      "ambiguidades": []
    }
  ],
  "observacoes": "Ficaram aproximadamente 6 mil reais de saldo no Nubank."
}
```

**2. Relato sem operação realizada** (intenção, sem recomendação do modelo)

Entrada:

> Estou pensando em aplicar 20 mil em algum Tesouro Prefixado, o que vocês mandam?

Saída:

```json
{
  "operacao_valida": false,
  "motivo_invalida": "Intenção e pedido de recomendação; nenhuma operação realizada.",
  "operacoes": [],
  "observacoes": null
}
```

**3. Erro tratado** (chave inválida)

```text
Erro: A API recusou a credencial (chave inválida ou sem permissão). Confira o valor de LLM_API_KEY.
```

## Erros tratados

Cada situação gera uma mensagem curta, sem traceback e sem expor a chave. O programa
encerra com código de saída 1.

| Situação | Mensagem ao usuário |
|---|---|
| Anotação vazia | A anotação está vazia. Escreva o relato da operação. |
| Credencial ausente | Credencial ausente: defina LLM_API_KEY no arquivo .env (veja o .env.example). |
| Configuração inválida | Variáveis ausentes ou valores inválidos no .env, com o nome da variável |
| Credencial inválida | A API recusou a credencial (chave inválida ou sem permissão). Confira o valor de LLM_API_KEY. |
| Serviço indisponível ou limite de uso | O serviço do modelo está indisponível ou sobrecarregado. Tente novamente em alguns minutos. |
| Falha de comunicação | Não foi possível conectar ao serviço. Verifique sua conexão com a internet. |
| Timeout | O modelo demorou demais para responder. Tente novamente ou aumente LLM_TIMEOUT_SEGUNDOS no .env. |
| Resposta vazia, bloqueada ou fora do formato | O modelo devolveu uma resposta vazia ou em formato inesperado (a mensagem indica o campo problemático). |

## Testes

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Também funcionam com `pytest` (`pip install pytest` e depois `pytest`).

**Testes simulados (automáticos).** Todos os testes da pasta `tests/` usam respostas
simuladas e não chamam o LLM: configuração, cliente HTTP (cada status de erro, timeout,
sem rede), parser, entrada vazia e CLI. Eles também verificam que a chave nunca aparece
nas mensagens de erro. O arquivo `tests/gabarito.jsonl` traz 10 relatos fictícios com o
resultado esperado e tem a sua estrutura verificada por teste.

**Testes reais (manuais).** Executados com a API de verdade, com as saídas registradas em
[`docs/evidences.md`](docs/evidences.md):

| Cenário | Tipo |
|---|---|
| Fluxo normal com relatos do gabarito | real |
| Credencial inválida (chave falsa) | real |
| Credencial ausente (sem `LLM_API_KEY`) | real |
| Serviço indisponível (503) e timeout, observados durante o desenvolvimento | real (observado) |
| Demais erros (429, 404, falha de rede, resposta vazia, JSON inválido) | simulado |

## Estrutura do projeto

```text
src/diario_rf/
  config.py      lê e valida as variáveis de ambiente
  prompts.py     prompt de sistema, exemplos e montagem da entrada
  llm_client.py  monta a requisição, chama o modelo e extrai o texto
  parser.py      valida o JSON e recalcula campos_ausentes
  erros.py       exceções com mensagens para o usuário
  cli.py         captura a entrada e apresenta o resultado
tests/           testes automáticos (simulados) e gabarito.jsonl
docs/decisions.md     decisões, resultados, limitações e uso de IA
```

## Limitações conhecidas

- O parser valida a **forma** do JSON, não o **conteúdo**. O modelo pode errar: por exemplo,
  numa anotação sem instituição citada ("no banco"), ele preencheu `emissor` com a palavra
  genérica "banco".
- O programa registra o que foi dito: não confere se valores e taxas existiram, nem avalia
  isenção de imposto ou risco.
- A resposta pode variar entre execuções, mesmo com temperatura baixa.
- Depende de um serviço externo gratuito, sujeito a indisponibilidade (503) e a limites de uso.
- O gabarito tem apenas 10 casos, em português do Brasil.

## Privacidade

Use apenas anotações **fictícias**. O plano gratuito do serviço pode usar o conteúdo
enviado para melhorar produtos do Google. Não coloque dados reais de investimentos
seus ou de outras pessoas.

## Decisões e uso de IA

As decisões de projeto, os resultados dos testes e a declaração do uso de ferramentas
de IA estão em [`docs/decisions.md`](docs/decisions.md).