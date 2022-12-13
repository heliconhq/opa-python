apidoc:
	poetry run sphinx-apidoc opa -o docs/source

docdeps:
	poetry export --without-hashes --format=requirements.txt > docs/requirements.txt

docs: docdeps apidoc
	poetry run sphinx-build -b html docs/source/ docs/build/html

test:
	poetry run pytest


