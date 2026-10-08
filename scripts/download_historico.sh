#!/usr/bin/env bash
# Fase 10 — baixa a amostra historica trimestral (mar/2023 a jun/2026).
set -e
cd /c/DataBricks
COMPETENCIAS="202303 202306 202309 202312 202403 202406 202409 202412 202503 202506 202509 202512 202603 202606"
for comp in $COMPETENCIAS; do
  dest="data/raw/${comp}_NovoBolsaFamilia.zip"
  if [ -f "$dest" ]; then
    echo "[$comp] ja existe, pulando download"
    continue
  fi
  echo "[$comp] baixando..."
  curl -fL --max-time 300 -A "Mozilla/5.0" \
    -o "$dest" \
    "https://dadosabertos-download.cgu.gov.br/PortalDaTransparencia/saida/novo-bolsa-familia/${comp}_NovoBolsaFamilia.zip"
  echo "[$comp] OK ($(du -h "$dest" | cut -f1))"
  sleep 3
done
echo "TODOS OS DOWNLOADS CONCLUIDOS"
