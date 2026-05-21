.DEFAULT_GOAL := help

.PHONY: help install run test lint format

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Crea el entorno virtual e instala todas las dependencias (incluye dev)
	uv sync --group dev

run: ## Inicia el servidor de desarrollo
	uv run python run.py

test: ## Ejecuta los tests
	uv run pytest

lint: ## Verifica el estilo del código
	uv run ruff check app tests

format: ## Formatea el código
	uv run ruff format app tests
