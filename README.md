Philippine Cubers Association API
===
[![Test](https://github.com/pca/web-backend/actions/workflows/main.yml/badge.svg?branch=master)](https://github.com/pca/web-backend/actions?query=branch%3Amaster)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

API that powers [pinoycubers.org](https://pinoycubers.org/). Built with Django and <3.

## WCA Data

All official competition results and data are owned by [the WCA (World Cube Assocation)](https://www.worldcubeassociation.org)
published at [https://www.worldcubeassociation.org/results/](https://www.worldcubeassociation.org/results/).

## Setup

### Requirements

*  [docker](https://www.docker.com/community-edition#/download)
*  [docker-compose](https://docs.docker.com/compose/install/)

### Development Setup

1. Make a `.env` file from `.env.example`

    ```
    $ cp .env.example .env
    ```

2. Build and run the containers.

    ```
    $ docker-compose build
    $ docker-compose up -d
    ```

### Database Setup

1. Run database migrations.

    ```
    $ docker-compose run --rm pca-api migrate
    ```

2. Import WCA database.

    ```
    $ docker-compose run --rm pca-api syncwca
    ```

3. Create a superuser.

    ```
    $ docker-compose run --rm pca-api createsuperuser
    ```

## Developers

This repository is maintained by [Philippine Cubers Association](https://facebook.com/PhilippineCubersAssociation/)
