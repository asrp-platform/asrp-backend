# RSAPA Backend


## Setup local development environment

In the `local.yml` env-variables are set up so the project runs out of docker container.
For deployment is needed to set up the list of env-variables below:

- DB_HOST=rsapa_database
- BACKEND_DOMAIN=${app_domain}
- BACKEND_PORT=${app_port}

### Start and build containers

```shell
docker compose -f ./local.yml --build -d
```

For deployment the `HOST` environment variable should match the database service name ызусшашув шт `local.yml`.
For local development set `HOST` to `localhost`.


## Naming

### Branch naming

There are four name options for branches due to the GitFlow development:
1. `feature` - for features
2. `release`
3. `hotfix`
4. `bugfix`

### Commits naming

We use [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) to name our commits using the following special words:

- feat: (msg) - for new features
- fix: (msg) - for fixing bugs
- BREAKING CHANGE: (msg) - for
- ci: (msg)


## Main services


### App

Root URL of api must start with `api/` prefix. For example:

```
http://localhost:8000/api/users/1
```

### Database


### Media files storage

the storage is accessible via `MEDIA_PATH_NAME/file_name`. For example:

```
http://localhost:8000/api/media/photo.jpeg
```
