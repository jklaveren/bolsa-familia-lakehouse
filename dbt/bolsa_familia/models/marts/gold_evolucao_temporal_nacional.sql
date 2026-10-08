-- Serie temporal nacional e por UF — valor total pago e beneficiarios unicos
-- por mes amostrado (Secao 10.2). Alimenta a comparacao VAR vs. rede neural.
-- Depende da amostra historica multi-competencia (Secao 10.1), nao apenas de
-- 202601 — so tera mais de um ponto quando as competencias trimestrais
-- adicionais forem ingeridas.

with por_uf_mes as (
    select
        uf,
        mes_referencia,
        sum(valor_parcela) as valor_total,
        count(distinct nis_hash) as beneficiarios_unicos
    from {{ ref('stg_pagamentos') }}
    group by uf, mes_referencia
),

nacional as (
    select
        cast(null as string) as uf,
        mes_referencia,
        sum(valor_parcela) as valor_total,
        count(distinct nis_hash) as beneficiarios_unicos
    from {{ ref('stg_pagamentos') }}
    group by mes_referencia
)

select * from por_uf_mes
union all
select * from nacional
