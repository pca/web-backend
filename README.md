Philippine Cubers Association
===

This is the new PCA web repo written in python. You can checkout our old [PCA web project](https://github.com/geocine/pinoycubers) written in PHP.

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

### Setup

1. Setup configuration depending on the environment you're in. Make a copy of `docker-compose.yml` and `development.env` and rename it (e.g. `production.yml` and `production.env` for production setup). Modify the config files depending on your needs. Set COMPOSE_FILE environment variable to the compose file you are working on so that `Makefile` can load it.

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

3. Run migrations.

```
$ make migrate
```

## Developers

This repository is maintained by [Philippine Cubers Association](https://facebook.com/PhilippineCubersAssociation/)
