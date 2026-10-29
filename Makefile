.PHONY: venv build upload upload_test

venv:
	python3 -m venv venv

serve_docs:
	mkdocs serve -a localhost:3000

build_docs:
	mkdocs build

deploy_docs:
	mkdocs gh-deploy


build:
	rm -rf dist
	uv build

# Credentials: TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-... (or ~/.pypirc)
upload:
	uv tool run --from twine twine check dist/*
	uv tool run --from twine twine upload dist/*

upload_test:
	uv tool run --from twine twine check dist/*
	uv tool run --from twine twine upload --repository-url https://test.pypi.org/legacy/ dist/*


