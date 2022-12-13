apidoc:
	poetry run sphinx-apidoc opa -o docs/source

docdeps:
	poetry export --without-hashes --format=requirements.txt > docs/requirements.txt

docs: docdeps
	poetry run sphinx-build -b html docs/source/ docs/build/html

test:
	poetry run pytest $(file)

clean:
	cd docs && make clean

server:
	docker run -it --rm -p 8181:8181 openpolicyagent/opa run --server --set=decision_logs.console=true --addr :8181
