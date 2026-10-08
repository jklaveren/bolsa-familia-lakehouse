output "network" {
  value = docker_network.bolsa_familia.name
}

output "volumes" {
  value = [docker_volume.postgres_db.name, docker_volume.airflow_logs.name]
}

output "airflow_webserver" {
  value = docker_container.airflow_webserver.name
}

output "streamlit_port" {
  value = var.streamlit_port
}
