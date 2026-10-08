# Cartao 2a — IaC local que espelha o docker-compose.yml (Secao 9.2).
# Sem cloud real: `terraform validate` + `plan` verdes bastam.
# Paridade com compose: rede bolsa-familia, volumes postgres-db/airflow-logs,
# servicos postgres, airflow-init (one-shot), airflow-webserver, airflow-scheduler, streamlit.

variable "airflow_image" {
  description = "Imagem do Airflow (build local do Dockerfile.airflow por padrao via compose; aqui tag pronta)."
  type        = string
  default     = "apache/airflow:2.9.3"
}

variable "postgres_image" {
  type    = string
  default = "postgres:16"
}

variable "streamlit_port" {
  type    = number
  default = 8501
}

variable "airflow_port" {
  type    = number
  default = 8080
}

variable "postgres_db" {
  type    = string
  default = "airflow"
}

variable "postgres_user" {
  type    = string
  default = "airflow"
}

variable "postgres_password" {
  type      = string
  default   = "airflow"
  sensitive = true
}
