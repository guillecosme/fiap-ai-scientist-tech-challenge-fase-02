output "stream_name" {
  description = "Nome do Kinesis Data Stream de eventos"
  value       = aws_kinesis_stream.eventos.name
}

output "stream_arn" {
  description = "ARN do stream"
  value       = aws_kinesis_stream.eventos.arn
}

output "consumer_function_name" {
  description = "Nome da Lambda consumidora"
  value       = aws_lambda_function.consumer.function_name
}
