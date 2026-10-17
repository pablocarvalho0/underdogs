#!/usr/bin/env bash
set -e

# Executa a suite de testes oficial do projeto
if [ -d ".venv" ]; then
    .venv/bin/pytest "$@"
else
    pytest "$@"
fi
