-- Mesma agregacao de gold_pagamentos_uf_mes, em nivel de municipio (Secao 8.1).

select
    uf,
    codigo_municipio_siafi,
    nome_municipio,
    mes_referencia,
    sum(valor_parcela) as valor_total,
    avg(valor_parcela) as valor_medio,
    count(distinct nis_hash) as beneficiarios_unicos,
    count(*) as qtd_parcelas
from {{ ref('stg_pagamentos') }}
group by uf, codigo_municipio_siafi, nome_municipio, mes_referencia
