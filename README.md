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

## Development Setup

### Requirements

*  [docker](https://www.docker.com/community-edition#/download)
*  [docker-compose](https://docs.docker.com/compose/install/)

### Setup

1. Build:

```
$ docker-compose build
```

2. Migrate

```
$ docker-compose exec app python manage.py migrate
```

3. Run

```
$ docker-compose up -d
```

4 Open the web app using http://localhost:8000

## Developers

This repository is maintained by [Philippine Cubers Association](https://facebook.com/PhilippineCubersAssociation/)
