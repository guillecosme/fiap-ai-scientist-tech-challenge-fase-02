variable "project" {
  description = "Prefixo do projeto"
  type        = string
}

variable "environment" {
  description = "Ambiente (dev, prod, etc.)"
  type        = string
}

variable "region" {
  description = "Regiao AWS"
  type        = string
}

variable "bucket_suffix" {
  description = "Sufixo aleatorio, reaproveitado no bucket de artefatos"
  type        = string
}

variable "bronze_bucket" {
  type = string
}

variable "silver_bucket" {
  type = string
}

variable "gold_bucket" {
  type = string
}

variable "pipeline_role_arn" {
  description = "ARN da role usada pelos jobs do Glue"
  type        = string
}

variable "schedule_expression" {
  description = "Agenda da pipeline batch no EventBridge"
  type        = string
  default     = "rate(1 day)"
}

variable "tags" {
  type    = map(string)
  default = {}
}
