# Crawler que varre a camada Gold e registra as tabelas no Glue Data Catalog,
# deixando os marts consultaveis pelo Athena sem precisar declarar schema na mao.
resource "aws_glue_crawler" "gold" {
  name          = "${var.project}-gold-crawler-${var.environment}"
  role          = var.role_arn
  database_name = var.gold_database

  s3_target {
    path = "s3://${var.gold_bucket}/"
  }

  # Agrupa arquivos compativeis numa mesma tabela, respeitando o particionamento.
  configuration = jsonencode({
    Version = 1.0
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
  })

  tags = var.tags
}

# Workgroup do Athena com o teto de bytes lidos por query. E uma trava de custo:
# consultas que varreriam dados demais sao barradas antes de gerar gasto.
resource "aws_athena_workgroup" "gold" {
  name = "${var.project}-${var.environment}"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true
    bytes_scanned_cutoff_per_query     = var.bytes_scanned_cutoff

    result_configuration {
      output_location = "s3://${var.gold_bucket}/_athena_results/"
    }
  }

  force_destroy = true
  tags          = var.tags
}
