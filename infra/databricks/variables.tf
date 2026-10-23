variable "databricks_host" {
  description = "URL do workspace, ex.: https://dbc-xxxxxxxx-xxxx.cloud.databricks.com"
  type        = string
}

variable "databricks_token" {
  description = "Personal access token do workspace."
  type        = string
  sensitive   = true
}

variable "catalogo" {
  description = "Catalogo Unity onde vivem as camadas."
  type        = string
  default     = "workspace"
}

variable "schema_silver" {
  type    = string
  default = "bolsa_familia"
}

variable "repo_url" {
  description = "Repositorio Git que o job clona a cada execucao."
  type        = string
  default     = "https://github.com/jklaveren/bolsa-familia-lakehouse"
}

variable "branch" {
  type    = string
  default = "main"
}

variable "email_notificacao" {
  description = "Para onde vai o aviso de falha. Vazio desliga a notificacao."
  type        = string
  default     = ""
}
