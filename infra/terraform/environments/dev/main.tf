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
  tags          = local.default_tags
}

module "iam" {
  source = "../../modules/iam"

  project     = var.project
  environment = var.environment
  bucket_arns = module.storage.bucket_arns
  tags        = local.default_tags
}
