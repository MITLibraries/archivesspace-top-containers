
### Dependency commands ###

install: ## Install dependencies
	pipenv install --dev

update: install ## Update all Python dependencies
	pipenv clean
	pipenv update --dev

### Test commands ###

test: ## Run tests and print a coverage report
	pipenv run coverage run --source=top_containers -m pytest -vv
	pipenv run coverage report -m

coveralls: test
	pipenv run coverage lcov -o ./coverage/lcov.info

### Code quality and safety commands ###

lint: bandit black mypy pylama safety ## Run linting, code quality, and safety checks

bandit:
	pipenv run bandit -r top_containers

black:
	pipenv run black --check --diff top_containers

mypy:
	pipenv run mypy top_containers

pylama:
	pipenv run pylama --options setup.cfg

safety:
	pipenv check
	pipenv verify
