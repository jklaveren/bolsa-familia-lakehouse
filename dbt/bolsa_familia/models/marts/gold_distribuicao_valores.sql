-- Histograma de faixas de valor pago, em intervalos de R$50 (Secao 8.1) —
-- usado para detectar concentracao/outliers na distribuicao de valores.

with faixas as (
    select
        valor_parcela,
        floor(valor_parcela / 50) * 50 as faixa_inicio
    from {{ ref('stg_pagamentos') }}
)

select
    faixa_inicio,
    faixa_inicio + 50 as faixa_fim,
    count(*) as qtd_parcelas,
    sum(valor_parcela) as valor_total_na_faixa
from faixas
group by faixa_inicio
order by faixa_inicio
