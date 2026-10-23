# Lakehouse Databricks — Bolsa Família

[![CI](https://github.com/jklaveren/bolsa-familia-lakehouse/actions/workflows/ci.yml/badge.svg)](https://github.com/jklaveren/bolsa-familia-lakehouse/actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Pipeline de dados ponta a ponta sobre os microdados públicos do **Novo Bolsa Família**
(Portal da Transparência / CGU): ingestão em **PySpark**, **Delta Lake** em camadas
bronze → silver → gold, modelagem **dbt** no **Databricks**, orquestração **Airflow**,
**Terraform** para a infraestrutura e **CI no GitHub Actions** — com governança **LGPD**
desde a camada silver.

> **Em 30 segundos:** 242M+ linhas processadas · 13 testes dbt com log de execução ·
> CI verde · NIS pseudonimizado com SHA-256 + salt · PII nunca chega na gold.

---

## Resultado

| Métrica | Valor | Evidência |
|---|---|---|
| Linhas processadas | **242M+** (soma das competências rodadas) | [`docs/evidencias/fase6_quality_report_202601.txt`](docs/evidencias/fase6_quality_report_202601.txt) |
| Volume por competência | **19.480.034** linhas na bronze (jan/2026) | [`docs/evidencias/fase6_quality_report_202601.txt`](docs/evidencias/fase6_quality_report_202601.txt) |
| Testes dbt | **13/13 PASS** (schema, unicidade, relacionamento, soma) | [`docs/evidencias/fase5_dbt_test.txt`](docs/evidencias/fase5_dbt_test.txt) |
| Gate de CI funcionando | teste quebrado **derruba o build** (exit 1) | [`docs/evidencias/fase8_ci_falha_de_proposito.txt`](docs/evidencias/fase8_ci_falha_de_proposito.txt) |
| Camadas | bronze (raw) → silver (tipada, dedup, pseudonimizada) → gold (marts) | [`docs/evidencias/fase3_silver_schema_202601.txt`](docs/evidencias/fase3_silver_schema_202601.txt) |
| Qualidade | relatório de checagens por competência | [`docs/evidencias/fase6_quality_report_202601.txt`](docs/evidencias/fase6_quality_report_202601.txt) |
| Governança | SHA-256 + salt no NIS, PII removida, linhagem bronze → gold | `src/silver/`, `dbt/bolsa_familia/models` |
| Custo/performance | partitioning, z-order e broadcast join | `notebooks/`, [Decisões técnicas](#decisões-técnicas) |

O CI mais recente está verde (badge acima). O job `dbt-test` roda de verdade quando os
secrets `DATABRICKS_*` estão configurados; sem eles, o CI valida `pytest`, `terraform
validate`, `dbt deps` e `dbt parse`.

## Arquitetura

```
Portal da Transparência (CSV mensal)
        │ HTTPS
        ▼
┌──────────┐   ┌──────────┐   ┌───────────────────┐
│  BRONZE  │──▶│  SILVER  │──▶│  GOLD (dbt)       │
│  PySpark │   │ tipagem  │   │ staging → marts   │
│  Delta   │   │ dedup    │   │ 13 testes         │
│  raw     │   │ pseudo.  │   │ Star Schema       │
└──────────┘   └──────────┘   └───────────────────┘
     ▲               ▲                    ▲
     └───────── Airflow (DAG mensal) ─────┘
```

A DAG `bolsa_familia_pipeline` encadeia `ingest_bronze → clean_silver → dbt_run →
dbt_test → notify`, com reprocesso de qualquer competência já publicada via
`{"competencia": "AAAAMM"}` no trigger manual.

## Como reproduzir

```bash
cp .env.example .env                      # preencha as credenciais locais
pip install -r requirements.txt
bash scripts/download_historico.sh        # fonte oficial (CGU), ~GBs
docker compose up -d                      # Airflow (8080) + Streamlit (8501)
python scripts/smoke_test_fase1.py
dbt build --project-dir dbt/bolsa_familia
terraform -chdir=infra init && terraform -chdir=infra validate
```

> O `docker compose` exige `POSTGRES_PASSWORD` e `AIRFLOW_ADMIN_PASSWORD` no `.env`.
> Para `terraform plan/apply`, defina `TF_VAR_airflow_admin_password`.
> O diretório `data/` é intencionalmente vazio: os dados vêm do script de download.

## Mapa do repositório

| Pasta | O quê |
|---|---|
| `src/bronze`, `src/silver` | ingestão e limpeza em PySpark |
| `src/quality` | checagens de qualidade |
| `src/forecast` | comparação VAR × rede neural (MLflow) |
| `dbt/bolsa_familia` | modelos staging → marts + 13 testes |
| `dags/` | DAG mensal do Airflow |
| `infra/`, `infra/azure` | Terraform local e Azure (ADLS Gen2 + Databricks) |
| `notebooks/` | pipeline pronto para o Databricks |
| `scripts/` | download oficial, smoke tests, bridge Snowflake |
| `sql/unity_catalog.sql` | governança Unity Catalog |
| `docs/` | design técnico, bridge Snowflake e evidências de execução |
| `app.py` | demo Streamlit sobre a camada gold |

## Decisões técnicas

- **Delta Lake, não Parquet puro:** ACID, time travel e merge permitem reprocessar a
  partir da bronze sem pedir a fonte de novo.
- **dbt com gate:** merge quebrado não entra — os 13 testes travam o CI quando o job
  dbt está habilitado.
- **LGPD desde a silver:** pseudonimização com salt e remoção de PII; a gold nunca
  recebe identificador pessoal.
- **Partição por competência:** toda consulta filtra por mês, o que reduz leitura em
  ordens de magnitude.
- **Lote primeiro:** streaming só onde existe SLA. A fonte é mensal por natureza.

## Limitações (e o que eu faria diferente)

Transparência faz parte do projeto — o que **não** está pronto:

- Processei **12 das 14 competências** disponíveis; as 35 do histórico completo ainda
  não rodaram.
- O Airflow roda em Docker Compose local. Em produção, o caminho é MWAA/Composer ou
  Databricks Workflows.
- Falta uma camada de observabilidade (Elementary / Great Expectations) além do teste
  duro no CI.
- Sem `DATABRICKS_*` configurado, o job `dbt-test` do CI é pulado — os logs de execução
  ficam em `docs/evidencias/`.

## Autoria

**Jessica Van Klaveren** — Engenheira de Dados · Lakehouse, crédito e dados regulados.
Databricks · PySpark · Delta Lake · dbt · Airflow · SQL · Power BI · LGPD.

[klaverenjv@gmail.com](mailto:klaverenjv@gmail.com) · [linkedin.com/in/jessicanolin](https://linkedin.com/in/jessicanolin) · São Leopoldo/RS
