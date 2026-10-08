"""Camada gold-viz: agregados minúsculos (JSON) para o dashboard — sem Spark.

Lê os parquet Delta ativos (via _delta_log, respeitando removes), agrega com
pyarrow puro (sem pandas) e grava docs/viz_gold.json (KBs, versionável, sem PII).
Uso: python scripts/build_gold_viz.py
"""
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parent.parent
SILVER = REPO / "data" / "silver" / "pagamentos"
BRONZE = REPO / "data" / "bronze" / "pagamentos"
QUARENTENA = REPO / "data" / "silver" / "quarentena_sem_nis"
SAIDA = REPO / "docs" / "viz_gold.json"


def active_parquet(table_dir: Path) -> list[Path]:
    """Arquivos parquet ativos segundo o _delta_log (adds menos removes)."""
    active: dict[str, Path] = {}
    for jf in sorted((table_dir / "_delta_log").glob("*.json")):
        for line in jf.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if "add" in e and "path" in e["add"]:
                active[e["add"]["path"]] = table_dir / e["add"]["path"]
            elif "remove" in e and "path" in e["remove"]:
                active.pop(e["remove"]["path"], None)
    return sorted(active.values())


def comp(mes) -> str:
    return f"{mes.year:04d}{mes.month:02d}"


def agrega_silver() -> tuple[dict, dict]:
    por_mes_uf: dict[tuple[str, str], list] = defaultdict(lambda: [0, 0.0])
    arquivos = active_parquet(SILVER)
    print(f"silver: {len(arquivos)} arquivos ativos")
    for i, f in enumerate(arquivos):
        if i % 50 == 0:
            print(f"  ...{i}/{len(arquivos)}")
        uf = f.parent.name.split("=", 1)[1] if "=" in f.parent.name else "?"
        t = pq.read_table(f, columns=["mes_competencia", "valor_parcela"])
        g = t.group_by(["mes_competencia"]).aggregate(
            [("valor_parcela", "sum"), ("valor_parcela", "count")]
        )
        meses = g.column("mes_competencia").to_pylist()
        somas = g.column("valor_parcela_sum").to_pylist()
        conts = g.column("valor_parcela_count").to_pylist()
        for mes, soma, n in zip(meses, somas, conts):
            k = (comp(mes), uf)
            por_mes_uf[k][0] += n or 0
            por_mes_uf[k][1] += float(soma or 0)
    return por_mes_uf, {"arquivos": len(arquivos)}


def conta_bronze() -> dict[str, int]:
    """Linhas bronze por competência (só metadata, sem ler dados)."""
    out: dict[str, int] = defaultdict(int)
    for f in active_parquet(BRONZE):
        # partição mes_competencia=YYYYMM está no path
        c = next((p.split("=", 1)[1] for p in f.parts if p.startswith("mes_competencia=")),
                 f.parent.name.split("=", 1)[1] if "=" in f.parent.name else "?")
        out[c] += pq.ParquetFile(f).metadata.num_rows
    return dict(out)


def conta_total(table_dir: Path) -> tuple[int, int]:
    arquivos = active_parquet(table_dir)
    total = sum(pq.ParquetFile(f).metadata.num_rows for f in arquivos)
    return total, len(arquivos)


def main() -> None:
    por_mes_uf, info = agrega_silver()
    bronze = conta_bronze()
    quar_total, quar_arq = conta_total(QUARENTENA)

    meses = sorted({m for m, _ in por_mes_uf})
    serie = []
    for m in meses:
        linhas = sum(n for (mm, _), (n, _) in por_mes_uf.items() if mm == m)
        valor = sum(v for (mm, _), (_, v) in por_mes_uf.items() if mm == m)
        serie.append({"competencia": m, "linhas_silver": linhas,
                      "valor_total": round(valor, 2),
                      "linhas_bronze": bronze.get(m)})

    ultima = meses[-1]
    por_uf = [{"uf": uf, "linhas": n, "valor": round(v, 2)}
              for (m, uf), (n, v) in sorted(por_mes_uf.items()) if m == ultima]

    saida = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "competencias": meses,
        "total_linhas_silver": sum(s["linhas_silver"] for s in serie),
        "total_valor_silver": round(sum(s["valor_total"] for s in serie), 2),
        "quarentena_linhas": quar_total,
        "serie": serie,
        "ultima_competencia": ultima,
        "por_uf": por_uf,
    }
    SAIDA.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK: {SAIDA} ({SAIDA.stat().st_size/1024:.1f} KB) | "
          f"{saida['total_linhas_silver']:,} linhas | R$ {saida['total_valor_silver']:,.2f}")


if __name__ == "__main__":
    main()
