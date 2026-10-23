-- Valor total negativo ou mes sem nenhum beneficiario so' acontece por erro
-- de agregacao (join que multiplica, filtro que zera). Um sum() errado nao
-- quebra a query -- quebra o numero.

select
    uf,
    mes_referencia,
    valor_total,
    beneficiarios_unicos
from {{ ref('gold_evolucao_temporal_nacional') }}
where valor_total < 0
   or beneficiarios_unicos < 1
