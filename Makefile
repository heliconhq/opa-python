apidoc:
	poetry run sphinx-apidoc opa -o docs/source

docs: apidoc
	poetry run sphinx-build -b html docs/source/ docs/build/html
