"""Validacoes automaticas Bronze -> Silver (Secao 12.1 do design doc).

Cada check retorna um QualityCheckResult; run_all_checks agrega tudo em um
relatorio (Secao 12: "Validacoes de qualidade de dados explicitas ... com
relatorio de execucao").
"""
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

try:
    from pyspark.sql import DataFrame
    from pyspark.sql import functions as F
    _PYSPARK_OK = True
except Exception:  # ambiente sem pyspark (CI leve / dev sem Java): import continua valido
    DataFrame = Any  # type: ignore
    F = None  # type: ignore
    _PYSPARK_OK = False
    if TYPE_CHECKING:
        from pyspark.sql import DataFrame

UFS_VALIDAS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO",
}

EXPECTED_BRONZE_COLUMNS = {
    "mes_competencia", "mes_referencia", "uf", "codigo_municipio_siafi",
    "nome_municipio", "cpf_favorecido", "nis_favorecido", "nome_favorecido",
    "valor_parcela",
}


@dataclass
class QualityCheckResult:
    name: str
    passed: bool
    detail: str


def check_row_count_conservation(
    bronze_count: int, silver_count: int, quarantine_count: int
) -> QualityCheckResult:
    ok = (silver_count + quarantine_count) <= bronze_count
    exact = (silver_count + quarantine_count) == bronze_count
    detail = (
        f"bronze={bronze_count} silver={silver_count} quarentena={quarantine_count} "
        f"(diferenca esperada = deduplicacao: {bronze_count - silver_count - quarantine_count})"
    )
    # silver+quarentena pode ser MENOR que bronze por causa da deduplicacao
    # (dropDuplicates), nunca maior — nenhuma linha pode ser "inventada".
    return QualityCheckResult("contagem_conservada", ok, detail)


def check_schema(df: DataFrame) -> QualityCheckResult:
    missing = EXPECTED_BRONZE_COLUMNS - set(df.columns)
    ok = len(missing) == 0
    detail = "todas as colunas esperadas presentes" if ok else f"colunas faltando: {missing}"
    return QualityCheckResult("schema_bronze", ok, detail)


def check_valor_parcela_range(
    df: DataFrame, valor_col: str = "valor_parcela", max_valor: float = 5000.0
) -> QualityCheckResult:
    """max_valor=5000 e um teto de sanidade, nao um limite oficial do programa.
    Base empirica: competencia real 202601 tem min=25.00, max=3956.00,
    media=666.26 (verificado em 15/09/2026) — 5000 da margem sem mascarar
    outliers genuinos.
    """
    if not _PYSPARK_OK:
        raise RuntimeError("check_valor_parcela_range exige pyspark instalado")
    fora_da_faixa = df.filter(
        (F.col(valor_col) <= 0) | (F.col(valor_col) >= max_valor)
    ).count()
    ok = fora_da_faixa == 0
    detail = f"{fora_da_faixa} linhas com valor_parcela fora de (0, {max_valor})"
    return QualityCheckResult("valor_parcela_faixa_plausivel", ok, detail)


def check_uf_valida(df: DataFrame, uf_col: str = "uf") -> QualityCheckResult:
    if not _PYSPARK_OK:
        raise RuntimeError("check_uf_valida exige pyspark instalado")
    ufs_encontradas = {r[uf_col] for r in df.select(uf_col).distinct().collect()}
    invalidas = ufs_encontradas - UFS_VALIDAS
    ok = len(invalidas) == 0
    detail = "todas as UFs pertencem ao conjunto valido" if ok else f"UFs invalidas: {invalidas}"
    return QualityCheckResult("uf_valida", ok, detail)


def run_all_checks(
    bronze: DataFrame, silver: DataFrame, quarentena: DataFrame
) -> list[QualityCheckResult]:
    results = [
        check_schema(bronze),
        check_row_count_conservation(bronze.count(), silver.count(), quarentena.count()),
        check_uf_valida(silver),
    ]
    if "valor_parcela" in silver.columns:
        results.append(check_valor_parcela_range(silver))
    return results


def print_report(results: list[QualityCheckResult]) -> bool:
    print("\n=== Relatorio de qualidade de dados ===")
    all_ok = True
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        if not r.passed:
            all_ok = False
        print(f"[{status}] {r.name}: {r.detail}")
    print(f"=== {'TODOS OS CHECKS PASSARAM' if all_ok else 'HA CHECKS FALHANDO'} ===\n")
    return all_ok
