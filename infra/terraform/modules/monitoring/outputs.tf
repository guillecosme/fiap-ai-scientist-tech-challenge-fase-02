output "sns_topic_arn" {
  description = "ARN do topico de alertas"
  value       = aws_sns_topic.alertas.arn
}

output "dashboard_name" {
  description = "Nome do dashboard do CloudWatch"
  value       = aws_cloudwatch_dashboard.pipeline.dashboard_name
}
