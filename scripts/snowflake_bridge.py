"""Cartao 2c — ponte Delta Lake local -> Snowflake trial (offline-friendly).

Gera, a partir de docs/viz_gold.json (sem PII, KBs):
  out/snowflake/stg_pagamentos_uf.sql  (DDL + COPY INTO a partir de stage)
  out/snowflake/por_uf_*.csv          (1 CSV por competencia, pronto p/ PUT/COPY)
  out/snowflake/uniform_alternativa.sql (Iceberg UniForm, se trial indisponivel)

Sem acesso real: nada e executado contra Snowflake aqui — o script so gera os
artefatos + imprime o passo a passo. Com credencial, rode os comandos do
docs/snowflake_bridge.md.

Uso:
    python scripts/snowflake_bridge.py
    python scripts/snowflake_bridge.py --out out/snowflake
"""
import argparse
import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VIZ = REPO / "docs" / "viz_gold.json"


def carregar_viz(path: Path = VIZ) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} nao encontrado — gere com python scripts/build_gold_viz.py"
        )
    return json.loads(path.read_text(encoding="utf-8"))


DDL = """-- Ponte Delta -> Snowflake (gerado por scripts/snowflake_bridge.py)
-- Stage externo aponta para os CSVs exportados; rode PUT antes do COPY.
CREATE SCHEMA IF NOT EXISTS BOLSA_FAMILIA;
CREATE TABLE IF NOT EXISTS BOLSA_FAMILIA.PAGAMENTOS_UF (
  competencia STRING,
  uf STRING,
  linhas NUMBER,
  valor_total FLOAT
);
-- PUT file://por_uf_<comp>.csv @~/staged AUTO_COMPRESS=TRUE;
-- COPY INTO BOLSA_FAMILIA.PAGAMENTOS_UF FROM @~/staged/por_uf_<comp>.csv
--   FILE_FORMAT=(TYPE=CSV SKIP_HEADER=1 FIELD_OPTIONALLY_ENCLOSED_BY='\"');
"""

UNIFORM = """-- Alternativa sem trial Snowflake: Iceberg UniForm (Delta Universal Format).
-- No Databricks Runtime 14+: ALTER TABLE ... SET TBLPROPERTIES (
--   'delta.enableIcebergCompatV2'='true', 'delta.universalFormat.enabledFormats'='iceberg');
-- Depois aponte o Snowflake (external volume + catalog) para o mesmo storage.
-- Ver docs/snowflake_bridge.md secao "Plano B".
"""


def gerar(viz: dict, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    gerados = []
    (out_dir / "stg_pagamentos_uf.sql").write_text(DDL, encoding="utf-8")
    gerados.append(out_dir / "stg_pagamentos_uf.sql")
    (out_dir / "uniform_alternativa.sql").write_text(UNIFORM, encoding="utf-8")
    gerados.append(out_dir / "uniform_alternativa.sql")

    por_mes_uf: dict[str, list] = {}
    for item in viz.get("por_uf", []):
        por_mes_uf.setdefault(viz["ultima_competencia"], []).append(item)
    for comp, linhas in por_mes_uf.items():
        csv_path = out_dir / f"por_uf_{comp}.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["competencia", "uf", "linhas", "valor_total"])
            for r in sorted(linhas, key=lambda x: x["uf"]):
                w.writerow([comp, r["uf"], r["linhas"], r["valor"]])
        gerados.append(csv_path)
    return gerados


def main() -> None:
    ap = argparse.ArgumentParser(description="Ponte Delta -> Snowflake (gera artefatos).")
    ap.add_argument("--out", default="out/snowflake")
    ap.add_argument("--viz", default=str(VIZ))
    args = ap.parse_args()
    viz = carregar_viz(Path(args.viz))
    gerados = gerar(viz, REPO / args.out)
    print(f"OK: {len(gerados)} artefatos em {args.out}/")
    for g in gerados:
        print(f" - {g.name}")
    print("Proximo passo: ver docs/snowflake_bridge.md (PUT + COPY INTO com trial).")


if __name__ == "__main__":
    main()
