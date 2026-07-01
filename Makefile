.PHONY: help setup lint test up down deploy plan destroy clean

help:
	@echo "Alvos disponiveis:"
	@echo "  setup    instala dependencias com uv"
	@echo "  lint     roda ruff (check + format --check)"
	@echo "  test     roda a suite de testes com pytest"
	@echo "  up       sobe o ambiente local (LocalStack + Spark) via docker compose"
	@echo "  down     derruba o ambiente local"
	@echo "  plan     terraform plan no ambiente dev"
	@echo "  deploy   terraform apply no ambiente dev"
	@echo "  destroy  terraform destroy no ambiente dev"
	@echo "  clean    limpa caches e dados locais das camadas"

setup:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .

test:
	uv run pytest -q

up:
	docker compose up -d

down:
	docker compose down -v

plan:
	cd infra/terraform/environments/dev && terraform init -input=false && terraform plan

deploy:
	cd infra/terraform/environments/dev && terraform init -input=false && terraform apply -auto-approve

destroy:
	cd infra/terraform/environments/dev && terraform destroy -auto-approve

clean:
	rm -rf .pytest_cache .ruff_cache
	find data -type f ! -name '.gitkeep' -delete
