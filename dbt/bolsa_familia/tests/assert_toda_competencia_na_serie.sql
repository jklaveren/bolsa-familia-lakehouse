-- Toda competencia que entrou na Silver tem que aparecer na serie temporal.
-- Pega a falha silenciosa: a carga roda, a Gold materializa sem erro e um
-- mes simplesmente some do agregado.

with na_origem as (
    select distinct mes_referencia from {{ ref('stg_pagamentos') }}
),

na_serie as (
    select distinct mes_referencia from {{ ref('gold_evolucao_temporal_nacional') }}
)

select na_origem.mes_referencia
from na_origem
left join na_serie using (mes_referencia)
where na_serie.mes_referencia is null
