.PHONY: install test lint inspect validate

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check .

inspect:
	thesisforge inspect examples/bachelor-thesis/thesis.md

validate:
	thesisforge validate examples/bachelor-thesis/thesis.md
