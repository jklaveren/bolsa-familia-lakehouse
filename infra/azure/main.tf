# Cartao A1: resource group + StorageV2 + Data Lake Gen2 filesystem +
# Databricks workspace (SKU trial) + Key Vault p/ secrets.
resource "azurerm_resource_group" "main" {
  name     = "${var.prefix}-rg"
  location = var.location
}

resource "azurerm_storage_account" "lake" {
  name                     = "${replace(var.prefix, "-", "")}lake"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true # Data Lake Gen2
}

resource "azurerm_storage_data_lake_gen2_filesystem" "bronze" {
  name               = "bronze"
  storage_account_id = azurerm_storage_account.lake.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "silver" {
  name               = "silver"
  storage_account_id = azurerm_storage_account.lake.id
}

resource "azurerm_databricks_workspace" "main" {
  name                = "${var.prefix}-dbw"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.databricks_sku
}

resource "azurerm_key_vault" "main" {
  name                = "${var.prefix}-kv"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tenant_id           = "00000000-0000-0000-0000-000000000000" # substituir pelo tenant real no apply
  sku_name            = "standard"
}
