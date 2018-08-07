Philippine Cubers Association
===
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Build Status](https://travis-ci.org/pca/web-backend.svg?branch=master)](https://travis-ci.org/pca/web-backend)
[![Maintainability](https://api.codeclimate.com/v1/badges/7a8887688397d1cbcd06/maintainability)](https://codeclimate.com/github/pca/web-backend/maintainability)
[![Coverage Status](https://img.shields.io/coveralls/github/pca/web-backend/master.svg)](https://coveralls.io/github/pca/web-backend?branch=master)

This is the new PCA web repo written in python. Live test server: [https://www.pinoycubers.org/](https://www.pinoycubers.org/)

## Features

1. **WCA Login** - Link your WCA Account
2. **Compititions** - Updated list of upcoming competitions
3. **National Rankings** - View the national rankings
4. **Regional Rankings (Unofficial)** - View the regional rankings
5. **City/Provincial Rankings (Unofficial)** - View the city/provincial rankings

## WCA Data

All official competition records and data are owned by [the WCA (World Cube Assocation)](https://www.worldcubeassociation.org).
No official record has been tampered/modified.

## Setup

### Requirements

*  [docker](https://www.docker.com/community-edition#/download)
*  [docker-compose](https://docs.docker.com/compose/install/)

### Development Setup

1. Build and run the containers.

    ```
    $ docker-compose -f compose/development.yml build
    $ docker-compose -f compose/development.yml up -d
    ```

### Database Setup

1. Run migrations for the default database.

    ```
    $ docker-compose -f compose/development.yml exec api python manage.py migrate
    ```

2. Load database_config fixtures (contains the default config for the WCA databases).

    ```
    $ docker-compose -f compose/development.yml exec api python manage.py loaddata database_config
    ```

3. Import WCA database.

    ```
    $ docker-compose -f compose/staging.yml exec api sh /scripts/sync_wca_database
    ```

## Developers

This repository is maintained by [Philippine Cubers Association](https://facebook.com/PhilippineCubersAssociation/)
