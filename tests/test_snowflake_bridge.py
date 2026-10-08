"""Cartao 2c — gate: ponte Snowflake gera artefatos a partir do viz (stdlib only)."""
import csv
from pathlib import Path

from scripts.snowflake_bridge import carregar_viz, gerar

REPO = Path(__file__).resolve().parent.parent


def test_viz_existe_e_tem_27_ufs():
    viz = carregar_viz()
    assert viz["ultima_competencia"] == "202601"
    assert len(viz["por_uf"]) == 27


def test_gerar_cria_ddl_csv_uniform(tmp_path):
    viz = carregar_viz()
    gerados = gerar(viz, tmp_path)
    nomes = {p.name for p in gerados}
    assert "stg_pagamentos_uf.sql" in nomes
    assert "uniform_alternativa.sql" in nomes
    csvs = [p for p in gerados if p.suffix == ".csv"]
    assert len(csvs) == 1
    with csvs[0].open(encoding="utf-8") as f:
        linhas = list(csv.reader(f))
    assert linhas[0] == ["competencia", "uf", "linhas", "valor_total"]
    assert len(linhas) == 28  # header + 27 UFs
    total = sum(float(r[3]) for r in linhas[1:])
    assert abs(total - viz["total_valor_silver"]) < 1.0
