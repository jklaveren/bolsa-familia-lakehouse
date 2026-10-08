"""Monta a serie temporal nacional (Secao 10.1/10.2) a partir da Silver local.

Filtra mes_referencia == mes_competencia para pegar so os pagamentos "em dia"
de cada competencia amostrada — sem isso, pagamentos retroativos de uma
competencia se sobrepoem aos meses cobertos por outras competencias da
amostra trimestral, inflando a serie com contagem duplicada do mesmo mes de
referencia visto por arquivos diferentes.
"""
import pandas as pd

try:
    from pyspark.sql import functions as F
    _PYSPARK_OK = True
except Exception:
    F = None  # type: ignore
    _PYSPARK_OK = False

try:
    from src.common.spark_session import get_spark
except Exception:
    def get_spark(*a, **k):
        raise RuntimeError("Spark indisponivel neste ambiente")

SILVER_DIR = "data/silver/pagamentos"


def build_national_series() -> pd.DataFrame:
    spark = get_spark("forecast-series")
    silver = spark.read.format("delta").load(SILVER_DIR)

    serie = (
        silver.filter(F.col("mes_referencia") == F.col("mes_competencia"))
        .groupBy("mes_referencia")
        .agg(
            F.sum("valor_parcela").alias("valor_total"),
            F.countDistinct("nis_hash").alias("beneficiarios_unicos"),
        )
        .orderBy("mes_referencia")
    )

    df = serie.toPandas()
    spark.stop()

    df["mes_referencia"] = pd.to_datetime(df["mes_referencia"])
    df = df.set_index("mes_referencia").sort_index()
    df["valor_total"] = df["valor_total"].astype(float)
    return df


if __name__ == "__main__":
    df = build_national_series()
    print(df)
    print(f"\n{len(df)} pontos na serie, de {df.index.min().date()} a {df.index.max().date()}")
