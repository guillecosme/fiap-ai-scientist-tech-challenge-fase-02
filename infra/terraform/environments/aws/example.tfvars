# Copie para terraform.tfvars e ajuste conforme a conta.
# Este root provisiona a arquitetura completa (Glue, Step Functions, Athena, etc.)
# em uma conta AWS real.

project     = "alfabetizacao"
environment = "dev"
region      = "us-east-1"

# Permite destruir os buckets mesmo com objetos. Conveniente em ambiente de teste,
# para que terraform destroy nao trave em bucket nao vazio. Em producao, deixe false.
force_destroy = true

# E-mail opcional para receber os alertas de monitoramento (confirme a inscricao no email).
# alert_email = "voce@exemplo.com"

extra_tags = {
  owner = "time-engenharia-dados"
}
