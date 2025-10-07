.PHONY: setup install test run clean shell

# Detect if using pyenv or venv
PYTHON := python3
VENV_DIR := venv
PYENV_VENV := psl-env

# Setup virtual environment
setup:
	@if command -v pyenv > /dev/null 2>&1; then \
		echo "Creating pyenv virtual environment..."; \
		pyenv virtualenv 3.13.0 $(PYENV_VENV) || true; \
		pyenv local $(PYENV_VENV); \
	else \
		echo "Creating standard virtual environment..."; \
		$(PYTHON) -m venv $(VENV_DIR); \
	fi

# Install dependencies
install:
	pip install --upgrade pip
	pip install -r requirements.txt

# Run tests
test:
	@if command -v pyenv > /dev/null 2>&1; then \
		if ! pyenv version-name | grep -q $(PYENV_VENV); then \
			echo "⚠️  Warning: $(PYENV_VENV) is not activated!"; \
			echo "Run: pyenv activate $(PYENV_VENV)"; \
			echo "  OR: pyenv local $(PYENV_VENV)"; \
			exit 1; \
		fi; \
	fi
	pytest tests/ -v

# Run server
run:
	python main.py

# Run tests with coverage
test-coverage:
	pytest tests/ --cov=psl --cov-report=html --cov-report=term

# Clean up
clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Start a shell with the virtual environment activated
shell:
	@if command -v pyenv > /dev/null 2>&1 && pyenv versions | grep -q $(PYENV_VENV); then \
		echo "Starting shell with pyenv environment $(PYENV_VENV)..."; \
		pyenv activate $(PYENV_VENV) && exec $$SHELL; \
	elif [ -d "$(VENV_DIR)" ]; then \
		echo "Starting shell with venv..."; \
		. $(VENV_DIR)/bin/activate && exec $$SHELL; \
	else \
		echo "No virtual environment found. Run 'make setup' first."; \
	fi

# Full setup (create venv + install deps)
init: setup install
	@echo "Setup complete! Activate the environment:"
	@if command -v pyenv > /dev/null 2>&1; then \
		echo "  pyenv activate $(PYENV_VENV)"; \
		echo "  OR: pyenv local $(PYENV_VENV)"; \
	else \
		echo "  source $(VENV_DIR)/bin/activate"; \
	fi
