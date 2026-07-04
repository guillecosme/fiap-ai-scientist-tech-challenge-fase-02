locals {
  consumer_source = "${path.module}/../../../../src/pipeline/ingestion/streaming_consumer.py"

  # O endpoint do LocalStack so e injetado na Lambda quando rodando local. Em
  # conta AWS real, a Lambda usa o endpoint padrao do servico.
  lambda_env = merge(
    {
      BRONZE_BUCKET    = var.bronze_bucket
      STREAMING_PREFIX = "alunos_streaming"
    },
    var.use_localstack ? { AWS_ENDPOINT_URL = var.localstack_endpoint } : {}
  )
}

# Stream em modo on-demand: escala sozinho com o volume e cobra por uso, sem
# precisar dimensionar shards manualmente. Decisao alinhada a FinOps.
resource "aws_kinesis_stream" "eventos" {
  name = "${var.project}-eventos-${var.environment}"

  stream_mode_details {
    stream_mode = "ON_DEMAND"
  }

  tags = var.tags
}

data "archive_file" "consumer" {
  type        = "zip"
  source_file = local.consumer_source
  output_path = "${path.module}/build/streaming_consumer.zip"
}

resource "aws_lambda_function" "consumer" {
  function_name    = "${var.project}-streaming-consumer-${var.environment}"
  role             = var.role_arn
  runtime          = "python3.12"
  handler          = "streaming_consumer.handler"
  filename         = data.archive_file.consumer.output_path
  source_code_hash = data.archive_file.consumer.output_base64sha256
  timeout          = 60

  environment {
    variables = local.lambda_env
  }

  tags = var.tags
}

resource "aws_lambda_event_source_mapping" "kinesis_to_lambda" {
  event_source_arn                   = aws_kinesis_stream.eventos.arn
  function_name                      = aws_lambda_function.consumer.arn
  starting_position                  = "LATEST"
  batch_size                         = 100
  maximum_batching_window_in_seconds = 10
}

# Permissao para a role ler o stream do Kinesis.
data "aws_iam_policy_document" "kinesis_read" {
  statement {
    actions = [
      "kinesis:GetRecords",
      "kinesis:GetShardIterator",
      "kinesis:DescribeStream",
      "kinesis:DescribeStreamSummary",
      "kinesis:ListShards",
    ]
    resources = [aws_kinesis_stream.eventos.arn]
  }
}

resource "aws_iam_role_policy" "kinesis_read" {
  name   = "${var.project}-kinesis-read-${var.environment}"
  role   = var.role_name
  policy = data.aws_iam_policy_document.kinesis_read.json
}
