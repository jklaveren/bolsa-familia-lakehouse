"""Pseudonimizacao de NIS (Secao 5.1 / 7.2 do design doc).

O salt NUNCA e commitado: vem de variavel de ambiente (.env local, ignorado
pelo git). O nome completo do beneficiario e removido nesta camada em diante —
nao existe funcao de pseudonimizacao para nome porque ele simplesmente nao
avanca para Silver/Gold (ver Secao 5.1).
"""
import os
from typing import TYPE_CHECKING, Any

try:
    from pyspark.sql import Column, DataFrame
    from pyspark.sql import functions as F
    _PYSPARK_OK = True
except Exception:
    Column = Any  # type: ignore
    DataFrame = Any  # type: ignore
    F = None  # type: ignore
    _PYSPARK_OK = False
    if TYPE_CHECKING:
        from pyspark.sql import Column, DataFrame

SALT_ENV_VAR = "BOLSA_FAMILIA_PSEUDONYM_SALT"


def get_salt() -> str:
    salt = os.environ.get(SALT_ENV_VAR)
    if not salt:
        raise RuntimeError(
            f"Variavel de ambiente {SALT_ENV_VAR} nao definida. "
            "Defina um salt secreto (ex.: em um .env local, nunca commitado) "
            "antes de rodar a pseudonimizacao."
        )
    return salt


def nis_hash_column(nis_col: Column, salt: str) -> Column:
    if not _PYSPARK_OK:
        raise RuntimeError("nis_hash_column exige pyspark instalado")
    return F.sha2(F.concat(nis_col, F.lit(salt)), 256)


def pseudonymize(df: DataFrame, salt: str, nis_col: str = "nis_favorecido") -> DataFrame:
    """Adiciona nis_hash e remove nis_favorecido / nome_favorecido do DataFrame."""
    if not _PYSPARK_OK:
        raise RuntimeError("pseudonymize exige pyspark instalado")
    return (
        df.withColumn("nis_hash", nis_hash_column(F.col(nis_col), salt))
        .drop(nis_col, "nome_favorecido")
    )
