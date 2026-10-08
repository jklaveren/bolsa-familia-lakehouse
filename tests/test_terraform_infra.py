"""Cartao 2a — gate: infra/main.tf espelha o docker-compose.yml (stdlib only)."""
from pathlib import Path
import re

REPO = Path(__file__).resolve().parent.parent
MAIN = REPO / "infra" / "main.tf"
COMPOSE = REPO / "docker-compose.yml"


def _read(p: Path) -> str:
    assert p.exists(), f"faltando {p}"
    return p.read_text(encoding="utf-8")


def test_terraform_files_exist():
    for f in ["versions.tf", "variables.tf", "main.tf", "outputs.tf"]:
        assert (REPO / "infra" / f).exists(), f"infra/{f} nao encontrado"


def test_terraform_contem_recursos_espelho_do_compose():
    tf = _read(MAIN)
    for recurso in [
        'resource "docker_network"',
        'resource "docker_volume"',
        'resource "docker_container" "postgres"',
        'resource "docker_container" "airflow_init"',
        'resource "docker_container" "airflow_webserver"',
        'resource "docker_container" "airflow_scheduler"',
        'resource "docker_container" "streamlit"',
    ]:
        assert recurso in tf, f"main.tf sem {recurso}"


def test_terraform_paridade_servicos_com_compose():
    tf = _read(MAIN)
    yml = _read(COMPOSE)
    var_tf = _read(REPO / "infra" / "variables.tf")
    # defaults das imagens no variables.tf batem com o compose; main.tf usa as vars
    assert "postgres:16" in var_tf and "postgres:16" in yml
    assert "apache/airflow:2.9.3" in var_tf
    assert "var.postgres_image" in tf and "var.airflow_image" in tf
    assert "8080" in tf and "8080" in yml
    assert "8501" in tf and "8501" in yml
    assert "LocalExecutor" in tf


def test_terraform_sintaxe_basica_balanceada():
    tf = _read(MAIN)
    assert tf.count("{") == tf.count("}"), "chaves desbalanceadas em main.tf"
    assert tf.count('"') % 2 == 0, "aspas desbalanceadas em main.tf"
    assert re.search(r'terraform\s*\{', (REPO / "infra" / "versions.tf").read_text(encoding="utf-8"))
