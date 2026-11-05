# Decisões do projeto

## Problema e usuários

O diário nasceu de uma necessidade minha e de conhecidos que operam com renda fixa. Cada um anota as operações 
de um jeito: uns com gíria e abreviação, outros com informações faltando, e alguns misturam operação, opinião, 
sonho e dúvida no mesmo texto. Isso dificulta organizar um histórico. O programa transforma esses relatos em 
registros com campos fixos e organiza o que a pessoa relatou, não recomenda, sugere nem avalia investimentos.

> 1º Caso limpo: "Apliquei 10.000 reais num CDB do Banco Inter, 105% do CDI, vence em janeiro de 2029, liquidez no vencimento."; 

> 2º Gíria e abreviação: "botei 5k na LCA do BDMG, 84% do CDI, vencimento em setembro de 2028, mas com resgate todo santo dia"; 

> 3º Expressões regionais e pouca experiência ou conhecimento: "Tenho um dinheirin na poupança da Caixa, vi um dia desses, tinha aumentado uns 300 reais, um dia, quem sabe, ajeito minha casinha, nem que eu coloque 50 real lá todo mês."; 

> 4º Motivo misturado com opinião: "Reinvesti os 15 mil da LCI que venceu numa debênture da Vale, IPCA + 7,5%, achei a taxa boa demais, mas não sei se é arriscado."

## Entrada e saída

O usuário informa uma anotação em texto livre pelo terminal. O programa
imprime um registro em JSON.

**Entrada**

Apliquei 10.000 reais num CDB do Banco Inter, 105% do CDI, vence em janeiro de 2029, liquidez no vencimento.


**Saída**

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
## Por que um LLM
## Acesso ao LLM (provedor, modelo, API REST)
## Parâmetros configurados
## Organização do código
## Erros tratados
## Casos de teste
## Escolhas de escopo (o que decidi não fazer)
## Mudanças de ideia durante o projeto

- 02/11/2026

  ```
  Inicialmente o projeto seria voltado para operações de renda variável na Nasdaq, 
  principalmente nos setores de tecnologia e inteligência artificial, porém como é 
  algo não tão comum quanto operações de renda fixa em meu meio, a ideia para um 
  diário de operações de investimentos de renda fixa foi mantida, mas com um segmento 
  distinto e mais conhecido.
  ```

  ```
  No caso 7 do gabarito, havia um trecho entre parênteses ("pós-fixado com spread, 
  diferente de % do CDI") que foi removido para não entregar a resposta ao modelo.
  ```
  
- 03/11/2026
   ```
   O campo campos_ausentes é calculado em código, e não pelo modelo, por ser uma
   derivação determinística (diferença entre os campos esperados e os extraídos).
   Isso evita erros do modelo nessa checagem e reduz tokens de saída.
   ```
  
   ```
  A escolha pelo modelo Gemini é temporária haja vista que o LLM institucional ainda 
  não tinha sido liberada nesta data.
  ```
## Resultados e limitações

- 04/11/2026

  ```
  Caso 6, motivo_declarado: "reserva". Isso é a origem do dinheiro, e o prompt diz 
  que origem pode contar como motivo.
  ```
  
  ```
  Caso 6, taxa_valor. O modelo devolveu "8,67% a.a" e o gabarito tem "8,67% a.a.". 
  Isso não é erro do modelo, e sim a necessidade de normalizar o texto na comparação.
  ```
## Uso de ferramentas de IA

A ideia do projeto, um diário de operações de renda fixa, surgiu em 02/11/2026. Durante o desenvolvimento, usei o Claude (Anthropic) como apoio, nos seguintes pontos:

- **Escopo:** orientações para definir e delimitar o projeto.
- **Código:** esqueleto inicial dos arquivos `config.py`, `llm_client.py` e `cli.py`.
- **Revisão:** análise do schema de saída e do gabarito.
- **Git:** orientações sobre o fluxo de versionamento.

A definição do problema, as decisões de projeto, a escrita do código final, os ajustes e a validação dos resultados foram feitos por mim.

## Critérios de aceite