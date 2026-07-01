output "bucket_names" {
  description = "Nome dos buckets por camada"
  value       = { for layer, bucket in aws_s3_bucket.layer : layer => bucket.id }
}

output "bucket_arns" {
  description = "ARN dos buckets por camada"
  value       = { for layer, bucket in aws_s3_bucket.layer : layer => bucket.arn }
}

output "glue_databases" {
  description = "Nome dos databases do Glue Data Catalog por camada"
  value       = { for layer, db in aws_glue_catalog_database.layer : layer => db.name }
}
