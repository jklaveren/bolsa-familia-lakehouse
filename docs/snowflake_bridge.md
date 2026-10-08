# Ponte Delta Sharing → Snowflake trial (Cartão 2c)

> Sem inventar acesso: nada aqui foi executado contra um Snowflake real.
> O script `scripts/snowflake_bridge.py` gera os artefatos offline a partir de
> `docs/viz_gold.json` (agregado sem PII). Com um trial ativo, execute o passo 3.

## 1. O que o script gera

```bash
python scripts/snowflake_bridge.py
# out/snowflake/stg_pagamentos_uf.sql   — DDL + COPY INTO
# out/snowflake/por_uf_202601.csv       — 27 UFs, pronto p/ PUT
# out/snowflake/uniform_alternativa.sql — plano B Iceberg UniForm
```

Fonte: `docs/viz_gold.json` (202601 = 19.479.712 silver, R$ 12,98B, 27 UFs).
Nenhum NIS/nome sai do Delta local — só agregados por UF.

## 2. Via Delta Sharing (preferido, se o workspace permitir)

1. No Databricks: crie um share do schema Gold (`CREATE SHARE ... ADD SCHEMA bolsa_familia`).
2. No Snowflake: `CREATE PROVIDER` + `CREATE DATABASE FROM SHARE` (Secure Data Sharing).
3. Valide: `SELECT COUNT(*) FROM SHARE_DB...MARTS_PAGAMENTOS_UF`.

## 3. Via CSV + stage (funciona em qualquer trial, 5 min)

```sql
-- 1. rode o DDL:
-- out/snowflake/stg_pagamentos_uf.sql
-- 2. no SnowSQL:
PUT file://out/snowflake/por_uf_202601.csv @~/staged AUTO_COMPRESS=TRUE;
COPY INTO BOLSA_FAMILIA.PAGAMENTOS_UF
  FROM @~/staged/por_uf_202601.csv
  FILE_FORMAT=(TYPE=CSV SKIP_HEADER=1 FIELD_OPTIONALLY_ENCLOSED_BY='"');
-- 3. confira:
SELECT competencia, COUNT(*), SUM(valor_total) FROM BOLSA_FAMILIA.PAGAMENTOS_UF GROUP BY 1;
-- esperado: 27 linhas, soma R$ 12.978.539.408,00
```

## 4. Plano B — sem trial: Iceberg UniForm

Se o trial estiver indisponível, não invente print de Snowflake: documente o
UniForm como alternativa (mesmo storage lido pelos dois motores).
SQL em `out/snowflake/uniform_alternativa.sql`. Critério: `docs/viz_gold.json`
continua sendo a prova auditável até o trial existir.

## 5. Custos

Trial Snowflake (30 dias, USD 400 em créditos): custo $0 se ficar no
warehousing XS com auto-suspend 60s. Não deixe warehouse ligado.
