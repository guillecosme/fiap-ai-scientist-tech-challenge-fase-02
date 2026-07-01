.PHONY: help doctor setup lint test clean \
        local \
        ls-up ls-down ls-deploy ls-run ls-destroy \
        aws-plan aws-deploy aws-run aws-destroy

AWS_ROOT = infra/terraform/environments/aws
LS_ROOT  = infra/terraform/environments/localstack

help:
	@echo "Qualidade e setup:"
	@echo "  doctor      checa pre-requisitos por modo"
	@echo "  setup       instala dependencias com uv"
	@echo "  lint        roda ruff"
	@echo "  test        roda a suite de testes"
	@echo "  clean       limpa caches e dados locais das camadas"
	@echo ""
	@echo "Modo local (filesystem, sem nuvem):"
	@echo "  local       roda a pipeline inteira em data/"
	@echo ""
	@echo "Modo LocalStack (AWS emulada, sem custo):"
	@echo "  ls-up       sobe LocalStack e Spark via docker compose"
	@echo "  ls-deploy   provisiona a infra no LocalStack e mostra o .env"
	@echo "  ls-run      roda a pipeline contra o LocalStack"
	@echo "  ls-destroy  esvazia buckets e destroi no LocalStack"
	@echo "  ls-down     derruba os containers"
	@echo ""
	@echo "Modo AWS real:"
	@echo "  aws-plan    terraform plan na conta AWS"
	@echo "  aws-deploy  terraform apply na conta AWS"
	@echo "  aws-run     dispara a pipeline (Step Functions)"
	@echo "  aws-destroy esvazia buckets e destroi na conta AWS"

doctor:
	bash scripts/doctor.sh

setup:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .

test:
	uv run pytest -q

clean:
	rm -rf .pytest_cache .ruff_cache
	find data -type f ! -name '.gitkeep' -delete

# ---- local -----------------------------------------------------------------
local:
	bash scripts/run_pipeline.sh local

# ---- localstack ------------------------------------------------------------
ls-up:
	docker compose up -d

ls-down:
	docker compose down -v

ls-deploy:
	bash scripts/bootstrap_localstack.sh

ls-run:
	bash scripts/run_pipeline.sh localstack

ls-destroy:
	bash scripts/teardown.sh localstack

# ---- aws -------------------------------------------------------------------
aws-plan:
	terraform -chdir=$(AWS_ROOT) init -input=false && terraform -chdir=$(AWS_ROOT) plan

aws-deploy:
	terraform -chdir=$(AWS_ROOT) init -input=false && terraform -chdir=$(AWS_ROOT) apply -auto-approve

aws-run:
	bash scripts/run_pipeline.sh aws

aws-destroy:
	bash scripts/teardown.sh aws
