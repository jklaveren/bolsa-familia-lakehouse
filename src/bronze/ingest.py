"""Camada Bronze — ingestao raw do Novo Bolsa Familia (Secao 7.1 do design doc).

Le o CSV original (ISO-8859-1, delimitado por ';') sem nenhuma transformacao de
negocio, mantem todas as colunas como string (schema-on-read) e grava em Delta
Lake particionado por mes_competencia. Nenhuma linha e descartada nesta camada.
"""
import argparse
import zipfile
from pathlib import Path

import requests
from typing import TYPE_CHECKING, Any

try:
    from pyspark.sql import DataFrame, SparkSession
    from pyspark.sql.types import StringType, StructField, StructType
    _PYSPARK_OK = True
except Exception:
    DataFrame = Any  # type: ignore
    SparkSession = Any  # type: ignore
    StringType = StructField = StructType = None  # type: ignore
    _PYSPARK_OK = False
    if TYPE_CHECKING:
        from pyspark.sql import DataFrame, SparkSession

try:
    from src.common.spark_session import get_spark
except Exception:
    def get_spark(*a, **k):
        raise RuntimeError("Spark indisponivel neste ambiente")

RAW_DIR = Path("data/raw")
BRONZE_DIR = Path("data/bronze/pagamentos")
DOWNLOAD_URL = (
    "https://dadosabertos-download.cgu.gov.br/PortalDaTransparencia/saida/"
    "novo-bolsa-familia/{competencia}_NovoBolsaFamilia.zip"
)

# Nomes originais do arquivo (ISO-8859-1) -> nomes normalizados (snake_case ascii).
# A normalizacao de nome de coluna nao e uma transformacao de negocio: os valores
# permanecem string, crus, identicos ao arquivo fonte.
COLUMN_MAP = {
    "MÊS COMPETÊNCIA": "mes_competencia",
    "MÊS REFERÊNCIA": "mes_referencia",
    "UF": "uf",
    "CÓDIGO MUNICÍPIO SIAFI": "codigo_municipio_siafi",
    "NOME MUNICÍPIO": "nome_municipio",
    "CPF FAVORECIDO": "cpf_favorecido",
    "NIS FAVORECIDO": "nis_favorecido",
    "NOME FAVORECIDO": "nome_favorecido",
    "VALOR PARCELA": "valor_parcela",
}

SCHEMA = StructType([StructField(c, StringType(), True) for c in COLUMN_MAP]) if _PYSPARK_OK else None


def download_zip(competencia: str) -> Path:
    """Baixa o zip da competencia do Portal da Transparencia, se ainda nao existir.

    A ingestao busca o dado na fonte em vez de exigir download manual — e o que
    permite a DAG do Airflow rodar em qualquer maquina sem preparo previo.
    """
    zip_path = RAW_DIR / f"{competencia}_NovoBolsaFamilia.zip"
    if zip_path.exists():
        return zip_path

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    url = DOWNLOAD_URL.format(competencia=competencia)
    parcial = zip_path.with_suffix(".zip.parcial")

    print(f"Baixando {url} ...")
    with requests.get(url, stream=True, timeout=(30, 600)) as resp:
        resp.raise_for_status()
        with parcial.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)

    # So renomeia no fim: evita deixar um zip truncado que parece valido se a
    # conexao cair no meio do download.
    parcial.rename(zip_path)
    print(f"Download concluido: {zip_path} ({zip_path.stat().st_size} bytes)")
    return zip_path


def extract_csv(competencia: str) -> Path:
    """Garante o zip da competencia (baixando se preciso) e extrai o CSV."""
    zip_path = download_zip(competencia)
    extract_dir = RAW_DIR / competencia

    csvs = list(extract_dir.glob("*.csv")) if extract_dir.exists() else []
    if not csvs:
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)
        csvs = list(extract_dir.glob("*.csv"))

    if not csvs:
        raise FileNotFoundError(f"Nenhum .csv encontrado dentro de {zip_path}")
    return csvs[0]


def read_raw(spark: SparkSession, csv_path: Path) -> DataFrame:
    raw_schema = StructType(
        [StructField(name, StringType(), True) for name in COLUMN_MAP]
    )
    df = (
        spark.read.option("header", True)
        .option("sep", ";")
        .option("encoding", "ISO-8859-1")
        .option("quote", '"')
        .option("multiLine", True)
        .schema(raw_schema)
        .csv(str(csv_path))
    )
    # csv() com schema explicito usa os nomes do schema, entao renomeamos as
    # colunas de origem (acentuadas) para o schema normalizado via alias posicional.
    return df


def ingest_bronze(spark: SparkSession, competencia: str) -> DataFrame:
    csv_path = extract_csv(competencia)

    header_line = csv_path.open(encoding="ISO-8859-1").readline()
    original_columns = [c.strip().strip('"') for c in header_line.strip().split(";")]
    ordered_targets = [COLUMN_MAP[c] for c in original_columns]

    df_raw = (
        spark.read.option("header", True)
        .option("sep", ";")
        .option("encoding", "ISO-8859-1")
        .option("quote", '"')
        .option("multiLine", True)
        .csv(str(csv_path))
    )
    for original, target in zip(df_raw.columns, ordered_targets):
        df_raw = df_raw.withColumnRenamed(original, target)

    (
        df_raw.write.format("delta")
        .mode("overwrite")
        .partitionBy("mes_competencia")
        .option("replaceWhere", f"mes_competencia = '{competencia}'")
        .save(str(BRONZE_DIR))
    )
    return df_raw


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingestao Bronze — Novo Bolsa Familia")
    parser.add_argument("--competencia", required=True, help="AAAAMM, ex: 202601")
    args = parser.parse_args()

    spark = get_spark("bronze-ingest")
    df = ingest_bronze(spark, args.competencia)
    total = df.count()
    print(f"Bronze OK — competencia={args.competencia} linhas={total}")
    spark.stop()


if __name__ == "__main__":
    main()
