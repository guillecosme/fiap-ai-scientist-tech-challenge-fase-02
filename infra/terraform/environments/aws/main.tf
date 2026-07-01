# Sufixo aleatorio que torna os nomes de bucket unicos sem amarrar o codigo a
# nenhuma conta especifica. E o que permite subir o ambiente do zero em qualquer
# conta AWS (a sua ou a do avaliador) sem ajustes manuais.
resource "random_id" "suffix" {
  byte_length = 4
}

module "storage" {
  source = "../../modules/medallion_storage"

  project       = var.project
  environment   = var.environment
  bucket_suffix = random_id.suffix.hex
  force_destroy = var.force_destroy
  tags          = local.default_tags
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
  use_localstack      = var.use_localstack
  localstack_endpoint = local.localstack_endpoint
  tags                = local.default_tags
}

module "analytics" {
  source = "../../modules/analytics"

  project       = var.project
  environment   = var.environment
  gold_bucket   = module.storage.bucket_names["gold"]
  gold_database = module.storage.glue_databases["gold"]
  role_arn      = module.iam.role_arn
  tags          = local.default_tags
}

module "orchestration" {
  source = "../../modules/orchestration"

  project           = var.project
  environment       = var.environment
  region            = var.region
  bucket_suffix     = random_id.suffix.hex
  bronze_bucket     = module.storage.bucket_names["bronze"]
  silver_bucket     = module.storage.bucket_names["silver"]
  gold_bucket       = module.storage.bucket_names["gold"]
  pipeline_role_arn = module.iam.role_arn
  force_destroy     = var.force_destroy
  tags              = local.default_tags
}

module "monitoring" {
  source = "../../modules/monitoring"

  project                = var.project
  environment            = var.environment
  region                 = var.region
  state_machine_arn      = module.orchestration.state_machine_arn
  consumer_function_name = module.streaming.consumer_function_name
  alert_email            = var.alert_email
  tags                   = local.default_tags
}
