export LANG := C.UTF-8

VENV  	:= .venv
BUILD	:= build

.PHONY: tests

clean:
	@rm -rfv $(BUILD)

build:
	@mkdir -pv $(BUILD)

tests: build
	mkdir -p $(BUILD)/htmlcov
	source $(VENV)/bin/activate && pytest -v --cov=solidblue3 --cov-report=html:$(BUILD)/htmlcov tests