Philippine Cubers Association
===
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

This is the new PCA web repo written in python. Live test server: [https://www.pinoycubers.org/](https://www.pinoycubers.org/)

## Features

1. **WCA Login** - Link your WCA Account
2. **Compititions** - Updated list of upcoming competitions
3. **National Rankings** - View the national rankings
4. **Regional Rankings (Unofficial)** - View the regional rankings

## WCA Data

All official competition records and data are owned by [the WCA (World Cube Assocation)](https://www.worldcubeassociation.org).
No official record has been tampered/modified.

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
    $ docker-compose exec pca-api python manage.py migrate
    ```

2. Import WCA database.

    ```
    $ docker-compose exec pca-api sh /app/sync_wca_database.sh
    ```

3. Create a superuser.

    ```
    $ docker-compose exec pca-api python manage.py createsuperuser
    ```

## Developers

This repository is maintained by [Philippine Cubers Association](https://facebook.com/PhilippineCubersAssociation/)
