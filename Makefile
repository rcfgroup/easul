.PHONY: venv build upload upload_test

PYTHON ?= python3
TWINE ?= twine

venv:
	$(PYTHON) -m venv venv

serve_docs:
	mkdocs serve -a localhost:3000

build_docs:
	mkdocs build

deploy_docs:
	mkdocs gh-deploy


build:
	rm -rf dist
	$(PYTHON) setup.py sdist bdist_wheel

# Credentials: TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-... (or ~/.pypirc)
upload:
	$(TWINE) check dist/*
	$(TWINE) upload dist/*

upload_test:
	$(TWINE) check dist/*
	$(TWINE) upload --repository-url https://test.pypi.org/legacy/ dist/*
