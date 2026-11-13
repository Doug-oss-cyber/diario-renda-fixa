# Diário de operações de renda fixa

Transforma anotações livres de investimentos de renda fixa em registros
estruturados (JSON) para um diário de operações.

O programa **só organiza o que a pessoa relatou**: não recomenda, não sugere e
não avalia investimentos. Projeto P0 (TrendsIA), em Python, com chamada REST a um
LLM servido pelo **Ollama** (API de chat, `/api/chat`).

## Pré-requisitos

- Python 3.10 ou superior (testado com Python 3.12.3)
- Acesso de rede a um servidor Ollama com o modelo escolhido já baixado
  (nos testes: `qwen3.5:9b-q4_K_M`)
- Se o servidor exigir autenticação, uma chave de API (enviada como `Bearer`)

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

Edite o `.env`. Ele pode guardar a chave e **nunca vai para o Git** (está no `.gitignore`).

| Variável | Obrigatória | Padrão | O que é |
|---|---|---|---|
| `LLM_BASE_URL` | sim | — | Endereço base do servidor Ollama, começando com `http://` ou `https://` |
| `LLM_MODEL` | sim | — | Nome do modelo no Ollama, por exemplo `qwen3.5:9b-q4_K_M` (o usado nos testes) |
| `LLM_API_KEY` | não | — | Chave enviada como `Authorization: Bearer`, só se o servidor exigir (segredo) |
| `LLM_TEMPERATURE` | não | `0` | Baixa, para respostas consistentes na extração |
| `LLM_MAX_TOKENS` | não | `2048` | Limite de saída (`num_predict`). Relatos com mais de uma operação geram JSON longo |
| `LLM_TIMEOUT_SEGUNDOS` | não | `120` | Tempo máximo de espera pela resposta do modelo |
| `LLM_ESPERA_PRONTIDAO_SEGUNDOS` | não | `180` | Quanto esperar o servidor responder antes de chamar o modelo. O container pode levar 1 a 2 minutos para subir; `0` faz uma única tentativa |
| `LLM_VERIFICAR_SSL` | não | `true` | `false` desativa a verificação do certificado HTTPS (veja abaixo) |
| `LLM_CA_BUNDLE` | não | — | Caminho de um arquivo de CA própria para validar o servidor; tem prioridade sobre `LLM_VERIFICAR_SSL` |

O cliente (`llm_client.py`) usa o formato do Ollama (`/api/chat`, com `format: "json"`
e `think: false`). Usar outro provedor exige adaptar esse arquivo.

### Certificado HTTPS

Por padrão o certificado do servidor é verificado. Se o servidor ainda não tem um
certificado válido para o seu endereço (por exemplo, um ingress de Kubernetes que
apresenta o certificado de reserva do controlador), a chamada falha com
"Não foi possível validar o certificado HTTPS do servidor da LLM."

- **Solução correta:** configurar um certificado válido no servidor e, se for de uma CA
  própria, apontar `LLM_CA_BUNDLE` para ela.
- **Contorno temporário:** `LLM_VERIFICAR_SSL=false`. O programa registra um aviso a cada
  execução. Sem verificação, o tráfego fica exposto a interceptação, inclusive a chave de
  API, então **não use em produção nem com dados reais**.

## Execução

```bash
PYTHONPATH=src python -m diario_rf.cli "Tirei 1500 do CDB de liquidez diária do Nubank, ficaram uns 6 mil lá."
```

Sem argumento, o programa pede a anotação no terminal. No PowerShell, defina antes
`$env:PYTHONPATH="src"`.

Antes de chamar o modelo, o programa espera o servidor responder (até
`LLM_ESPERA_PRONTIDAO_SEGUNDOS`). Se o container acabou de subir, a primeira execução
pode levar alguns minutos.

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

**3. Erro tratado** (servidor ainda não respondeu)

```text
Erro: A LLM ainda não respondeu (último erro: HTTP 502). Se o container acabou de iniciar, aguarde 1 a 2 minutos e tente novamente.
```

## Erros tratados

Cada situação gera uma mensagem curta, sem traceback e sem expor a chave. O programa
encerra com código de saída 1.

