"""Roda os checks de qualidade (Secao 12.1) sobre uma competencia ja ingerida
e imprime o relatorio de execucao — evidencia da Fase 6."""
import argparse
import sys

from pyspark.sql import functions as F

from src.common.spark_session import get_spark
from src.quality.checks import print_report, run_all_checks

BRONZE_DIR = "data/bronze/pagamentos"
SILVER_DIR = "data/silver/pagamentos"
QUARANTINE_DIR = "data/silver/quarentena_sem_nis"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--competencia", required=True)
    args = parser.parse_args()

    spark = get_spark("quality-checks")
    bronze = spark.read.format("delta").load(BRONZE_DIR).filter(
        F.col("mes_competencia") == args.competencia
    )
    silver = spark.read.format("delta").load(SILVER_DIR)
    quarentena = spark.read.format("delta").load(QUARANTINE_DIR)

    results = run_all_checks(bronze, silver, quarentena)
    ok = print_report(results)
    spark.stop()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
