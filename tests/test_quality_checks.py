from src.quality.checks import (
    check_row_count_conservation,
    check_schema,
    check_uf_valida,
    check_valor_parcela_range,
)


def test_check_schema_passes_with_all_columns(spark):
    df = spark.createDataFrame(
        [("202601", "202601", "SP", "1", "SAO PAULO", "", "123", "Fulano", "850,00")],
        [
            "mes_competencia", "mes_referencia", "uf", "codigo_municipio_siafi",
            "nome_municipio", "cpf_favorecido", "nis_favorecido",
            "nome_favorecido", "valor_parcela",
        ],
    )
    result = check_schema(df)
    assert result.passed


def test_check_schema_fails_with_missing_column(spark):
    df = spark.createDataFrame([("SP",)], ["uf"])
    result = check_schema(df)
    assert not result.passed
    assert "uf" not in result.detail or "faltando" in result.detail


def test_check_row_count_conservation_exact_match():
    result = check_row_count_conservation(bronze_count=100, silver_count=90, quarantine_count=10)
    assert result.passed


def test_check_row_count_conservation_allows_dedup_reduction():
    result = check_row_count_conservation(bronze_count=100, silver_count=80, quarantine_count=10)
    assert result.passed


def test_check_row_count_conservation_fails_if_more_than_bronze():
    result = check_row_count_conservation(bronze_count=100, silver_count=95, quarantine_count=10)
    assert not result.passed


def test_check_uf_valida_passes_for_known_ufs(spark):
    df = spark.createDataFrame([("SP",), ("RJ",), ("BA",)], ["uf"])
    result = check_uf_valida(df)
    assert result.passed


def test_check_uf_valida_fails_for_unknown_uf(spark):
    df = spark.createDataFrame([("SP",), ("XX",)], ["uf"])
    result = check_uf_valida(df)
    assert not result.passed


def test_check_valor_parcela_range_passes_for_plausible_values(spark):
    df = spark.createDataFrame([(850.00,), (600.00,)], ["valor_parcela"])
    result = check_valor_parcela_range(df)
    assert result.passed


def test_check_valor_parcela_range_fails_for_zero_or_negative(spark):
    df = spark.createDataFrame([(850.00,), (0.00,), (-10.00,)], ["valor_parcela"])
    result = check_valor_parcela_range(df)
    assert not result.passed
