variable "project" {
  description = "Prefixo do projeto usado na nomeacao dos recursos"
  type        = string
  default     = "alfabetizacao"
}

variable "environment" {
  description = "Nome do ambiente"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "Regiao AWS"
  type        = string
  default     = "us-east-1"
}

variable "use_localstack" {
  description = "Quando true, aponta os endpoints para o LocalStack e usa credenciais ficticias, permitindo rodar tudo localmente sem conta AWS"
  type        = bool
  default     = false
}

variable "extra_tags" {
  description = "Tags adicionais a serem mescladas com as tags padrao"
  type        = map(string)
  default     = {}
}
