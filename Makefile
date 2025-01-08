run:
	docker-compose up

build:
	docker-compose up --build

stop:
	docker stop FINANCE_CORE_SERVER
	docker stop FINANCE_CORE_DB
	docker stop FINANCE_CORE_CELERY_BEAT
	docker stop FINANCE_CORE_CELERY
	docker stop FINANCE_CORE_REDIS

server-up:
	docker start FINANCE_CORE_SERVER

server-down:
	docker stop FINANCE_CORE_SERVER

db-up:
	docker start FINANCE_CORE_DB

db-down:
	docker stop FINANCE_CORE_DB

server-shell:
	docker exec -it FINANCE_CORE_SERVER /bin/bash

db-shell:
	docker exec -it FINANCE_CORE_DB /bin/bash

test: db-up server-up
	docker exec -it FINANCE_CORE_SERVER pytest --cov-fail-under=99
	docker stop FINANCE_CORE_SERVER
	docker stop FINANCE_CORE_DB

lint:
	docker exec -it FINANCE_CORE_SERVER isort .
	docker exec -it FINANCE_CORE_SERVER black .
	docker exec -it FINANCE_CORE_SERVER flake8 --exit-zero

all: test lint
