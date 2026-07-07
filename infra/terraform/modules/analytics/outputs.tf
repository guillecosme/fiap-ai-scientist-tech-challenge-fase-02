output "crawler_name" {
  description = "Nome do crawler da camada Gold"
  value       = aws_glue_crawler.gold.name
}

output "athena_workgroup" {
  description = "Nome do workgroup do Athena"
  value       = aws_athena_workgroup.gold.name
}
