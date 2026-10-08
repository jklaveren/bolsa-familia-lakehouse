# Cartao A1 — Azure trial (P2-Azure). Apply SÓ com credencial (az login);
# sem credencial, `validate + plan` no CI bastam (cartoes A1/A3).
variable "prefix" {
  type    = string
  default = "bolsafamilia"
}

variable "location" {
  type    = string
  default = "brazilsouth"
}

variable "databricks_sku" {
  description = "SKU trial do workspace Databricks."
  type        = string
  default     = "trial"
}
