# Evidências de execução

Cada cenário indica o comando, a saída do terminal, a data e se foi **real**
(chamada de verdade ao LLM) ou **simulado** (teste automático com resposta falsa).
Nenhuma saída abaixo contém chave ou credencial.

## Contexto: duas fases do projeto

| Fase | Provedor | Commit/tag | Observação |
|---|---|---|---|
| 1 | Gemini (`gemini-3.1-flash-lite`), API REST do Google AI Studio | `dafe5cafa4da5ce7d6b6696d463f4403c4d6ffe3` | Usado enquanto o LLM institucional não estava liberado |
| 2 | Ollama interno (`qwen3.5:9b-q4_K_M`) na plataforma Devel Lab | `a02c47124d1a1cc067765c5af24ab25cdf3dc2d7` | Mudança registrada em 10/11/2026 |

O Ollama interno não exige autenticação. Por isso, a partir da fase 2, credencial
ausente e credencial inválida são demonstradas por **testes simulados**, como
previsto no enunciado. As evidências reais desses dois cenários foram feitas na
fase 1 e continuam válidas para o código daquele commit
(`git checkout [hash]` as reproduz).

## 1. Fase 1: evidências reais com o Gemini

### 1.1 Fluxo normal (real)

| Campo       | Valor |
|-------------|-------|
| **Data**    | 04/11/2026 |
| **Comando** | `PYTHONPATH=src python -m diario_rf.cli "Apliquei 10.000 reais num CDB do Banco Inter, 105% do CDI, vence em janeiro de 2029, liquidez no vencimento."` |

**Saída:**
```json
{
  "operacao_valida": true,
  "motivo_invalida": null,
  "operacoes": [
    {
      "tipo_operacao": "aplicacao",
      "data_operacao": null,
      "produto": "CDB",
      "emissor": "Banco Inter",
      "valor": 10000.0,
      "indexador": "CDI",
      "taxa_tipo": "percentual_do_indexador",
      "taxa_valor": "105%",
      "data_vencimento": "2029-01",
      "liquidez": "no vencimento",
      "motivo_declarado": null,
      "campos_ausentes": ["data_operacao"],
      "ambiguidades": []
    }
  ],
  "observacoes": null
}
```

### 1.2 Credencial inválida (real)

| Campo              | Valor |
|--------------------|-------|
| **Data**           | 04/11/2026 |
| **Como foi feito** | `LLM_API_KEY` com valor falso no `.env` |

**Saída:**
```text
Erro: A API recusou a credencial (chave inválida ou sem permissão). Confira o valor de LLM_API_KEY.
```

### 1.3 Credencial ausente (real)
| Campo              | Valor |
|--------------------|-------|
| **Data**           | 04/11/2026 |
| **Como foi feito** | `LLM_API_KEY` removida do `.env` |

**Saída:**
```text
Erro: Credencial ausente: defina LLM_API_KEY no arquivo .env (veja o .env.example).
```

### 1.4 Indisponibilidade e timeout (reais, observados)

**Erro 503 – Service Unavailable**

| Campo              | Valor |
|--------------------|-------|
| **Data**           | 04/11/2026 |
| **Horário**        | 15:31 |
| **Mensagem**       | Falha na chamada à API: `HTTPSConnectionPool(host='generativelanguage.googleapis.com', port=443): Read timed out. (read timeout=30)` |
| **Erro adicional** | `503 Server Error: Service Unavailable` |
| **URL**            | `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent` |

## 2. Migração para o Ollama (fase 2)

O que mudou no código:

| Arquivo | Mudança |
|---|---|
| `llm_client.py` | Endpoint `/api/chat`, resposta em `message.content`, cabeçalho `Authorization` só quando há chave, tratamento de resposta cortada (`done_reason: length`) |
| `config.py` | `LLM_API_KEY` opcional; timeout padrão 120 s; `LLM_ESPERA_PRONTIDAO_SEGUNDOS` (a LLM leva 1 a 2 min para ficar disponível) |
| `erros.py` / cliente | 401/403 vira `CredencialInvalida` (com chave) ou `CredencialAusente` (sem chave) |
| `parser.py` | Remove blocos `<think>...</think>` antes de interpretar |
| `cli.py` | Entrada também por `DIARIO_ANOTACAO` (o container não tem terminal) |

Motivo: O LLM institucional foi liberado e a entrega final rodará na plataforma.

## 3. Fase 2: testes simulados (automáticos, sem rede)

Comando: `pytest`
Resultado: `51 passed, 81 subtests passed in 0.17s`

| Cenário | Tipo | Onde |
|---|---|---|
| Configuração ausente ou inválida | simulado | `tests/unit/test_config.py` |
| Credencial ausente (401 sem chave) | simulado | `tests/unit/test_llm_client.py` |
| Credencial inválida (401 com chave) | simulado | `tests/unit/test_llm_client.py` |
| Serviço indisponível (503) e limite (429) | simulado | `tests/unit/test_llm_client.py` |
| Falha de comunicação e timeout | simulado | `tests/unit/test_llm_client.py` |
| LLM ainda iniciando (espera esgotada) | simulado | `tests/unit/test_llm_client.py` |
| Resposta vazia, cortada ou fora do formato | simulado | `test_llm_client.py`, `test_parser.py` |
| Chave não aparece nas mensagens de erro | simulado | `test_llm_client` |

## 4. Fase 2: execuções reais na plataforma

- Imagem: `[seunomegmailcom]:latest`, enviada em [ainda por preencher]
- Variáveis configuradas no dashboard: `LLM_BASE_URL`, `LLM_MODEL`, `DIARIO_ANOTACAO`
  (sem valores sensíveis)
- Logs (container iniciado às [ainda por preencher]; a LLM respondeu após [ainda por preencher] s):
  ```text
  [PREENCHER: trecho dos Logs]
  ```
- Fluxo normal com Ollama: [ainda por preencher: resultado]
- Observações sobre a qualidade (diferenças em relação ao Gemini): [ainda por preencher]

## 5. Evidências reais com o modelo em produção

### 5.1 LLM não respondendo (real)

| Campo              | Valor |
|--------------------|-------|
| **Data e hora**           | 10/11/2026 16:09 |
| **Resposta** | Erro: A LLM ainda não respondeu. Se o container acabou de iniciar, aguarde 1 a 2 minutos e tente novamente. |

## 6. Conferência de segredos

- [ ] Nenhuma saída acima contém chave, token ou credencial
- [ ] `.env` não está versionado (`git ls-files | grep .env` mostra só `.env.example`)
- [ ] O histórico do Git não contém chaves reais
