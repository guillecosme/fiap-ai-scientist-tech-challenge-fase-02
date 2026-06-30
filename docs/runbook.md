# Runbook de execução

Passo a passo para rodar a pipeline localmente (LocalStack) e provisioná-la na AWS de forma agnóstica à conta. Detalhado conforme a infraestrutura e os jobs são implementados.

## Execução local (custo zero)

Pré-requisitos: Docker, uv.

```bash
make setup
make up
```

## Provisionamento na AWS

Pré-requisitos: Terraform, credenciais AWS configuradas.

```bash
make deploy
# ...
make destroy
```

O objetivo é que qualquer conta AWS consiga subir e destruir o ambiente sem ajustes manuais. Os detalhes de variáveis e ordem de execução entram aqui.
