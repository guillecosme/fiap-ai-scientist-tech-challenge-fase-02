locals {
  bucket_object_arns = [for arn in values(var.bucket_arns) : "${arn}/*"]
  bucket_root_arns   = values(var.bucket_arns)
}

# Role assumida pelos jobs de processamento (Glue) e pela ingestao. Mantida
# generica de proposito para servir tanto o Glue quanto execucoes locais.
data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com", "lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "pipeline" {
  name               = "${var.project}-pipeline-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.assume.json
  tags               = var.tags
}

# Acesso de leitura e escrita restrito apenas aos buckets das camadas.
data "aws_iam_policy_document" "s3_access" {
  statement {
    sid       = "ListLayerBuckets"
    actions   = ["s3:ListBucket", "s3:GetBucketLocation"]
    resources = local.bucket_root_arns
  }
  statement {
    sid       = "ReadWriteLayerObjects"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = local.bucket_object_arns
  }
}

resource "aws_iam_role_policy" "s3_access" {
  name   = "${var.project}-s3-access-${var.environment}"
  role   = aws_iam_role.pipeline.id
  policy = data.aws_iam_policy_document.s3_access.json
}

# Acesso ao catalogo do Glue e logs do CloudWatch, necessarios para os jobs.
data "aws_iam_policy_document" "catalog_and_logs" {
  statement {
    sid = "GlueCatalog"
    actions = [
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:GetTable",
      "glue:GetTables",
      "glue:CreateTable",
      "glue:UpdateTable",
      "glue:BatchCreatePartition",
      "glue:GetPartitions",
    ]
    resources = ["*"]
  }
  statement {
    sid = "CloudWatchLogs"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "catalog_and_logs" {
  name   = "${var.project}-catalog-logs-${var.environment}"
  role   = aws_iam_role.pipeline.id
  policy = data.aws_iam_policy_document.catalog_and_logs.json
}
