locals {
  localstack_endpoint = "http://localhost:4566"

  default_tags = merge({
    project     = var.project
    environment = var.environment
    managed_by  = "terraform"
    domain      = "educacao-alfabetizacao"
  }, var.extra_tags)
}

provider "aws" {
  region = var.region

  default_tags {
    tags = local.default_tags
  }

  # Ajustes para execucao local contra o LocalStack. Em conta AWS real, basta
  # deixar use_localstack como false (padrao) e configurar as credenciais.
  access_key                  = var.use_localstack ? "test" : null
  secret_key                  = var.use_localstack ? "test" : null
  skip_credentials_validation = var.use_localstack
  skip_metadata_api_check     = var.use_localstack
  skip_region_validation      = var.use_localstack
  s3_use_path_style           = var.use_localstack

  dynamic "endpoints" {
    for_each = var.use_localstack ? [1] : []
    content {
      s3             = local.localstack_endpoint
      glue           = local.localstack_endpoint
      iam            = local.localstack_endpoint
      sts            = local.localstack_endpoint
      kinesis        = local.localstack_endpoint
      lambda         = local.localstack_endpoint
      stepfunctions  = local.localstack_endpoint
      cloudwatch     = local.localstack_endpoint
      cloudwatchlogs = local.localstack_endpoint
      events         = local.localstack_endpoint
      sns            = local.localstack_endpoint
    }
  }
}
