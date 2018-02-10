build:
	docker-compose build

run:
	docker-compose up -d

stop:
	docker-compose stop

logs:
	docker-compose logs -f --tail 250 app

migrations:
	docker-compose exec app python manage.py makemigrations

migrate:
	docker-compose exec app python manage.py migrate

shell:
	docker-compose exec app python manage.py shell

superuser:
	docker-compose exec app python manage.py createsuperuser
