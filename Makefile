.PHONY: static

docker_compose_path = "docker-compose.dev.yml"

DC = docker-compose -f $(docker_compose_path)
DC_RUN = $(DC) run --rm
DC_RUN_MNG = $(DC_RUN) diplom python manage.py
MANAGER = poetry

###################################################################################################
## Build/run/stop/etc. ############################################################################

createsuperuser:
	$(DC_RUN_MNG) createsuperuser

static:
	$(DC_RUN_MNG) collectstatic --no-input

build:
	$(DC) build --no-cache
	make static

up:
	$(DC) up -d --build

down:
	$(DC) down

down-v:
	$(DC) down -v

down-v-rmi:
	$(DC) down -v --rmi local

restart:
	$(DC) restart

logs:
	$(DC) logs -f

###################################################################################################
## Databases ######################################################################################

migrations: # produce migrations from code
	$(DC_RUN_MNG) makemigrations

migrate: # apply db migrations
	$(DC_RUN_MNG) migrate

###################################################################################################
## Testing ########################################################################################

# Run tests locally. All pytest args can be specified using `pytest-args`:
# $ make tests pytest-args='-k test_name'  # Run specific test.
# $ make tests pytest-args='--ff -x'  # Run all tests. Stop if any fail. Rerun last failed if any.

test:
	@echo 'Running tests with arguments: '$(pytest-args)
	$(DC_RUN) django $(MANAGER) run pytest --ds=settings.test -v $(pytest-args) .

test-coverage:
	@echo 'Running test coverage with arguments: '$(pytest-args)
	$(DC_RUN) django pytest --ds=settings.test --cov=. --cov-report=term-missing --cov-config=../pyproject.toml -c ../pyproject.toml .

###################################################################################################
## Code tools #####################################################################################

install-pre-commit:
	$(MANAGER) run pre-commit install

check:
	$(MANAGER) run ruff check app

format:
	$(MANAGER) run ruff check --fix .

lint:
	make check
	@# For some reason, mypy and pylint fails to resolve PYTHONPATH, set manually.
	PYTHONPATH=./app $(MANAGER) run pylint app
	PYTHONPATH=./app $(MANAGER) run mypy --namespace-packages --show-error-codes app --check-untyped-defs --ignore-missing-imports --show-traceback
