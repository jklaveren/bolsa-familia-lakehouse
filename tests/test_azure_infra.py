"""Cartoes A1-A3 — gate: Azure IaC + job + Unity Catalog (stdlib only)."""
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
AZ = REPO / "infra" / "azure"


def _read(p: Path) -> str:
    assert p.exists(), f"faltando {p}"
    return p.read_text(encoding="utf-8")


def test_azure_tf_files_exist():
    for f in ["versions.tf", "variables.tf", "main.tf", "outputs.tf"]:
        assert (AZ / f).exists(), f"infra/azure/{f} nao encontrado"


def test_azure_main_tem_recursos_minimos():
    tf = _read(AZ / "main.tf")
    for r in [
        'resource "azurerm_resource_group"',
        'resource "azurerm_storage_account"',
        'resource "azurerm_storage_data_lake_gen2_filesystem"',
        'resource "azurerm_databricks_workspace"',
        'resource "azurerm_key_vault"',
    ]:
        assert r in tf, f"azure/main.tf sem {r}"
    assert tf.count("{") == tf.count("}")


def test_azure_job_notebook_usa_abfss_e_secret():
    nb = _read(REPO / "notebooks" / "azure_bronze_silver.py")
    assert "abfss://" in nb
    assert "dbutils.secrets.get" in nb
    assert "nis_hash" in nb
    assert "nome_favorecido" in nb  # expurgo LGPD portado


def test_unity_catalog_tem_schema_e_grants():
    sql = _read(REPO / "sql" / "unity_catalog.sql")
    assert "CREATE SCHEMA" in sql
    assert "GRANT" in sql


def test_docs_azure_existe():
    assert (REPO / "docs" / "azure.md").exists()
