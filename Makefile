.PHONY: test
test:
	docker-compose up --exit-code-from testrunner
