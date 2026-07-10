variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "region" {
  type = string
}

variable "state_machine_arn" {
  description = "ARN da state machine, para alarmar em falhas de execucao"
  type        = string
}

variable "consumer_function_name" {
  description = "Nome da Lambda consumidora, para alarmar em erros"
  type        = string
}

variable "alert_email" {
  description = "E-mail opcional para receber os alertas. Vazio nao cria assinatura."
  type        = string
  default     = ""
}

variable "metrics_namespace" {
  description = "Namespace das metricas custom da pipeline"
  type        = string
  default     = "Alfabetizacao/Pipeline"
}

variable "tags" {
  type    = map(string)
  default = {}
}
