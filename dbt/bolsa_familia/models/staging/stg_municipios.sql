-- Dimensao de municipios (distinta a partir da Silver) — usada para o teste
-- de integridade referencial de gold_pagamentos_municipio_mes (Secao 8.2).

select distinct
    codigo_municipio_siafi,
    nome_municipio,
    uf
from {{ ref('stg_pagamentos') }}
