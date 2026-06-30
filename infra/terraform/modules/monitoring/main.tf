# Topico de alertas. Quando um alarme dispara, publica aqui; a assinatura por
# e-mail e opcional.
resource "aws_sns_topic" "alertas" {
  name = "${var.project}-alertas-${var.environment}"
  tags = var.tags
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.alert_email == "" ? 0 : 1
  topic_arn = aws_sns_topic.alertas.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# Falha de execucao da pipeline (Step Functions).
resource "aws_cloudwatch_metric_alarm" "pipeline_falhou" {
  alarm_name          = "${var.project}-pipeline-falhou-${var.environment}"
  namespace           = "AWS/States"
  metric_name         = "ExecutionsFailed"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  dimensions          = { StateMachineArn = var.state_machine_arn }
  alarm_actions       = [aws_sns_topic.alertas.arn]
  alarm_description   = "Uma execucao da pipeline falhou"
  tags                = var.tags
}

# Erros na ingestao por streaming (Lambda consumidora).
resource "aws_cloudwatch_metric_alarm" "ingestao_streaming_erros" {
  alarm_name          = "${var.project}-streaming-erros-${var.environment}"
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  dimensions          = { FunctionName = var.consumer_function_name }
  alarm_actions       = [aws_sns_topic.alertas.arn]
  alarm_description   = "A Lambda de streaming registrou erros"
  tags                = var.tags
}

# Falha em alguma etapa, via metrica custom emitida pelos jobs.
resource "aws_cloudwatch_metric_alarm" "etapa_falhou" {
  alarm_name          = "${var.project}-etapa-falhou-${var.environment}"
  namespace           = var.metrics_namespace
  metric_name         = "StageFailure"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alertas.arn]
  alarm_description   = "Uma etapa da pipeline reportou falha"
  tags                = var.tags
}

# Painel reunindo latencia, volume e falhas das etapas.
resource "aws_cloudwatch_dashboard" "pipeline" {
  dashboard_name = "${var.project}-pipeline-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Latencia por etapa (s)"
          region = var.region
          view   = "timeSeries"
          metrics = [
            [var.metrics_namespace, "StageDurationSeconds", "stage", "ingestao"],
            [var.metrics_namespace, "StageDurationSeconds", "stage", "silver"],
            [var.metrics_namespace, "StageDurationSeconds", "stage", "gold"],
            [var.metrics_namespace, "StageDurationSeconds", "stage", "qualidade"],
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Volume ingerido por tabela"
          region = var.region
          view   = "timeSeries"
          stat   = "Sum"
          metrics = [
            [var.metrics_namespace, "RecordsIngested", "table", "uf"],
            [var.metrics_namespace, "RecordsIngested", "table", "municipio"],
            [var.metrics_namespace, "RecordsIngested", "table", "alunos"],
          ]
        }
      },
    ]
  })
}
