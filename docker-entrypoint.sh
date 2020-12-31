#!/usr/bin/env sh
set -e

if [ "$1" = "migrate" ]
then
    python manage.py migrate
    exit 0
fi

if [ "$1" = "makemigrations" ]
then
    python manage.py makemigrations
    exit 0
fi

if [ "$1" = "runserver" ]
then
    python manage.py runserver 0.0.0.0:8000
    exit 0
fi

if [ "$1" = "runserver" ]
then
    python manage.py runserver 0.0.0.0:8000
    exit 0
fi

if [ "$1" = "syncwca" ]
then
    sh /app/sync_wca_database.sh
    exit 0
fi

gunicorn -k gevent -w 4 config.wsgi -b 0.0.0.0:8000 --access-logfile - --error-logfile - --reload
