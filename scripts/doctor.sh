#!/usr/bin/env bash
# Checa os pre-requisitos por modo antes de rodar a pipeline.
# Uso: bash scripts/doctor.sh
set -uo pipefail

ok() { printf "  [ ok ] %s\n" "$1"; }
miss() { printf "  [falta] %s\n" "$1"; }

have() { command -v "$1" >/dev/null 2>&1; }

echo "Pre-requisitos comuns:"
have uv && ok "uv" || miss "uv (https://docs.astral.sh/uv/)"
have java && ok "java (necessario para o Spark local)" || miss "java 17 (Spark local)"

echo
echo "Modo local: precisa de uv e java."

echo
echo "Modo LocalStack:"
have docker && ok "docker" || miss "docker"
have terraform && ok "terraform" || miss "terraform"

echo
echo "Modo AWS real:"
have terraform && ok "terraform" || miss "terraform"
if have aws; then
  if aws sts get-caller-identity >/dev/null 2>&1; then
    ok "aws cli autenticada ($(aws configure get region 2>/dev/null || echo 'sem regiao'))"
  else
    miss "aws cli presente, mas sem credenciais validas (rode aws configure)"
  fi
else
  miss "aws cli (necessaria so para o modo AWS real)"
fi

echo
echo "Dica: copie .env.example para .env e escolha o modo antes de rodar."
