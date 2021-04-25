FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update && apt-get install -y curl unzip

WORKDIR /app

COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY ./docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

EXPOSE 8000
CMD ["gunicorn", "-k", "gevent", "-w", "4", "config.wsgi", "-b", "0.0.0.0:8000", \
    "--access-logfile", "-", "--error-logfile", "-"]
