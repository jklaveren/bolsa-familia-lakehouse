# Lakehouse Databricks — Bolsa Família

[![CI](https://github.com/jklaveren/bolsa-familia-lakehouse/actions/workflows/ci.yml/badge.svg)](https://github.com/jklaveren/bolsa-familia-lakehouse/actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Pipeline de dados ponta a ponta sobre os microdados públicos do **Novo Bolsa Família**
(Portal da Transparência / CGU): ingestão em **PySpark**, **Delta Lake** em camadas
bronze → silver → gold, modelagem **dbt** no **Databricks**, orquestração **Airflow**,
**Terraform** para a infraestrutura e **CI no GitHub Actions** — com governança **LGPD**
desde a camada silver.

> **Em 30 segundos:** 242M+ linhas processadas · 18 testes dbt que rodam em toda PR ·
> orquestração em Databricks Workflows · NIS pseudonimizado com SHA-256 + salt ·
> PII nunca chega na gold.

---

## Resultado

| Métrica | Valor | Evidência |
|---|---|---|
| Linhas processadas | **242M+** (soma das competências rodadas) | [`docs/evidencias/fase6_quality_report_202601.txt`](docs/evidencias/fase6_quality_report_202601.txt) |
| Volume por competência | **19.480.034** linhas na bronze (jan/2026) | [`docs/evidencias/fase6_quality_report_202601.txt`](docs/evidencias/fase6_quality_report_202601.txt) |
| Testes dbt | **18/18 PASS** em toda PR, sem credencial (DuckDB) | [`docs/evidencias/ci_dbt_duckdb.txt`](docs/evidencias/ci_dbt_duckdb.txt) |
| Testes contra o workspace | **13/13 PASS** no Databricks | [`docs/evidencias/fase5_dbt_test.txt`](docs/evidencias/fase5_dbt_test.txt) |
| Gate de CI funcionando | teste quebrado **derruba o build** (exit 1) | [`docs/evidencias/fase8_ci_falha_de_proposito.txt`](docs/evidencias/fase8_ci_falha_de_proposito.txt) |
| Camadas | bronze (raw) → silver (tipada, dedup, pseudonimizada) → gold (marts) | [`docs/evidencias/fase3_silver_schema_202601.txt`](docs/evidencias/fase3_silver_schema_202601.txt) |
| Qualidade | relatório de checagens por competência | [`docs/evidencias/fase6_quality_report_202601.txt`](docs/evidencias/fase6_quality_report_202601.txt) |
| Governança | SHA-256 + salt no NIS, PII removida, linhagem bronze → gold | `src/silver/`, `dbt/bolsa_familia/models` |
| Custo/performance | partitioning, z-order e broadcast join | `notebooks/`, [Decisões técnicas](#decisões-técnicas) |

O CI mais recente está verde (badge acima). Os **18 testes dbt executam em toda PR**:
a mesma árvore de modelos roda em **DuckDB** sobre uma amostra versionada em `seeds/`,
sem precisar de credencial de workspace. O que se prova ali não é volume — é que as
regras continuam valendo: unicidade de chave, integridade referencial, domínio de UF,
faixa de valor e a soma da gold batendo com a silver. Com os secrets `DATABRICKS_*`
configurados, um job adicional repete a suíte contra o workspace real.

Teste que falha **grava as linhas culpadas** numa tabela no schema `qualidade`
(`store_failures`), em vez de sumir no log — dá para abrir o caso em SQL depois, sem
reproduzir a execução.

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

**Em produção o mesmo encadeamento roda como job do Databricks Workflows**
([`infra/databricks/`](infra/databricks/)), declarado em Terraform: cluster efêmero para
as tarefas PySpark, SQL Warehouse para o dbt, agendamento mensal, retry e alerta nativos.
O job clona a branch a cada execução, então o que roda em produção é exatamente o que
está no repositório. O Docker Compose continua servindo o desenvolvimento local, onde
subir a stack inteira em um comando vale mais do que depender de nuvem.

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
| `infra/databricks` | Job mensal em Databricks Workflows (Terraform) |
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
- A amostra do CI é **sintética e pequena** (600 linhas, gerada por
  `scripts/gerar_amostra_ci.py`). Ela prova as regras, não a performance — os números de
  volume vêm das execuções reais em `docs/evidencias/`.
- A observabilidade é `store_failures` mais testes de volume, faixa e integridade. Um
  catálogo de execuções com histórico e alerta (Elementary, Monte Carlo) é o passo
  seguinte, e só se paga com mais de um pipeline em produção.
- O job do Databricks Workflows é validado por `terraform validate` no CI, mas o `apply`
  depende de um workspace pago — o agendamento em si nunca rodou.

## Autoria

**Jessica Van Klaveren** — Engenheira de Dados · Lakehouse, crédito e dados regulados.
Databricks · PySpark · Delta Lake · dbt · Airflow · SQL · Power BI · LGPD.

[klaverenjv@gmail.com](mailto:klaverenjv@gmail.com) · [linkedin.com/in/jessicanolin](https://linkedin.com/in/jessicanolin) · São Leopoldo/RS
