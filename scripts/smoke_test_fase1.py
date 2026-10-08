"""Fase 1 — Ambiente: prova mínima de que PySpark + Delta Lake funcionam localmente.

Critério de conclusão (Secao 15): "Script minimo le um DataFrame e grava em Delta com sucesso".
Nao depende do dataset real (isso e Fase 2) — usa um DataFrame sintetico pequeno.
"""
import shutil
from pathlib import Path

from src.common.spark_session import get_spark

DELTA_PATH = Path("data/_smoke_test_delta")


def main() -> None:
    spark = get_spark("fase1-smoke-test")

    df = spark.createDataFrame(
        [(1, "SP", 850.00), (2, "RJ", 600.00), (3, "BA", 750.50)],
        ["id", "uf", "valor_parcela"],
    )

    if DELTA_PATH.exists():
        shutil.rmtree(DELTA_PATH)

    df.write.format("delta").mode("overwrite").save(str(DELTA_PATH))
    lido = spark.read.format("delta").load(str(DELTA_PATH))

    count_escrito = df.count()
    count_lido = lido.count()
    assert count_lido == count_escrito, (
        f"Falha: escreveu {count_escrito} linhas, leu {count_lido}"
    )

    print(f"OK — {count_lido} linhas escritas e lidas com sucesso em formato Delta em {DELTA_PATH}")
    lido.show()

    spark.stop()
    shutil.rmtree(DELTA_PATH)


if __name__ == "__main__":
    main()
