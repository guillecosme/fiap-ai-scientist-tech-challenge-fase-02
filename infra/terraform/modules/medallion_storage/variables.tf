variable "project" {
  description = "Prefixo do projeto, usado na nomeacao dos recursos"
  type        = string
}

variable "environment" {
  description = "Ambiente (dev, prod, etc.)"
  type        = string
}

variable "bucket_suffix" {
  description = "Sufixo aleatorio para garantir nomes de bucket globalmente unicos sem depender da conta"
  type        = string
}

variable "tags" {
  description = "Tags padrao aplicadas aos recursos"
  type        = map(string)
  default     = {}
}

variable "force_destroy" {
  description = "Permite destruir os buckets mesmo com objetos. Util em dev e localstack; em producao deixe false"
  type        = bool
  default     = false
}

variable "enable_glue_catalog" {
  description = "Cria os databases no Glue Data Catalog. Desligado no localstack, onde a consulta usa DuckDB"
  type        = bool
  default     = true
}
