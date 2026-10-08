output "resource_group" {
  value = azurerm_resource_group.main.name
}

output "storage_account" {
  value = azurerm_storage_account.lake.name
}

output "databricks_workspace" {
  value = azurerm_databricks_workspace.main.name
}

output "key_vault" {
  value = azurerm_key_vault.main.name
}
