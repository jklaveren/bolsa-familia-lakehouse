output "job_id" {
  description = "ID do job mensal no Databricks Workflows."
  value       = databricks_job.bolsa_familia_mensal.id
}

output "job_url" {
  description = "Link direto para o job no workspace."
  value       = "${var.databricks_host}/jobs/${databricks_job.bolsa_familia_mensal.id}"
}

output "warehouse_id" {
  description = "SQL Warehouse usado pela tarefa dbt."
  value       = databricks_sql_endpoint.dbt.id
}
