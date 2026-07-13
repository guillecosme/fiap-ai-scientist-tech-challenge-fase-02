locals {
  src_dir  = "${path.module}/../../../../src"
  jobs_dir = "${path.module}/../../../../jobs"

  # Argumentos comuns a todos os jobs Glue. As variaveis de configuracao chegam
  # como argumentos do job e sao exportadas para o ambiente pela ponte do Glue.
  common_job_args = {
    "--extra-py-files"  = "s3://${aws_s3_bucket.artifacts.id}/code/src.zip"
    "--STORAGE_BACKEND" = "s3"
    "--BRONZE_BUCKET"   = var.bronze_bucket
    "--SILVER_BUCKET"   = var.silver_bucket
    "--GOLD_BUCKET"     = var.gold_bucket
    "--AWS_REGION"      = var.region
    "--job-language"    = "python"
  }

  stages = {
    ingestao  = "batch_ingest_job.py"
    silver    = "silver_job.py"
    gold      = "gold_job.py"
    qualidade = "quality_job.py"
  }
}

# Bucket de artefatos: guarda o codigo empacotado (zip do pacote e scripts dos
# jobs) que o Glue executa.
resource "aws_s3_bucket" "artifacts" {
  bucket        = "${var.project}-artifacts-${var.environment}-${var.bucket_suffix}"
  force_destroy = var.force_destroy
  tags          = var.tags
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "archive_file" "src" {
  type        = "zip"
  source_dir  = local.src_dir
  output_path = "${path.module}/build/src.zip"
}

resource "aws_s3_object" "src" {
  bucket = aws_s3_bucket.artifacts.id
  key    = "code/src.zip"
  source = data.archive_file.src.output_path
  etag   = data.archive_file.src.output_md5
}

resource "aws_s3_object" "job_script" {
  for_each = local.stages

  bucket = aws_s3_bucket.artifacts.id
  key    = "code/${each.value}"
  source = "${local.jobs_dir}/${each.value}"
  etag   = filemd5("${local.jobs_dir}/${each.value}")
}

resource "aws_glue_job" "stage" {
  for_each = local.stages

  name         = "${var.project}-${each.key}-${var.environment}"
  role_arn     = var.pipeline_role_arn
  glue_version = "4.0"

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.artifacts.id}/${aws_s3_object.job_script[each.key].key}"
    python_version  = "3"
  }

  default_arguments = local.common_job_args
  number_of_workers = 2
  worker_type       = "G.1X"

  tags = var.tags
}

# Role da Step Functions: pode disparar e acompanhar os jobs Glue.
data "aws_iam_policy_document" "sfn_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sfn" {
  name               = "${var.project}-sfn-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.sfn_assume.json
  tags               = var.tags
}

data "aws_iam_policy_document" "sfn_policy" {
  statement {
    actions   = ["glue:StartJobRun", "glue:GetJobRun", "glue:GetJobRuns", "glue:BatchStopJobRun"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "sfn_policy" {
  name   = "${var.project}-sfn-glue-${var.environment}"
  role   = aws_iam_role.sfn.id
  policy = data.aws_iam_policy_document.sfn_policy.json
}

# Fluxo: ingestao -> silver -> gold -> gate de qualidade, com retry e captura de
# erro levando a um estado de falha explicito.
resource "aws_sfn_state_machine" "pipeline" {
  name     = "${var.project}-pipeline-${var.environment}"
  role_arn = aws_iam_role.sfn.arn

  definition = jsonencode({
    Comment = "Pipeline medalhao de alfabetizacao"
    StartAt = "Ingestao"
    States = {
      Ingestao = {
        Type       = "Task"
        Resource   = "arn:aws:states:::glue:startJobRun.sync"
        Parameters = { JobName = aws_glue_job.stage["ingestao"].name }
        Retry      = [{ ErrorEquals = ["States.ALL"], IntervalSeconds = 30, MaxAttempts = 2, BackoffRate = 2 }]
        Catch      = [{ ErrorEquals = ["States.ALL"], Next = "Falhou" }]
        Next       = "Silver"
      }
      Silver = {
        Type       = "Task"
        Resource   = "arn:aws:states:::glue:startJobRun.sync"
        Parameters = { JobName = aws_glue_job.stage["silver"].name }
        Retry      = [{ ErrorEquals = ["States.ALL"], IntervalSeconds = 30, MaxAttempts = 2, BackoffRate = 2 }]
        Catch      = [{ ErrorEquals = ["States.ALL"], Next = "Falhou" }]
        Next       = "Gold"
      }
      Gold = {
        Type       = "Task"
        Resource   = "arn:aws:states:::glue:startJobRun.sync"
        Parameters = { JobName = aws_glue_job.stage["gold"].name }
        Retry      = [{ ErrorEquals = ["States.ALL"], IntervalSeconds = 30, MaxAttempts = 2, BackoffRate = 2 }]
        Catch      = [{ ErrorEquals = ["States.ALL"], Next = "Falhou" }]
        Next       = "Qualidade"
      }
      Qualidade = {
        Type       = "Task"
        Resource   = "arn:aws:states:::glue:startJobRun.sync"
        Parameters = { JobName = aws_glue_job.stage["qualidade"].name }
        Catch      = [{ ErrorEquals = ["States.ALL"], Next = "Falhou" }]
        Next       = "Concluido"
      }
      Concluido = { Type = "Succeed" }
      Falhou    = { Type = "Fail", Error = "PipelineFalhou", Cause = "Uma etapa da pipeline falhou" }
    }
  })

  tags = var.tags
}

# EventBridge dispara a pipeline batch na agenda definida.
data "aws_iam_policy_document" "events_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "events" {
  name               = "${var.project}-events-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.events_assume.json
  tags               = var.tags
}

data "aws_iam_policy_document" "events_policy" {
  statement {
    actions   = ["states:StartExecution"]
    resources = [aws_sfn_state_machine.pipeline.arn]
  }
}

resource "aws_iam_role_policy" "events_policy" {
  name   = "${var.project}-events-sfn-${var.environment}"
  role   = aws_iam_role.events.id
  policy = data.aws_iam_policy_document.events_policy.json
}

resource "aws_cloudwatch_event_rule" "schedule" {
  name                = "${var.project}-pipeline-schedule-${var.environment}"
  schedule_expression = var.schedule_expression
  tags                = var.tags
}

resource "aws_cloudwatch_event_target" "schedule" {
  rule     = aws_cloudwatch_event_rule.schedule.name
  arn      = aws_sfn_state_machine.pipeline.arn
  role_arn = aws_iam_role.events.arn
}
