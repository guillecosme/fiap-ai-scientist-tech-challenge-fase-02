output "role_arn" {
  description = "ARN da role usada pela pipeline"
  value       = aws_iam_role.pipeline.arn
}

output "role_name" {
  description = "Nome da role usada pela pipeline"
  value       = aws_iam_role.pipeline.name
}
