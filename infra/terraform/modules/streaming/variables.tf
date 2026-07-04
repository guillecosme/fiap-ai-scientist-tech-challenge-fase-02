variable "project" {
  description = "Prefixo do projeto"
  type        = string
}

variable "environment" {
  description = "Ambiente (dev, prod, etc.)"
  type        = string
}

variable "bronze_bucket" {
  description = "Nome do bucket Bronze, destino dos eventos consumidos"
  type        = string
}

variable "role_arn" {
  description = "ARN da role usada pela Lambda consumidora"
  type        = string
}

variable "role_name" {
  description = "Nome da role, para anexar a politica de leitura do Kinesis"
  type        = string
}

variable "use_localstack" {
  description = "Quando true, injeta o endpoint do LocalStack na Lambda"
  type        = bool
  default     = false
}

variable "localstack_endpoint" {
  description = "Endpoint do LocalStack"
  type        = string
  default     = "http://localhost:4566"
}

variable "tags" {
  description = "Tags padrao"
  type        = map(string)
  default     = {}
}
