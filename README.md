# Diário de operações de renda fixa

Transforma anotações livres de investimentos de renda fixa em registros
estruturados (JSON) para um diário de operações.

## Pré-requisitos
- Python 3.X (informe a versão que você usa)
- Uma chave de API do Google AI Studio (plano gratuito)

## Instalação
```bash
git clone <url-do-repositorio>
cd <pasta-do-repositorio>
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
pip install -r requirements.txt
```

## Configuração
```bash
cp .env.example .env
```
Edite o `.env` e preencha `LLM_API_KEY`, `LLM_BASE_URL` e `LLM_MODEL`
(explique onde obter a chave e quais valores usar).
Nunca faça commit do `.env`.

## Execução
```bash
PYTHONPATH=src python -m diario_rf.cli "Tirei 1500 do CDB de liquidez diária do Nubank, ficaram uns 6 mil lá."
```
Sem argumento, o programa pede a anotação no terminal.

## Exemplo
Entrada: 

>Tirei 1500 do CDB de liquidez diária do Nubank, ficaram uns 6 mil lá.

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

## Aviso
Use apenas anotações fictícias: o plano gratuito pode usar o conteúdo
enviado para melhorar produtos do Google. O programa só organiza o que
foi relatado e não recomenda investimentos.