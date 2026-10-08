#!/usr/bin/env bash
# Fase 10 (Secao 10) — processa Bronze + Silver para cada competencia
# historica ja baixada em data/raw/*.zip que ainda nao tem Bronze.
set -e
cd /c/DataBricks
source scripts/env.sh
set -a && source .env && set +a
export MSYS_NO_PATHCONV=1

PY=./.venv/Scripts/python.exe

for zip in data/raw/*_NovoBolsaFamilia.zip; do
  base=$(basename "$zip")
  comp="${base%%_*}"
  if [ "$comp" = "202601" ]; then
    echo "=== [$comp] ja processado anteriormente, pulando ==="
    continue
  fi
  echo "=== [$comp] iniciando ==="
  $PY -m src.bronze.ingest --competencia "$comp"
  $PY -m src.silver.clean --competencia "$comp"
  rm -rf "data/raw/${comp}" # descarta o CSV extraido (mantem so o .zip), Secao 10.1
  echo "=== [$comp] concluido ==="
done
echo "TODAS AS COMPETENCIAS PROCESSADAS"
