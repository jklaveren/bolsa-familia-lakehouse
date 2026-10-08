from src.silver.pseudonymize import nis_hash_column, pseudonymize


def test_nis_hash_is_deterministic_for_same_salt(spark):
    df = spark.createDataFrame([("12345",), ("67890",)], ["nis"])
    df = df.withColumn("h1", nis_hash_column(df["nis"], "salt-fixo"))
    df = df.withColumn("h2", nis_hash_column(df["nis"], "salt-fixo"))
    rows = df.collect()
    assert all(r["h1"] == r["h2"] for r in rows)


def test_nis_hash_differs_across_salts(spark):
    df = spark.createDataFrame([("12345",)], ["nis"])
    a = df.withColumn("h", nis_hash_column(df["nis"], "salt-a")).collect()[0]["h"]
    b = df.withColumn("h", nis_hash_column(df["nis"], "salt-b")).collect()[0]["h"]
    assert a != b


def test_nis_hash_differs_across_different_nis(spark):
    df = spark.createDataFrame([("11111",), ("22222",)], ["nis"])
    df = df.withColumn("h", nis_hash_column(df["nis"], "salt-fixo"))
    hashes = [r["h"] for r in df.collect()]
    assert hashes[0] != hashes[1]


def test_pseudonymize_drops_nis_and_nome(spark):
    df = spark.createDataFrame(
        [("12345", "Fulano de Tal", "SP")],
        ["nis_favorecido", "nome_favorecido", "uf"],
    )
    result = pseudonymize(df, salt="salt-fixo")
    assert "nis_favorecido" not in result.columns
    assert "nome_favorecido" not in result.columns
    assert "nis_hash" in result.columns
    assert "uf" in result.columns
