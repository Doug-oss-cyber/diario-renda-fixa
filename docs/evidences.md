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

| Data e hora      | Resposta |
|------------------|----------|
| 10/11/2026 16:09 | Erro: A LLM ainda não respondeu. Se o container acabou de iniciar, aguarde 1 a 2 minutos e tente novamente. |
| 11/11/2026 16:24 | Execução encerrada: FalhaComunicacao (LLM não respondeu — timeout 0 s) |

### 5.2 Execução bem-sucedida (real)

| Campo | Valor |
|-------|-------|
| **Data e hora** | 13/11/2026 16:14 |
| **Entrada** | `Tirei 1500 do CDB de liquidez diaria do Nubank` (46 caracteres) |
| **Modelo** | qwen3.5:9b-q4_K_M |
| **Prontidão** | Servidor já disponível; espera concluída em ~0,02 s |
| **Tempo da chamada ao modelo** | ~4,5 s (16:14:43 → 16:14:48) |
| **Resposta** | JSON válido: `operacao_valida: true`; uma operação com `tipo_operacao: "resgate"`, `produto: "CDB"`, `emissor: "Nubank"`, `valor: 1500.0`, `liquidez: "diária"` |
| **Campos ausentes** | `data_operacao`, `indexador`, `taxa_tipo`, `taxa_valor`, `data_vencimento` (declarados em `campos_ausentes`, sem inventar valores) |
| **Observação** | Todos os campos preenchidos constam no texto original. `ambiguidades` vazio, `observacoes` nulo. |

### 5.3 Espera de prontidão com o container subindo (real)

| Campo | Valor |
|-------|-------|
| **Data e hora** | 13/11/2026 16:07 |
| **Comportamento** | Respostas HTTP 502 e `ReadTimeout` durante ~1 min 30 s, depois o servidor respondeu e a solicitação seguiu ao modelo (16:07:20 → 16:08:51), dentro da janela de 180 s |

## 6. Falhas e limitações conhecidas

### 6.1 Certificado HTTPS do servidor da LLM

| Item | Descrição |
|------|-----------|
| **Sintoma** | Erro de validação de certificado ao chamar `llm-internal.softex` |
| **Causa** | O ingress apresenta o certificado de reserva do controlador (`Kubernetes Ingress Controller Fake Certificate`, `DNS:ingress.local`). O servidor não tem certificado válido para o host. |
| **Por que o `LLM_CA_BUNDLE` não resolve** | O nome no certificado (`ingress.local`) não bate com o host, então o erro seguinte seria de nome. Além disso, o certificado é gerado na subida do controlador e pode mudar a qualquer reinício. |
| **Contorno atual** | `LLM_VERIFICAR_SSL=false`, com `log.warning` a cada execução |
| **Risco** | Sem verificação, o tráfego fica exposto a interceptação (MITM), incluindo o cabeçalho `Authorization: Bearer` da chave |
| **Resolução definitiva** | Depende da plataforma: configurar certificado real para o host no ingress. Depois disso, remover o contorno (ou usar `LLM_CA_BUNDLE` com a CA correta). |

### 6.2 Indisponibilidade e partida a frio

| Item | Descrição |
|------|-----------|
| **Sintoma** | 502 e `ReadTimeout` por 1 a 2 minutos após o container iniciar (ver 5.1 e 5.3) |
| **Mitigação** | `aguardar_prontidao`, com janela configurável (`LLM_ESPERA_PRONTIDAO_SEGUNDOS`, padrão 180 s) |
| **Limitação** | O endpoint `/api/tags` responder indica que o servidor está de pé, não que o modelo está carregado em memória. A primeira chamada após a subida pode demorar mais e estourar o `timeout` padrão de 120 s (`TempoEsgotado`). Isso ainda não foi observado nos testes reais. |
| **Ajuste possível** | Aumentar `LLM_TIMEOUT_SEGUNDOS` ou fazer um aquecimento do modelo após a prontidão |

### 6.3 Qualidade da extração

| Item | Descrição |
|------|-----------|
| **Cobertura testada** | Só um caso simples: uma operação, frase curta, tudo explícito (5.2) |
| **Não testado** | Várias operações no mesmo relato, valores ambíguos (ex.: "uns 2 mil"), anotações que não são operação (`operacao_valida: false`) |
| **Schema** | `format: "json"` garante JSON sintaticamente válido, não o schema. Ainda não há validação de tipos, enums e chaves obrigatórias após `extrair_registro`. |
| **Data da operação** | Quando o relato não traz data, `data_operacao` fica nula. Não há regra para assumir a data do envio. |
| **Modelo** | Modelo de 9B quantizado (q4): pode errar tipo de campo ou omitir chaves em entradas mais complexas |

### 6.4 Falhas tratadas pelo cliente

As falhas de comunicação viram exceções próprias (`CredencialInvalida`, `CredencialAusente`, `ConfiguracaoInvalida`, `ServicoIndisponivel`, `TempoEsgotado`, `FalhaComunicacao`, `RespostaInvalida`), sem expor a chave nas mensagens. Resposta cortada por limite de tokens (`done_reason == "length"`) vira `RespostaInvalida`.

## 6. Conferência de segredos

- [ ] Nenhuma saída acima contém chave, token ou credencial
- [ ] `.env` não está versionado (`git ls-files | grep .env` mostra só `.env.example`)
- [ ] O histórico do Git não contém chaves reais
