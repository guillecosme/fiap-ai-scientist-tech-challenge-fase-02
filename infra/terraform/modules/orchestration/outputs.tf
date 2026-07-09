output "state_machine_arn" {
  description = "ARN da state machine da pipeline"
  value       = aws_sfn_state_machine.pipeline.arn
}

output "glue_job_names" {
  description = "Nome dos jobs Glue por etapa"
  value       = { for k, j in aws_glue_job.stage : k => j.name }
}

output "artifacts_bucket" {
  description = "Bucket de artefatos com o codigo dos jobs"
  value       = aws_s3_bucket.artifacts.id
}
