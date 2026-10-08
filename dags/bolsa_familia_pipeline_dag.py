"""DAG do pipeline completo Novo Bolsa Familia (Secao 9 do design doc).

ingest_bronze -> clean_silver -> dbt_run -> dbt_test -> notify

Roda via Docker Compose (imagem oficial apache/airflow) — ver docker-compose.yml.
Nao roda na maquina de desenvolvimento local (sem Docker); ver README para a
maquina onde o Airflow e executado.
"""
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# Garante "import src...." mesmo se PYTHONPATH nao propagar pro container
# (docker-compose env var exige recreate, nao so restart — ja causou confusao).
if "/opt/airflow" not in sys.path:
    sys.path.insert(0, "/opt/airflow")

DBT_PROJECT_DIR = "/opt/airflow/dbt/bolsa_familia"

default_args = {
    "owner": "jessica",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def _competencia(context) -> str:
    """AAAAMM da execucao, ou o valor passado em `conf` no trigger manual.

    O agendamento mensal pede a competencia do periodo executado, mas a CGU
    publica cada competencia com atraso — disparar manualmente com
    `{"competencia": "202601"}` permite reprocessar qualquer mes ja publicado.
    """
    conf = (context.get("dag_run").conf or {}) if context.get("dag_run") else {}
    return conf.get("competencia") or context["ds_nodash"][:6]


def _ingest_bronze(**context):
    from src.bronze.ingest import ingest_bronze
    from src.common.spark_session import get_spark

    spark = get_spark("airflow-bronze")
    try:
        ingest_bronze(spark, _competencia(context))
    finally:
        spark.stop()


def _clean_silver(**context):
    from src.common.spark_session import get_spark
    from src.silver.clean import clean_silver
    from src.silver.pseudonymize import get_salt

    spark = get_spark("airflow-silver")
    try:
        clean_silver(spark, _competencia(context), get_salt())
    finally:
        spark.stop()


with DAG(
    dag_id="bolsa_familia_pipeline",
    description="Bronze -> Silver -> dbt run -> dbt test, mensal",
    default_args=default_args,
    schedule_interval="@monthly",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["bolsa-familia"],
) as dag:
    ingest_bronze = PythonOperator(
        task_id="ingest_bronze",
        python_callable=_ingest_bronze,
    )

    clean_silver = PythonOperator(
        task_id="clean_silver",
        python_callable=_clean_silver,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt deps && dbt run --profiles-dir .",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt test --profiles-dir .",
    )

    notify = BashOperator(
        task_id="notify",
        bash_command='echo "Pipeline bolsa_familia concluido com sucesso para {{ ds }}"',
    )

    ingest_bronze >> clean_silver >> dbt_run >> dbt_test >> notify
