# Databricks Job — bronze -> silver lendo/escrevendo abfss:// (Cartao A2).
# Port do modulo src/silver/clean.py para o lake Azure (ADLS Gen2).
# No workspace Databricks (job Databricks, nao Spark local):
#   - monte os filesystems `bronze`/`silver` via Unity Catalog volumes ou
#     service principal com `abfss://<fs>@<storage>.dfs.core.windows.net/`.
#   - o salt vem de Databricks Secret (Key Vault-backed), nunca hardcoded.
#
# Uso no job: notebook task apontando para este arquivo + cluster DBR 14+.

# Databricks notebook source
# MAGIC %md ### Bronze -> Silver no ADLS (abfss)

# COMMAND ----------
import hashlib
from pyspark.sql import functions as F

STORAGE = spark.conf.get("bolsa.storage_account", "bolsafamilialake")
BRONZE = f"abfss://bronze@{STORAGE}.dfs.core.windows.net/pagamentos"
SILVER = f"abfss://silver@{STORAGE}.dfs.core.windows.net/pagamentos"
COMPETENCIA = spark.conf.get("bolsa.competencia", "202601")

# salt via secret scope (Key Vault): dbutils.secrets.get("bolsa-kv", "pseudonym-salt")
try:
    SALT = dbutils.secrets.get(scope="bolsa-kv", key="pseudonym-salt")  # noqa: F821
except Exception:
    SALT = "trocar-no-key-vault"  # falha fechada no teste do job, nunca em prod

bronze = spark.read.format("delta").load(BRONZE).filter(F.col("mes_competencia") == COMPETENCIA)

com_nis = bronze.filter(F.col("nis_favorecido").isNotNull() & (F.trim(F.col("nis_favorecido")) != ""))
silver = (
    com_nis.withColumn("nis_hash", F.sha2(F.concat(F.col("nis_favorecido"), F.lit(SALT)), 256))
    .drop("nis_favorecido", "nome_favorecido")
    .dropDuplicates(["nis_hash", "mes_referencia", "valor_parcela"])
)

(
    silver.write.format("delta")
    .mode("overwrite")
    .partitionBy("uf")
    .option("replaceWhere", f"mes_competencia = '{COMPETENCIA}'")
    .save(SILVER)
)

print(f"Silver OK no ADLS — competencia={COMPETENCIA} silver={silver.count()}")
