SHELL := /bin/bash
PYTHON = python3
FLAKE8_EXCLUDE = venv,.venv,.eggs,.tox,.git,__pycache__,*.pyc

.PHONY: clean init init-dev test check build docs

clean:
	@find . -name '*.pyc' -exec rm --force {} +
	@find . -name '*.pyo' -exec rm --force {} +
	@find . -name '*~' -exec rm --force {} +
	@rm -rf build
	@rm -rf dist
	@rm -rf *.egg-info
	@rm -f *.sqlite
	@rm -rf .cache
	@rm -rf docs/_build

init:
	@pip install --upgrade pip
	@pip install -e .

init-dev: init
	@pip install -e .[dev]
	@mypy pyamplipi --install-types --non-interactive
test:
	@${PYTHON} -m pytest

check:
	@${PYTHON} -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude ${FLAKE8_EXCLUDE}
	@${PYTHON} -m flake8 . --count --exit-zero --max-complexity=10 --max-line-length=132 --statistics --exclude ${FLAKE8_EXCLUDE}
	@mypy pyamplipi --check-untyped-defs

build:
	@${PYTHON} setup.py build

docs:
	@cd docs && sphinx-apidoc -o . ../pyamplipi -f
	@$(MAKE) -C docs html
