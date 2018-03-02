FROM python:3.6-alpine

RUN apk update
RUN apk add mysql-client

WORKDIR /app
ADD requirements.txt /app
RUN pip install -r requirements.txt
