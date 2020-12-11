[![CircleCI](https://circleci.com/gh/18F/federalist-garden-build.svg?style=svg)](https://circleci.com/gh/18F/federalist-garden-build)
[![Maintainability](https://api.codeclimate.com/v1/badges/b7ddc95a6745610b685b/maintainability)](https://codeclimate.com/github/18F/federalist-garden-build/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/b7ddc95a6745610b685b/test_coverage)](https://codeclimate.com/github/18F/federalist-garden-build/test_coverage)

# Federalist Garden Build

Docker image for building and publishing static sites as part of the Federalist platform.

Generally, site builds work in three stages: clone, build, and publish. Each stage is broken down into a number of steps. First, the container checks out the site from GitHub. Then it builds the site with the specified build engine. Then it gzip compresses text files and sets cache control headers. Finally, it uploads the built site to S3, and also creates redirect objects for directories, such as `/path` => `/path/`.

## Usage
### Command
```
python main.py [options]
```

### Command options
One of the following flags *must* be specified:

| Flag | Example | Description |
| ---- | ------- | ----------- |
| `-p`, `--params` | `-p '{"foo": "bar"}'` | A JSON encoded string containing the [build arguments](#build-arguments) |
| `-f`, `--file` | `--file ./.local/my-build.json` | A path to a JSON file containing the [build arguments](#build-arguments) |

### Using cloud.gov tasks
```
cf run-task <APP_NAME> "cd app && python main.py [options]"
```

### Using `docker-compose`
```
docker-compose run --rm app python main.py [options]
```

### Full examples
```
# build arguments provided as a JSON encoded string

cf run-task federalist-build-container "python main.py -p '{\"foo\": \"bar\"}'" --name "build-123"
```

```
# build arguments provided in a JSON encoded file

docker-compose run --rm app python main.py -f /tmp/local/my-build.json
```

## Environment variables

| Name | Optional? | VCAP Service | Description |
| ---- | :-------: | ------------ | ----------- |
| `CACHE_CONTROL` | Y | | Default value to set for the `Cache-Control` header of all published files, default is `max-age=60` |
| `DATABASE_URL` | N | | The URL of the database for database logging |
| `USER_ENVIRONMENT_VARIABLE_KEY` | N |  `federalist-{space}-uev-key` | Encryption key to decrypt user environment variables |

When running locally, environment variables are configured in `docker-compose.yml` under the `app` service.

## Build arguments

| Name | Optional? | Default | Description |
| ---- | :-------: | ------- | ----------- |
| `aws_access_key_id` | N | | AWS access key for the destination S3 bucket |
| `aws_secret_access_key` | N | | AWS secret key for the destination S3 bucket |
| `aws_default_region` | N | | AWS region for the destination S3 bucket |
| `bucket` | N | | AWS S3 bucket name for the destination S3 bucket |
| `github_token` | Y | `None` | GitHub auth token for cloning the repository |
| `status_callback` | N | | The URL the container should use to report the status of the completed build (ie, success or failure) |
| `config` | Y | `None` | A yaml block of configuration to add to `_config.yml` before building. Currently only used in `jekyll` site builds |
| `generator` | N | | The engine to use to build the site (`'jekyll'`, `'hugo'`, `'node.js'`, or `'static'`) |
| `owner` | N | | The GitHub organization of the source repository |
| `repository` | N | | The name of source the repository |
| `branch` | N | | The branch of the source repository to build |
| `site_prefix` | N | | The S3 bucket "path" that the site files will be published to. It should **not** have a trailing or prefix slash (Ex. `preview/<OWNER>/<REPOSITORY>/<BRANCH>`) |
| `baseurl` | Y | `None` | The base URL that will be used by the build engine to determine the absolute path for site assets (blank for custom domains, the `site_prefix` with a preceding `/` for preview domains |
| `user_environment_variables` | Y | | Array of objects containing the name and encrypted values of user-provided environment variables (Ex. `[{ name: "MY ENV VAR", ciphertext: "ABC123" }]`) |


## Environment variables provided during builds

The following environment variables are available during site builds and when running the `federalist` npm script. They may be useful for customizing the display of certain information in the published site, for example, to display the current published branch name.

* `OWNER`
* `REPOSITORY`
* `BRANCH`
* `SITE_PREFIX`
* `BASEURL`

## Development

### Getting started

#### Requirements
- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/)
- AWS S3 bucket name and associated credentials (key, secret, region)
- A Github repository with a Federalist-compatible site
- A Github Personal Access Token if building a private repository, see [creating a new personal token for your GitHub account](https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/) for more information.

#### Clone the repository
```sh
  git clone git@github.com:18F/federalist-garden-build.git
  cd federalist-garden-build
```

#### Create build arguments
```sh
  mkdir -p .local
  cp .local.sample.json .local/my-build.json
```

#### Update build arguments
Update the appropriate fields to contain the desired values for your build, see [build arguments](#build-arguments) for options. The `.local` folder should not be checked into version control (it is in `.gitignore`) and will be mounted into the Docker container at `/tmp/local`.

#### Initialize the database
This only needs to be once. To force a reinitialization of the database, remove the `tmp/db` folder in the project root and run the below command again.

```sh
  docker-compose run --rm db
```
Then kill the process when it is done.

#### Run the build
```sh
  docker-compose build
  docker-compose run --rm app python main.py -f /tmp/local/my-build.json
```
If the database is not ready when running a build (despite the healthcheck), just try running the build again.

#### Interact with the build environment
```sh
  docker-compose run --rm app bash
  python main.py -f /tmp/local/my-build.json
```

### Inspecting the database

1. Ensure the database is running (in the background)
```
docker-compose up -d --no-deps db
```

2. Run psql in the container
```
docker-compose exec db psql -U postgres -d federalist
```

### Inspecting logs
During or after builds the echoserver and database logs can be viewed with:
```sh
  # all logs
  docker-compose logs

  # only the echo server
  docker-compose logs echoserver

  # only the db
  docker-compose logs db
```

### Testing
1. Build the test image
```sh
docker-compose build test
```

2. Run any testing steps
```sh
# unit tests
docker-compose run --rm test pytest

# unit tests with code coverage
docker-compose run --rm test pytest --cov-report xml:./coverage/coverage.xml --cov-report html:./coverage --cov-report term --cov=src

# lint
docker-compose run --rm test flake8

# static analysis
docker-compose run --rm test bandit -r src
```

## Deployment

Deployment is done by in CircleCI automatically for merges into the `staging` and `main` branch.

## Public domain

This project is in the worldwide [public domain](LICENSE.md). As stated in [CONTRIBUTING](CONTRIBUTING.md):

> This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
>
> All contributions to this project will be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.

[Federalist]: https://federalist.18f.gov
[Docker Compose]: https://docs.docker.com/compose/install/
[Docker]: https://docs.docker.com/engine/installation/
[federalist-builder]: https://github.com/18f/federalist-builder
