locals {
  default_tags = merge({
    project     = var.project
    environment = var.environment
    managed_by  = "terraform"
    domain      = "educacao-alfabetizacao"
  }, var.extra_tags)
}

# Provider apontado para o LocalStack: credenciais ficticias, validacoes
# desligadas e endpoints locais. So os servicos usados neste root sao mapeados.
provider "aws" {
  region                      = var.region
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_region_validation      = true
  s3_use_path_style           = true

  default_tags {
    tags = local.default_tags
  }

  endpoints {
    s3         = var.localstack_endpoint
    iam        = var.localstack_endpoint
    sts        = var.localstack_endpoint
    kinesis    = var.localstack_endpoint
    lambda     = var.localstack_endpoint
    cloudwatch = var.localstack_endpoint
    events     = var.localstack_endpoint
    sns        = var.localstack_endpoint
  }
}