| Situação | Mensagem ao usuário |
|---|---|
| Anotação vazia | A anotação está vazia. Escreva o relato da operação. |
| Credencial ausente (servidor exige chave) | Credencial ausente: defina LLM_API_KEY no arquivo .env (veja o .env.example). |
| Configuração inválida | Variáveis ausentes ou valores inválidos no .env, com o nome da variável |
| Modelo ou endereço não encontrado (404) | Modelo ou endereço não encontrado. Confira LLM_MODEL e LLM_BASE_URL no .env. |
| Credencial inválida | A API recusou a credencial (chave inválida ou sem permissão). Confira o valor de LLM_API_KEY. |
| Servidor não respondeu na espera de prontidão | A LLM ainda não respondeu (último erro: ...). Se o container acabou de iniciar, aguarde 1 a 2 minutos e tente novamente. |
| Serviço indisponível (500, 502, 503, 504) | O serviço do modelo está indisponível ou sobrecarregado. Tente novamente em alguns minutos. |
| Limite de uso atingido (429) | Limite de uso do serviço atingido. Aguarde um pouco e tente novamente. |
| Certificado HTTPS inválido | Não foi possível validar o certificado HTTPS do servidor da LLM. |
| Falha de comunicação | Não foi possível conectar ao serviço. Verifique sua conexão e o endereço do servidor. |
| Timeout | O modelo demorou demais para responder. Tente novamente ou aumente LLM_TIMEOUT_SEGUNDOS no .env. |
| Resposta vazia, cortada ou fora do formato | O modelo devolveu uma resposta vazia ou em formato inesperado. Se foi cortada pelo limite de tokens, a mensagem sugere aumentar LLM_MAX_TOKENS. |

## Testes

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Também funcionam com `pytest` (`pip install pytest` e depois `pytest`).

**Testes simulados (automáticos).** Todos os testes da pasta `tests/` usam respostas
simuladas e não chamam o LLM: configuração (incluindo as opções de SSL), cliente HTTP
(cada status de erro, timeout, sem rede, espera de prontidão), parser, entrada vazia e
CLI. Eles também verificam que a chave nunca aparece nas mensagens de erro. O arquivo
`tests/gabarito.jsonl` traz 10 relatos fictícios com o resultado esperado e tem a sua
estrutura verificada por teste.

**Testes reais (manuais).** Executados com o servidor Ollama de verdade, com as saídas
registradas em [`docs/evidences.md`](docs/evidences.md):

| Cenário | Tipo |
|---|---|
| Fluxo normal com um relato simples de uma operação | real |
| Servidor subindo (502 e `ReadTimeout`) e espera de prontidão | real |
| LLM sem responder (falha de comunicação) | real (observado) |
| Credencial inválida e credencial ausente | simulado |
| Demais erros (429, 404, falha de rede, resposta vazia, JSON inválido) | simulado |

## Estrutura do projeto

```text
src/diario_rf/
  config.py      lê e valida as variáveis de ambiente
  prompts.py     prompt de sistema, exemplos e montagem da entrada
  llm_client.py  monta a requisição, espera o servidor ficar pronto, chama o modelo e extrai o texto
  parser.py      valida o JSON e recalcula campos_ausentes
  erros.py       exceções com mensagens para o usuário
  cli.py         captura a entrada e apresenta o resultado
tests/           testes automáticos (simulados) e gabarito.jsonl
docs/decisions.md     decisões, resultados, limitações e uso de IA
docs/evidences.md     evidências dos testes reais
```

## Limitações conhecidas

- O parser valida a **forma** do JSON, não o **conteúdo**. O modelo pode errar: por exemplo,
  em testes anteriores (com outro modelo), numa anotação sem instituição citada
  ("no banco"), ele preencheu `emissor` com a palavra genérica "banco".
- O programa registra o que foi dito: não confere se valores e taxas existiram, nem avalia
  isenção de imposto ou risco.
- A resposta pode variar entre execuções, mesmo com temperatura baixa. O modelo é pequeno
  (9B, quantizado em q4), então relatos longos ou ambíguos têm mais risco de erro.
- Quando o relato não traz data, `data_operacao` fica nula: o programa não assume a data
  do envio.
- O servidor pode levar de 1 a 2 minutos para responder após iniciar. A primeira chamada ao
  modelo depois disso também pode demorar mais; se estourar o tempo, aumente
  `LLM_TIMEOUT_SEGUNDOS`.
- Com `LLM_VERIFICAR_SSL=false` a conexão não é autenticada (veja "Certificado HTTPS").
- O gabarito tem apenas 10 casos, em português do Brasil.

## Privacidade

Use apenas anotações **fictícias**. O texto é enviado ao servidor configurado em
`LLM_BASE_URL`, e este projeto não controla como ele armazena ou usa o conteúdo. Não coloque
dados reais de investimentos seus ou de outras pessoas.

## Decisões e uso de IA

As decisões de projeto, os resultados dos testes e a declaração do uso de ferramentas
de IA estão em [`docs/decisions.md`](docs/decisions.md).