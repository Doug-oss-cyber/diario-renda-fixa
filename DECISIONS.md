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

```text
Apliquei 10.000 reais num CDB do Banco Inter, 105% do CDI, vence em janeiro de 2029, liquidez no vencimento.
```

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
## Uso de ferramentas de IA

A partir do dia 02/11/2026, foi iniciada a ideia do projeto para criar um diário de operações de renda fixa e usei a
IA Claude da Anthropic para orientações sobre escopo e auxílio com código.
