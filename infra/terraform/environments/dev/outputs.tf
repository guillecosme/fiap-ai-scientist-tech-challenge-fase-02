output "bucket_names" {
  description = "Nome dos buckets das camadas bronze, silver e gold"
  value       = module.storage.bucket_names
}

output "glue_databases" {
  description = "Databases do Glue Data Catalog por camada"
  value       = module.storage.glue_databases
}

output "pipeline_role_arn" {
  description = "ARN da role usada pelos jobs da pipeline"
  value       = module.iam.role_arn
}
