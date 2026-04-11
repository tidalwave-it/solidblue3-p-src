export LANG := C.UTF-8
VENV  := .venv

.PHONY: tests

tests:
	source $(VENV)/bin/activate && pytest -v --cov=solidblue3 --cov-report=html:$(BUILD)/htmlcov tests