"""Camada Silver — tipagem, deduplicacao, pseudonimizacao e quarentena
(Secao 7.2 do design doc).

Le a tabela Delta Bronze, aplica as transformacoes descritas na Secao 7.2 e
grava duas saidas Delta: a Silver valida (particionada por uf) e a quarentena
(linhas sem NIS, preservadas para investigacao — nunca descartadas em silencio).
"""
import argparse
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any

try:
    from pyspark.sql import DataFrame, SparkSession
    from pyspark.sql import functions as F
    _PYSPARK_OK = True
except Exception:
    DataFrame = Any  # type: ignore
    SparkSession = Any  # type: ignore
    F = None  # type: ignore
    _PYSPARK_OK = False
    if TYPE_CHECKING:
        from pyspark.sql import DataFrame, SparkSession

from src.silver.pseudonymize import get_salt, pseudonymize

try:
    from src.common.spark_session import get_spark
except Exception:  # import seguro sem pyspark/delta
    def get_spark(*a, **k):
        raise RuntimeError("Spark indisponivel neste ambiente")

BRONZE_DIR = "data/bronze/pagamentos"
SILVER_DIR = "data/silver/pagamentos"
QUARANTINE_DIR = "data/silver/quarentena_sem_nis"


def to_first_of_month(col_name: str):
    """'202601' (AAAAMM) -> date 2026-01-01."""
    return F.to_date(F.col(col_name), "yyyyMM")


def parse_valor(col_name: str):
    """'850,00' -> decimal(10,2) 850.00."""
    return F.regexp_replace(F.col(col_name), ",", ".").cast("decimal(10,2)")


def split_quarantine(df: DataFrame) -> tuple[DataFrame, DataFrame]:
    sem_nis = df.filter(
        F.col("nis_favorecido").isNull() | (F.trim(F.col("nis_favorecido")) == "")
    )
    com_nis = df.filter(
        F.col("nis_favorecido").isNotNull() & (F.trim(F.col("nis_favorecido")) != "")
    )
    return com_nis, sem_nis


def clean_silver(spark: SparkSession, competencia: str, salt: str) -> tuple[DataFrame, DataFrame]:
    bronze = spark.read.format("delta").load(BRONZE_DIR).filter(
        F.col("mes_competencia") == competencia
    )

    bronze_count = bronze.count()

    com_nis, sem_nis = split_quarantine(bronze)

    silver = (
        com_nis.withColumn("mes_competencia", to_first_of_month("mes_competencia"))
        .withColumn("mes_referencia", to_first_of_month("mes_referencia"))
        .withColumn("valor_parcela", parse_valor("valor_parcela"))
    )
    silver = pseudonymize(silver, salt)
    silver = silver.dropDuplicates(["nis_hash", "mes_referencia", "valor_parcela"])

    (
        silver.write.format("delta")
        .mode("overwrite")
        .partitionBy("uf")
        .option("replaceWhere", f"mes_competencia = date('{competencia[:4]}-{competencia[4:]}-01')")
        .save(SILVER_DIR)
    )
    (
        sem_nis.write.format("delta")
        .mode("overwrite")
        .option("replaceWhere", f"mes_competencia = '{competencia}'")
        .save(QUARANTINE_DIR)
    )

    silver_count = silver.count()
    quarantine_count = sem_nis.count()
    print(
        f"Silver OK — competencia={competencia} bronze={bronze_count} "
        f"silver={silver_count} quarentena={quarantine_count} "
        f"(dedup removeu {bronze_count - silver_count - quarantine_count} linhas)"
    )
    return silver, sem_nis


def competencia_padrao() -> str:
    """Mes anterior em AAAAMM.

    A CGU publica a competencia nos primeiros dias do mes seguinte, entao
    uma execucao agendada sem argumento quer sempre o mes que acabou. Deixa
    o job mensal rodar sem alguem preencher a data na mao, e o reprocesso de
    uma competencia antiga continua sendo `--competencia AAAAMM`.
    """
    hoje = date.today()
    ultimo_do_mes_passado = hoje.replace(day=1) - timedelta(days=1)
    return ultimo_do_mes_passado.strftime("%Y%m")


def main() -> None:
    parser = argparse.ArgumentParser(description="Limpeza Silver — Novo Bolsa Familia")
    parser.add_argument("--competencia", default="",
                        help="AAAAMM, ex: 202601. Vazio = mes anterior.")
    args = parser.parse_args()
    competencia = args.competencia.strip() or competencia_padrao()

    spark = get_spark("silver-clean")
    clean_silver(spark, competencia, get_salt())
    spark.stop()


if __name__ == "__main__":
    main()
