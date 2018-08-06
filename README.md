Philippine Cubers Association
===
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Build Status](https://travis-ci.org/pca/web-backend.svg?branch=master)](https://travis-ci.org/pca/web-backend)
[![Maintainability](https://api.codeclimate.com/v1/badges/7a8887688397d1cbcd06/maintainability)](https://codeclimate.com/github/pca/web-backend/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/7a8887688397d1cbcd06/test_coverage)](https://codeclimate.com/github/pca/web-backend/test_coverage)

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

### Config Setup

1. Setup configuration depending on the environment you're in. Make a copy of `development.yml` and `development.env` in `compose` and `envs` directory and rename it (e.g. `production.yml` and `production.env` for production setup). Modify the config files depending on your needs. Set COMPOSE_FILE environment variable to the compose file you are working on so that `Makefile` can load it.

    ```
    $ export COMPOSE_FILE=production.yml
    ```

2. Build the containers.

    ```
    $ make build
    ```

3. Run the containers.

    ```
    $ make run
    ```

### Database Setup

1. Run migrations for the default database.

    ```
    $ make migrate
    ```

2. Load database_config fixtures (contains the default config for the WCA databases).

    ```
    $ make dbconfig
    ```

3. TODO: Initial importing of WCA database.

## Developers

This repository is maintained by [Philippine Cubers Association](https://facebook.com/PhilippineCubersAssociation/)
