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
