output "bucket_names" {
  description = "Nome dos buckets das camadas no LocalStack"
  value       = module.storage.bucket_names
}

output "kinesis_stream_name" {
  description = "Nome do stream de eventos"
  value       = module.streaming.stream_name
}

output "alertas_sns_topic_arn" {
  description = "Topico SNS de alertas"
  value       = module.monitoring.sns_topic_arn
}
