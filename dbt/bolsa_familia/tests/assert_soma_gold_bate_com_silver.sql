-- Teste customizado (Secao 8.2): soma total de valor_parcela na Gold deve
-- ser identica a soma direta na Silver. dbt tests "falham" quando a query
-- retorna alguma linha — aqui, so retorna linha se as somas divergirem.

with soma_silver as (
    select sum(valor_parcela) as total from {{ ref('stg_pagamentos') }}
),

soma_gold as (
    select sum(valor_total) as total from {{ ref('gold_pagamentos_uf_mes') }}
)

select
    soma_silver.total as total_silver,
    soma_gold.total as total_gold
from soma_silver
cross join soma_gold
where abs(soma_silver.total - soma_gold.total) > 0.01
