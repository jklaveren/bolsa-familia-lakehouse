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
  description = "Senha do Postgres local. Default apenas para docker local; sobrescreva em qualquer outro ambiente."
  type        = string
  default     = "airflow"
  sensitive   = true
}

variable "airflow_admin_user" {
  description = "Usuario admin local do Airflow."
  type        = string
  default     = "admin"
}

variable "airflow_admin_password" {
  description = "Senha do admin local do Airflow. Defina via TF_VAR_airflow_admin_password ou -var."
  type        = string
  sensitive   = true
}

variable "airflow_admin_firstname" {
  type    = string
  default = "Admin"
}

variable "airflow_admin_lastname" {
  type    = string
  default = "User"
}

variable "airflow_admin_email" {
  type    = string
  default = "admin@example.com"
}
