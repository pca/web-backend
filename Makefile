COMPOSE_FILE?=docker-compose.yml

build:
	docker-compose -f ${COMPOSE_FILE} build

run:
	docker-compose -f ${COMPOSE_FILE} up -d

stop:
	docker-compose -f ${COMPOSE_FILE} stop

rm:
	docker-compose -f ${COMPOSE_FILE} rm -f

logs:
	docker-compose -f ${COMPOSE_FILE} logs -f --tail 250 app app_worker

migrations:
	docker-compose -f ${COMPOSE_FILE} exec app python manage.py makemigrations

migrate:
	docker-compose -f ${COMPOSE_FILE} exec app python manage.py migrate

shell:
	docker-compose -f ${COMPOSE_FILE} exec app python manage.py shell

superuser:
	docker-compose -f ${COMPOSE_FILE} exec app python manage.py createsuperuser

testsentry:
	docker-compose -f ${COMPOSE_FILE} exec app python manage.py raven test
