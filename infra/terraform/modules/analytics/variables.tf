variable "project" {
  description = "Prefixo do projeto"
  type        = string
}

variable "environment" {
  description = "Ambiente (dev, prod, etc.)"
  type        = string
}

variable "gold_bucket" {
  description = "Nome do bucket Gold, onde o crawler e o Athena leem"
  type        = string
}

variable "gold_database" {
  description = "Database do Glue Data Catalog da camada Gold"
  type        = string
}

variable "role_arn" {
  description = "ARN da role usada pelo crawler do Glue"
  type        = string
}

variable "bytes_scanned_cutoff" {
  description = "Teto de bytes lidos por query no Athena, como guarda de custo (padrao 1 GB)"
  type        = number
  default     = 1073741824
}

variable "tags" {
  description = "Tags padrao"
  type        = map(string)
  default     = {}
}
