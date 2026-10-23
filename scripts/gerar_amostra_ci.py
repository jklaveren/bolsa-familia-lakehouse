# -*- coding: utf-8 -*-
"""Gera a amostra sintetica que o CI usa para rodar os 13 testes dbt.

Por que sintetica: a Silver real vive no Databricks e tem centenas de
milhoes de linhas -- nao cabe no repositorio nem roda em runner gratuito.
O que o CI precisa provar nao e' volume, e' que as regras continuam
valendo: unicidade de chave, integridade referencial, dominio de UF e a
soma da Gold batendo com a Silver. Isso uma amostra pequena prova.

Deterministica (seed fixa): rodar de novo gera byte a byte o mesmo CSV,
entao o arquivo so' muda quando a regra muda -- e o diff fica legivel.

    python scripts/gerar_amostra_ci.py
"""
from __future__ import annotations

import csv
import hashlib
import os
import random

SAIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "dbt", "bolsa_familia", "seeds", "seed_pagamentos_amostra.csv")

# Tres competencias para a serie temporal ter mais de um ponto; sem isso
# gold_evolucao_temporal_nacional nasce com uma linha so' e o teste nao
# exercita o group by.
COMPETENCIAS = ["2025-11-01", "2025-12-01", "2026-01-01"]

# Codigo SIAFI real, nome real, UF real -- o teste accepted_values cobre a
# UF e o relationships cobre o municipio, entao valor fora do dominio
# derrubaria o build por motivo errado.
MUNICIPIOS = [
    ("8801", "SAO LEOPOLDO", "RS"),
    ("8585", "PORTO ALEGRE", "RS"),
    ("7107", "CURITIBA", "PR"),
    ("6001", "SAO PAULO", "SP"),
    ("6537", "CAMPINAS", "SP"),
    ("4123", "SALVADOR", "BA"),
    ("1219", "BELEM", "PA"),
    ("2111", "FORTALEZA", "CE"),
    ("6001", "SAO PAULO", "SP"),
    ("9701", "BRASILIA", "DF"),
]

BENEFICIARIOS_POR_MUNICIPIO = 20
SALT = "amostra-ci"  # nao e' o salt de producao: aqui nao ha' NIS real


def nis_hash(municipio: str, i: int) -> str:
    """Mesmo formato da Silver: SHA-256 hex de 64 caracteres."""
    return hashlib.sha256(f"{SALT}:{municipio}:{i}".encode()).hexdigest()


def main() -> None:
    rnd = random.Random(20260108)
    linhas = []
    for competencia in COMPETENCIAS:
        for codigo, nome, uf in MUNICIPIOS:
            for i in range(BENEFICIARIOS_POR_MUNICIPIO):
                # Faixa que cobre mais de um intervalo de R$50, para o
                # histograma de gold_distribuicao_valores ter varias faixas.
                valor = round(rnd.uniform(142.0, 788.0), 2)
                linhas.append({
                    "mes_competencia": competencia,
                    "mes_referencia": competencia,
                    "uf": uf,
                    "codigo_municipio_siafi": codigo,
                    "nome_municipio": nome,
                    "cpf_favorecido": "",  # mascarado na fonte, como em producao
                    "valor_parcela": f"{valor:.2f}",
                    "nis_hash": nis_hash(codigo, i),
                })

    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    with open(SAIDA, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        escritor.writeheader()
        escritor.writerows(linhas)
    print(f"{len(linhas)} linhas em {SAIDA}")


if __name__ == "__main__":
    main()
