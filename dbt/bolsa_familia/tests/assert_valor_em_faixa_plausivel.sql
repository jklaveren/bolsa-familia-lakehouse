-- Faixa de valor fora do plausivel indica erro de leitura do arquivo, nao
-- beneficio: nao existe parcela negativa nem de cinco digitos no programa.
-- Diferente de not_null, este teste pega o dado presente e errado -- que e'
-- o que passa despercebido.

select
    faixa_inicio,
    qtd_parcelas,
    valor_total_na_faixa
from {{ ref('gold_distribuicao_valores') }}
where faixa_inicio < 0
   or faixa_inicio >= 10000
