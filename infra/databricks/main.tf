# Job mensal no Databricks Workflows: o mesmo encadeamento da DAG do
# Airflow (bronze -> silver -> dbt run -> dbt test), porem orquestrado pelo
# proprio workspace.
#
# O Docker Compose com Airflow continua servindo o desenvolvimento local,
# onde subir a stack inteira em um comando vale mais do que depender de
# nuvem. Em producao, o job roda onde o dado ja' esta': sem cluster de
# orquestracao para manter, e com retry, alerta e historico nativos.
#
# O job clona o repositorio a cada execucao (git_source), entao o que
# roda em producao e' exatamente o que esta' na branch -- nao ha' copia de
# notebook vivendo solta no workspace.

locals {
  # Cluster pequeno e efemero: a carga e' mensal e cabe num no' unico.
  # Sobe para o job e morre no fim, entao nao ha' cluster ocioso.
  cluster_job = {
    spark_version = "15.4.x-scala2.12"
    node_type_id  = "Standard_DS3_v2"
    num_workers   = 2

    spark_conf = {
      # Particao menor que o padrao: os arquivos de competencia sao
      # grandes e poucos, e 200 particoes deixam tarefas ociosas.
      "spark.sql.shuffle.partitions" = "64"
    }
  }
}

resource "databricks_job" "bolsa_familia_mensal" {
  name        = "bolsa-familia-mensal"
  description = "Bronze -> Silver -> dbt run -> dbt test. Mensal, com reprocesso por competencia."

  # Dia 5 as 06h: a CGU publica a competencia nos primeiros dias do mes.
  schedule {
    quartz_cron_expression = "0 0 6 5 * ?"
    timezone_id            = "America/Sao_Paulo"
    pause_status           = "UNPAUSED"
  }

  # Execucao mensal nao se acumula: se a anterior ainda roda, a nova espera.
  max_concurrent_runs = 1

  git_source {
    url      = var.repo_url
    provider = "gitHub"
    branch   = var.branch
  }

  # Reprocesso de uma competencia ja' publicada, igual ao trigger manual da
  # DAG: basta informar AAAAMM ao disparar o job.
  # Vazio no agendamento: os entrypoints caem no mes anterior sozinhos.
  # Para reprocessar, dispare o job informando AAAAMM.
  parameter {
    name    = "competencia"
    default = ""
  }

  job_cluster {
    job_cluster_key = "principal"

    new_cluster {
      spark_version = local.cluster_job.spark_version
      node_type_id  = local.cluster_job.node_type_id
      num_workers   = local.cluster_job.num_workers
      spark_conf    = local.cluster_job.spark_conf
    }
  }

  task {
    task_key        = "ingest_bronze"
    job_cluster_key = "principal"

    spark_python_task {
      # source = GIT: o arquivo vem do clone da branch, nao do workspace.
      source      = "GIT"
      python_file = "src/bronze/ingest.py"
      parameters  = ["--competencia", "{{job.parameters.competencia}}"]
    }
  }

  task {
    task_key        = "clean_silver"
    job_cluster_key = "principal"
    depends_on { task_key = "ingest_bronze" }

    spark_python_task {
      source      = "GIT"
      python_file = "src/silver/clean.py"
      parameters  = ["--competencia", "{{job.parameters.competencia}}"]
    }
  }

  # dbt_task roda no SQL Warehouse, nao no cluster: o modelo e' SQL puro e
  # nao precisa de executor Spark.
  task {
    task_key = "dbt"
    depends_on { task_key = "clean_silver" }

    dbt_task {
      project_directory = "dbt/bolsa_familia"
      catalog           = var.catalogo
      schema            = var.schema_silver
      warehouse_id      = databricks_sql_endpoint.dbt.id

      # dbt test junto na mesma tarefa: modelo publicado sem teste e'
      # exatamente o que o projeto quer evitar.
      commands = [
        "dbt deps",
        "dbt run",
        "dbt test",
      ]
    }
  }

  dynamic "email_notifications" {
    for_each = var.email_notificacao == "" ? [] : [var.email_notificacao]
    content {
      on_failure = [email_notifications.value]
    }
  }
}

# Warehouse pequeno, com auto-stop curto: o dbt roda alguns minutos por mes.
resource "databricks_sql_endpoint" "dbt" {
  name             = "bolsa-familia-dbt"
  cluster_size     = "2X-Small"
  auto_stop_mins   = 10
  enable_serverless_compute = true
}
