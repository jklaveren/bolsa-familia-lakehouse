import datetime

from src.silver.clean import parse_valor, split_quarantine, to_first_of_month


def test_to_first_of_month_parses_aaaamm(spark):
    df = spark.createDataFrame([("202601",), ("202312",)], ["mes"])
    df = df.withColumn("data", to_first_of_month("mes"))
    rows = {r["mes"]: r["data"] for r in df.collect()}
    assert rows["202601"] == datetime.date(2026, 1, 1)
    assert rows["202312"] == datetime.date(2023, 12, 1)


def test_parse_valor_converts_comma_decimal(spark):
    df = spark.createDataFrame([("850,00",), ("1234,56",)], ["valor_parcela"])
    df = df.withColumn("valor", parse_valor("valor_parcela"))
    rows = {r["valor_parcela"]: float(r["valor"]) for r in df.collect()}
    assert rows["850,00"] == 850.00
    assert rows["1234,56"] == 1234.56


def test_split_quarantine_separates_missing_nis(spark):
    df = spark.createDataFrame(
        [
            ("12345", "SP"),
            ("", "RJ"),
            (None, "BA"),
            ("67890", "MG"),
        ],
        ["nis_favorecido", "uf"],
    )
    com_nis, sem_nis = split_quarantine(df)
    assert com_nis.count() == 2
    assert sem_nis.count() == 2
    assert {r["nis_favorecido"] for r in com_nis.collect()} == {"12345", "67890"}


def test_split_quarantine_preserves_total_row_count(spark):
    df = spark.createDataFrame(
        [("12345", "SP"), ("", "RJ"), (None, "BA")],
        ["nis_favorecido", "uf"],
    )
    com_nis, sem_nis = split_quarantine(df)
    assert com_nis.count() + sem_nis.count() == df.count()
