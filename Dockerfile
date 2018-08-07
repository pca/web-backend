FROM python:3.6-alpine

RUN apk update
RUN apk add mysql-client curl

WORKDIR /app/src
ADD requirements.txt /app/src
RUN pip install -r requirements.txt
