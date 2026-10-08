"""Factory de SparkSession configurada com suporte a Delta Lake."""


def get_spark(app_name: str = "bolsa-familia-pipeline"):
    try:
        from delta import configure_spark_with_delta_pip
        from pyspark.sql import SparkSession
    except Exception as exc:
        raise RuntimeError(
            "PySpark/Delta nao disponiveis neste ambiente "
            "(instale requirements.txt com Python 3.11 + JDK 17). "
            f"Detalhe: {exc}"
        ) from exc
    builder = (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config("spark.sql.session.timeZone", "America/Sao_Paulo")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.master", "local[*]")
        .config("spark.driver.memory", "4g")
        .config("spark.sql.shuffle.partitions", "8")
    )
    return configure_spark_with_delta_pip(builder).getOrCreate()
