-- Selecao/renomeacao 1:1 da tabela Silver, sem logica de negocio (Secao 8.1).
-- Isola a fonte: nenhum outro modelo le a source diretamente.

select
    mes_competencia,
    mes_referencia,
    uf,
    codigo_municipio_siafi,
    nome_municipio,
    valor_parcela,
    nis_hash
from {{ source('silver', 'pagamentos') }}
