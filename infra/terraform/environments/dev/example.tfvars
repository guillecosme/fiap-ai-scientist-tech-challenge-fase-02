# Copie para terraform.tfvars e ajuste conforme o ambiente.

project     = "alfabetizacao"
environment = "dev"
region      = "us-east-1"

# Deixe true para rodar localmente contra o LocalStack (sem custo e sem conta AWS).
# Em conta AWS real, deixe false e configure as credenciais (aws configure ou variaveis de ambiente).
use_localstack = false

extra_tags = {
  owner = "time-engenharia-dados"
}
