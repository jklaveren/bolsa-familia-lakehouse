# Espelho Terraform do docker-compose.yml (local, sem cloud).
# Compose origem: postgres, airflow-init, airflow-webserver, airflow-scheduler, streamlit.

resource "docker_network" "bolsa_familia" {
  name = "bolsa-familia"
}

resource "docker_volume" "postgres_db" {
  name = "postgres-db"
}

resource "docker_volume" "airflow_logs" {
  name = "airflow-logs"
}

resource "docker_image" "postgres" {
  name = var.postgres_image
}

resource "docker_image" "airflow" {
  name = var.airflow_image
}

resource "docker_container" "postgres" {
  name  = "bolsa-familia-postgres"
  image = docker_image.postgres.image_id

  env = [
    "POSTGRES_USER=${var.postgres_user}",
    "POSTGRES_PASSWORD=${var.postgres_password}",
    "POSTGRES_DB=${var.postgres_db}",
  ]

  volumes {
    volume_name    = docker_volume.postgres_db.name
    container_path = "/var/lib/postgresql/data"
  }

  networks_advanced {
    name = docker_network.bolsa_familia.name
  }

  healthcheck {
    test         = ["CMD", "pg_isready", "-U", "airflow"]
    interval     = "5s"
    retries      = 5
    start_period = "10s"
    timeout      = "5s"
  }
}

# airflow-init: one-shot `airflow db migrate + users create` (compose: service airflow-init).
# Em Terraform, modelado como container com must_run=false para rodar ate completar.
resource "docker_container" "airflow_init" {
  name     = "bolsa-familia-airflow-init"
  image    = docker_image.airflow.image_id
  must_run = false

  env = [
    "AIRFLOW__CORE__EXECUTOR=LocalExecutor",
    "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://${var.postgres_user}:${var.postgres_password}@postgres/${var.postgres_db}",
    "AIRFLOW__CORE__LOAD_EXAMPLES=false",
    "AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=false",
    "PYTHONPATH=/opt/airflow",
  ]

  entrypoint = ["/bin/bash", "-c"]
  command = [
    "airflow db migrate && airflow users create --username ${var.airflow_admin_user} --password ${var.airflow_admin_password} --firstname ${var.airflow_admin_firstname} --lastname ${var.airflow_admin_lastname} --role Admin --email ${var.airflow_admin_email}"
  ]

  networks_advanced {
    name = docker_network.bolsa_familia.name
  }
}

resource "docker_container" "airflow_webserver" {
  name  = "bolsa-familia-airflow-webserver"
  image = docker_image.airflow.image_id

  env = [
    "AIRFLOW__CORE__EXECUTOR=LocalExecutor",
    "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://${var.postgres_user}:${var.postgres_password}@postgres/${var.postgres_db}",
    "AIRFLOW__CORE__LOAD_EXAMPLES=false",
    "AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=false",
    "PYTHONPATH=/opt/airflow",
  ]

  command = ["webserver"]

  ports {
    internal = 8080
    external = var.airflow_port
  }

  volumes {
    volume_name    = docker_volume.airflow_logs.name
    container_path = "/opt/airflow/logs"
  }

  networks_advanced {
    name = docker_network.bolsa_familia.name
  }

  restart = "unless-stopped"
}

resource "docker_container" "airflow_scheduler" {
  name  = "bolsa-familia-airflow-scheduler"
  image = docker_image.airflow.image_id

  env = [
    "AIRFLOW__CORE__EXECUTOR=LocalExecutor",
    "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://${var.postgres_user}:${var.postgres_password}@postgres/${var.postgres_db}",
    "AIRFLOW__CORE__LOAD_EXAMPLES=false",
    "AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=false",
    "PYTHONPATH=/opt/airflow",
  ]

  command = ["scheduler"]

  volumes {
    volume_name    = docker_volume.airflow_logs.name
    container_path = "/opt/airflow/logs"
  }

  networks_advanced {
    name = docker_network.bolsa_familia.name
  }

  restart = "unless-stopped"
}

resource "docker_container" "streamlit" {
  name  = "bolsa-familia-streamlit"
  image = docker_image.airflow.image_id

  command = ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]

  ports {
    internal = 8501
    external = var.streamlit_port
  }

  networks_advanced {
    name = docker_network.bolsa_familia.name
  }

  restart = "unless-stopped"
}
