locals {
  # As tres camadas da arquitetura medalhao. Cada uma vira um bucket S3 e um
  # database no Glue Data Catalog.
  layers = ["bronze", "silver", "gold"]

  bucket_names = {
    for layer in local.layers :
    layer => "${var.project}-${layer}-${var.environment}-${var.bucket_suffix}"
  }
}

resource "aws_s3_bucket" "layer" {
  for_each = toset(local.layers)

  bucket = local.bucket_names[each.key]
  tags   = merge(var.tags, { layer = each.key })
}

# Versionamento ligado em todas as camadas. No Bronze e essencial para preservar
# o historico completo dos dados brutos ingeridos, requisito da arquitetura.
resource "aws_s3_bucket_versioning" "layer" {
  for_each = aws_s3_bucket.layer

  bucket = each.value.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "layer" {
  for_each = aws_s3_bucket.layer

  bucket = each.value.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "layer" {
  for_each = aws_s3_bucket.layer

  bucket                  = each.value.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_glue_catalog_database" "layer" {
  for_each = toset(local.layers)

  name        = "${var.project}_${each.key}_${var.environment}"
  description = "Camada ${each.key} do data lake de alfabetizacao"
}
