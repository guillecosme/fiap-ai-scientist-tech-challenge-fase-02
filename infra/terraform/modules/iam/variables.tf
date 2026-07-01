variable "project" {
  description = "Prefixo do projeto"
  type        = string
}

variable "environment" {
  description = "Ambiente (dev, prod, etc.)"
  type        = string
}

variable "bucket_arns" {
  description = "ARNs dos buckets das camadas, para escopar a politica de acesso"
  type        = map(string)
}

variable "tags" {
  description = "Tags padrao"
  type        = map(string)
  default     = {}
}
