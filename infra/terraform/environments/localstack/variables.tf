variable "project" {
  description = "Prefixo do projeto usado na nomeacao dos recursos"
  type        = string
  default     = "alfabetizacao"
}

variable "environment" {
  description = "Nome do ambiente"
  type        = string
  default     = "local"
}

variable "region" {
  description = "Regiao AWS (o LocalStack aceita qualquer uma)"
  type        = string
  default     = "us-east-1"
}

variable "localstack_endpoint" {
  description = "Endpoint do LocalStack"
  type        = string
  default     = "http://localhost:4566"
}

variable "alert_email" {
  description = "E-mail opcional para os alertas (no LocalStack normalmente fica vazio)"
  type        = string
  default     = ""
}

variable "extra_tags" {
  description = "Tags adicionais"
  type        = map(string)
  default     = {}
}
