-- Total pago, valor medio e beneficiarios unicos, por UF e mes (Secao 8.1).

select
    uf,
    mes_referencia,
    sum(valor_parcela) as valor_total,
    avg(valor_parcela) as valor_medio,
    count(distinct nis_hash) as beneficiarios_unicos,
    count(*) as qtd_parcelas
from {{ ref('stg_pagamentos') }}
group by uf, mes_referencia
