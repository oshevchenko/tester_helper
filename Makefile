.PHONY: run venv build utestpypi upypi clean veryclean test install freeze generated design design_settings

design build test utestpypi upypi freeze: generated
THIS_DIR = $(shell pwd)
VENV_PATH ?= $(THIS_DIR)/.venv
VENV_BIN_PATH = $(VENV_PATH)/bin
PROJECT_NAME = tester_helper
PROJECT_PATH = src/$(PROJECT_NAME)


ARGUMENTS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
FILENAME := $(word 1, $(ARGUMENTS))

%::
	@true

generated:
	@if [ ! -f "$(VENV_BIN_PATH)/python" ] || [ ! -f "$(VENV_BIN_PATH)/pip" ]; then \
		echo "Creating virtual environment at $(VENV_PATH)"; \
		python3 -m venv $(VENV_PATH); \
		$(VENV_BIN_PATH)/python -m pip install --upgrade pip; \
		$(VENV_BIN_PATH)/python -m pip install --upgrade build; \
		$(VENV_BIN_PATH)/python -m pip install --upgrade twine; \
	else \
		echo "Virtual environment already exists at $(VENV_PATH)"; \
	fi
	@echo "Generating version.py"
	$(VENV_BIN_PATH)/python scripts/get_git_version.py -o $(PROJECT_PATH)/resources/version.py

run:
	$(VENV_BIN_PATH)/python -m tester_helper

build: clean
	$(VENV_BIN_PATH)/python -m build --wheel
	$(VENV_BIN_PATH)/python -m pip install -e .

install:
	$(VENV_BIN_PATH)/python -m pip install --force-reinstall --no-deps dist/*.whl

clean:
	@rm -rf dist
	@rm -rf $(PROJECT_PATH)/resources/ui_*.py
	@rm -rf $(PROJECT_PATH)/resources/resources_rc.py
	@rm -rf $(PROJECT_PATH)/resources/version.py

veryclean: clean
	@rm -rf $(VENV_PATH)

test:
	$(VENV_BIN_PATH)/python -m unittest discover -s tests

design:
	$(VENV_BIN_PATH)/pyside6-designer $(PROJECT_PATH)/resources/$(FILENAME).ui > /dev/null 2>&1 &

design_main:
	$(VENV_BIN_PATH)/pyside6-designer $(PROJECT_PATH)/resources/MainWindow.ui > /dev/null 2>&1 &

utestpypi:
	$(VENV_BIN_PATH)/python -m twine upload --repository testpypi dist/* --verbose

upypi:
	$(VENV_BIN_PATH)/python -m twine upload dist/*
