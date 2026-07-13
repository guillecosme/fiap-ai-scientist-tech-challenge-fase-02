# Root do LocalStack. Provisiona apenas a faixa com paridade no LocalStack
# Community: storage, IAM, ingestao streaming (Kinesis + Lambda) e monitoramento.
# O processamento das camadas roda pelo Spark local apontando para o S3 do
# LocalStack, e a consulta analitica usa DuckDB. Glue, Athena e Step Functions
# ficam no root aws.

resource "random_id" "suffix" {
  byte_length = 4
}

module "storage" {
  source = "../../modules/medallion_storage"

  project             = var.project
  environment         = var.environment
  bucket_suffix       = random_id.suffix.hex
  force_destroy       = true
  enable_glue_catalog = false
  tags                = local.default_tags
}

module "iam" {
  source = "../../modules/iam"

  project     = var.project
  environment = var.environment
  bucket_arns = module.storage.bucket_arns
  tags        = local.default_tags
}

module "streaming" {
  source = "../../modules/streaming"

  project             = var.project
  environment         = var.environment
  bronze_bucket       = module.storage.bucket_names["bronze"]
  role_arn            = module.iam.role_arn
  role_name           = module.iam.role_name
  use_localstack      = true
  localstack_endpoint = var.localstack_endpoint
  tags                = local.default_tags
}

module "monitoring" {
  source = "../../modules/monitoring"

  project                = var.project
  environment            = var.environment
  region                 = var.region
  consumer_function_name = module.streaming.consumer_function_name
  enable_sfn_alarm       = false
  alert_email            = var.alert_email
  tags                   = local.default_tags
}
