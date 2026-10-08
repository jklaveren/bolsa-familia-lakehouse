# Lakehouse Databricks — Bolsa Família (242M+ linhas)

Pipeline de engenharia de dados ponta a ponta sobre microdados públicos do
Novo Bolsa Família (Portal da Transparência/CGU): ingestão em **PySpark**,
**Delta Lake** bronze → silver → gold, modelagem **dbt** no **Databricks**,
orquestração **Airflow**, IaC **Terraform** (local + Azure) e CI no
GitHub Actions — com governança **LGPD** de verdade.

## Resultado

| Métrica | Valor |
|---|---|
| Linhas processadas | 242M+ |
| Testes dbt (schema + integridade) | 13 passando, com gate no CI |
| Camadas | bronze (raw) → silver (tipada, dedup, pseudonimizada) → gold (marts) |
| Orquestração | DAG mensal Airflow |
| Custo/performance | partitioning + z-order + broadcast joins |
| Governança | hash SHA-256 com salt no NIS, remoção de PII, linhagem bronze→gold |
| Abertura | Delta Sharing / Snowflake bridge documentada |

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

## Mapa do repo

| Pasta | O quê |
|---|---|
| `src/bronze`, `src/silver` | ingestão e limpeza PySpark |
| `src/quality` | checagens de qualidade |
| `src/forecast` | comparação VAR × rede neural (MLflow) |
| `dbt/bolsa_familia` | modelos staging → marts + testes |
| `dags` | DAG mensal Airflow |
| `infra` | Terraform do ambiente local |
| `infra/azure` | Terraform Azure (ADLS Gen2 + Databricks) — ver `docs/azure.md` |
| `notebooks` | pipeline pronto p/ Databricks |
| `scripts` | download oficial + smoke tests + bridge Snowflake |
| `sql/unity_catalog.sql` | governança Unity Catalog |
| `docs` | design técnico (PDF), bridge Snowflake, evidências de run |
| `app.py` | demo Streamlit da gold |
| `data/` | vazio de propósito — baixe via `scripts/download_historico.sh` |

## Como reproduzir

```bash
pip install -r requirements.txt
bash scripts/download_historico.sh        # fonte oficial, ~GBs
docker compose up -d                      # Airflow + serviços
python scripts/smoke_test_fase1.py
dbt build --project-dir dbt/bolsa_familia
terraform -chdir=infra init && terraform -chdir=infra validate
```

## Decisões técnicas

- **Delta Lake, não Parquet puro:** ACID, time travel e merge — reprocesso a partir da bronze sem pedir a fonte de novo.
- **dbt com gate:** merge quebrado não entra — 13 testes travam o CI.
- **LGPD desde a silver:** pseudonimização com salt + remoção de PII; PII nunca chega na gold.
- **Lote primeiro:** streaming só onde há SLA — este pipeline é mensal por natureza da fonte.

## Autora

Jessica Van Klaveren — Engenheira de Dados (Databricks · PySpark · Delta Lake · dbt · Airflow). São Leopoldo, RS.
