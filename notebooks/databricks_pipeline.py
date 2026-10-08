# Databricks notebook source
# MAGIC %md
# MAGIC # Pipeline Novo Bolsa Familia — Databricks Free Edition (Fase 4/5/9)
# MAGIC
# MAGIC Versao adaptada do pipeline local (`src/bronze/ingest.py` +
# MAGIC `src/silver/clean.py`) para rodar como notebook Databricks (compute
# MAGIC serverless). Le os CSVs a partir de um Volume do Unity Catalog e grava
# MAGIC as tabelas Bronze/Silver como tabelas gerenciadas no catalogo, para o
# MAGIC dbt-databricks (Fase 4/5) ler via `source()`.
# MAGIC
# MAGIC Processa uma LISTA de competencias (nao so uma) — cada iteracao usa
# MAGIC `replaceWhere` filtrando por `mes_competencia`, entao rodar de novo ou
# MAGIC adicionar uma competencia nova nunca apaga as outras ja gravadas
# MAGIC (mesmo padrao do `src/bronze/ingest.py` / `src/silver/clean.py` locais).
# MAGIC
# MAGIC Pre-requisito (rodar uma vez, em uma celula SQL ou no Catalog Explorer):
# MAGIC ```sql
# MAGIC CREATE SCHEMA IF NOT EXISTS workspace.bolsa_familia;
# MAGIC CREATE VOLUME IF NOT EXISTS workspace.bolsa_familia.raw;
# MAGIC ```
# MAGIC Depois, upload de cada **.zip** baixado do Portal da Transparencia para
# MAGIC o Volume `workspace.bolsa_familia.raw`. O notebook extrai os .csv dos
# MAGIC zips que ainda nao foram extraidos.

# COMMAND ----------

# Configuracao — edite antes de rodar (sem widgets: o estado de widget
# persiste entre reimportacoes do notebook e ja causou confusao aqui).
competencias = [
    "202303", "202306", "202309", "202312",
    "202403", "202406", "202409", "202412",
    "202503", "202506", "202509", "202512",
    "202601", "202603", "202606",
]
salt = "32c09beff12af3c68ed04981f569fd2369cf05ea16d7de1b38dd519fe9f73f14"  # mesmo salt do .env local
catalog = "workspace"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.bolsa_familia")

VOLUME_DIR = f"/Volumes/{catalog}/bolsa_familia/raw"
BRONZE_TABLE = f"{catalog}.bolsa_familia.bronze_pagamentos"
SILVER_TABLE = f"{catalog}.bolsa_familia.pagamentos"
QUARANTINE_TABLE = f"{catalog}.bolsa_familia.quarentena_sem_nis"

COLUMN_MAP = {
    "MÊS COMPETÊNCIA": "mes_competencia",
    "MÊS REFERÊNCIA": "mes_referencia",
    "UF": "uf",
    "CÓDIGO MUNICÍPIO SIAFI": "codigo_municipio_siafi",
    "NOME MUNICÍPIO": "nome_municipio",
    "CPF FAVORECIDO": "cpf_favorecido",
    "NIS FAVORECIDO": "nis_favorecido",
    "NOME FAVORECIDO": "nome_favorecido",
    "VALOR PARCELA": "valor_parcela",
}

# COMMAND ----------
# MAGIC %md ## Loop: Bronze + Silver por competencia (so processa o que ainda falta)

# COMMAND ----------

import os
import zipfile

from pyspark.sql import functions as F
from pyspark.sql.utils import AnalysisException

for competencia in competencias:
    zip_path = f"{VOLUME_DIR}/{competencia}_NovoBolsaFamilia.zip"
    raw_path = f"{VOLUME_DIR}/{competencia}_NovoBolsaFamilia.csv"

    if not os.path.exists(zip_path):
        print(f"[{competencia}] zip nao encontrado em {zip_path}, pulando (faca o upload antes)")
        continue

    try:
        ja_tem = (
            spark.table(BRONZE_TABLE)
            .filter(F.col("mes_competencia") == competencia)
            .limit(1)
            .count()
            > 0
        )
    except AnalysisException:
        ja_tem = False

    if ja_tem:
        print(f"[{competencia}] ja existe na Bronze, pulando")
        continue

    print(f"[{competencia}] iniciando...")

    if not os.path.exists(raw_path):
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(VOLUME_DIR)

    df_raw = (
        spark.read.option("header", True)
        .option("sep", ";")
        .option("encoding", "ISO-8859-1")
        .option("quote", '"')
        .option("multiLine", True)
        .csv(raw_path)
    )
    for original, target in COLUMN_MAP.items():
        if original in df_raw.columns:
            df_raw = df_raw.withColumnRenamed(original, target)

    (
        df_raw.write.format("delta")
        .mode("overwrite")
        .option("replaceWhere", f"mes_competencia = '{competencia}'")
        .option("mergeSchema", "true")
        .partitionBy("mes_competencia")
        .saveAsTable(BRONZE_TABLE)
    )
    print(f"[{competencia}] Bronze OK — {df_raw.count()} linhas")

    bronze_comp = spark.table(BRONZE_TABLE).filter(F.col("mes_competencia") == competencia)
    sem_nis = bronze_comp.filter(F.col("nis_favorecido").isNull() | (F.trim(F.col("nis_favorecido")) == ""))
    com_nis = bronze_comp.filter(F.col("nis_favorecido").isNotNull() & (F.trim(F.col("nis_favorecido")) != ""))

    silver = (
        com_nis.withColumn("mes_competencia", F.to_date("mes_competencia", "yyyyMM"))
        .withColumn("mes_referencia", F.to_date("mes_referencia", "yyyyMM"))
        .withColumn("valor_parcela", F.regexp_replace("valor_parcela", ",", ".").cast("decimal(10,2)"))
        .withColumn("nis_hash", F.sha2(F.concat(F.col("nis_favorecido"), F.lit(salt)), 256))
        .drop("nis_favorecido", "nome_favorecido")
        .dropDuplicates(["nis_hash", "mes_referencia", "valor_parcela"])
    )

    data_competencia = f"date('{competencia[:4]}-{competencia[4:]}-01')"
    (
        silver.write.format("delta")
        .mode("overwrite")
        .option("replaceWhere", f"mes_competencia = {data_competencia}")
        .option("mergeSchema", "true")
        .partitionBy("uf")
        .saveAsTable(SILVER_TABLE)
    )
    (
        sem_nis.write.format("delta")
        .mode("overwrite")
        .option("replaceWhere", f"mes_competencia = '{competencia}'")
        .option("mergeSchema", "true")
        .saveAsTable(QUARANTINE_TABLE)
    )

    print(f"[{competencia}] Silver OK — silver={silver.count()} quarentena={sem_nis.count()}")

    # Descarta o CSV extraido para nao lotar o Volume — mantem so o .zip
    os.remove(raw_path)

print("\nProcessamento concluido para todas as competencias disponiveis no Volume.")

# COMMAND ----------
# MAGIC %md ## Evidencia

# COMMAND ----------

display(
    spark.sql(
        f"SELECT mes_competencia, count(*) as linhas FROM {SILVER_TABLE} "
        "GROUP BY mes_competencia ORDER BY mes_competencia"
    )
)
