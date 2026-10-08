# Azure (P2-Azure) — Cartão A3

> Critério final: `terraform apply` executado 1x de verdade + job verde + merge.
> Até lá, este doc registra o plano, os outputs esperados e os custos do trial.
> Sem credencial ativa, `validate + plan` no CI é o gate (não inventar outputs).

## Recursos (infra/azure/main.tf)

| Recurso | Nome | Obs |
|---|---|---|
| Resource group | `bolsafamilia-rg` | `brazilsouth` |
| StorageV2 + HNS (Gen2) | `bolsafamilialake` | filesystems `bronze`, `silver` |
| Databricks workspace | `bolsafamilia-dbw` | SKU `trial` |
| Key Vault | `bolsafamilia-kv` | salt + segredos, nunca no repo |

## Job Databricks (Cartão A2)

- Notebook: `notebooks/azure_bronze_silver.py` (port do `src/silver/clean.py` p/ `abfss://`).
- Unity Catalog: `sql/unity_catalog.sql` (schema + grants mínimos).
- Cluster: DBR 14+, 1 worker (trial). Conf: `bolsa.storage_account`, `bolsa.competencia`.
- Secret: scope `bolsa-kv` → Key Vault (`pseudonym-salt`).

## Outputs esperados do job verde (colar após o apply real)

```
Silver OK no ADLS — competencia=202601 silver=<n>
```

## Custos do trial

- Azure free (30 dias) + Databricks trial: custo $0 se destruir (`terraform destroy`)
  após a evidência. Não deixar cluster ligado: auto-terminate 30 min.
- Storage LRS ~R$ 0,10/GB/mês — amostra trimestral (~GBs) é centavos.

## Ativação (usuária, na hora — créditos expiram)

```bash
az login
cd infra/azure
terraform init
terraform validate
terraform plan -out=tfplan
terraform apply tfplan   # 1x de verdade, colar outputs aqui
```
