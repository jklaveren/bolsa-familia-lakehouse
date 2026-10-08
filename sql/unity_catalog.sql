-- Cartao A2 — Unity Catalog: schema + grants minimos (principio do menor privilegio).
CREATE SCHEMA IF NOT EXISTS bolsa_familia;
GRANT USE SCHEMA ON SCHEMA bolsa_familia TO `data-engineers`;
GRANT SELECT ON SCHEMA bolsa_familia TO `analistas`;
-- escrita restrita ao job bronze->silver (service principal do job):
GRANT CREATE TABLE, MODIFY ON SCHEMA bolsa_familia TO `sp-bolsa-job`;
