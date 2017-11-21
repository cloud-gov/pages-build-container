[![CircleCI](https://circleci.com/gh/18F/federalist-garden-build.svg?style=svg)](https://circleci.com/gh/18F/federalist-garden-build)
[![Dependency Status](https://gemnasium.com/badges/github.com/18F/federalist-garden-build.svg)](https://gemnasium.com/github.com/18F/federalist-garden-build)
[![Maintainability](https://api.codeclimate.com/v1/badges/322b89a24f0efc284dee/maintainability)](https://codeclimate.com/github/18F/federalist-garden-build/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/322b89a24f0efc284dee/test_coverage)](https://codeclimate.com/github/18F/federalist-garden-build/test_coverage)

# federalist-garden-build

Docker image for building and publishing static sites as part of the [Federalist][] platform. Build steps are written using the [PyInvoke][] task running framework.

Generally, site builds work in three stages: clone, build, and publish. Each stage is broken down into a number of [PyInvoke][] tasks. First, the container checks out the site from GitHub. Then it builds the site with the specified build engine. Then it gzip compresses text files and sets cache control headers. Finally, it uploads the built site to S3, and also creates redirect objects for directories, such as `/path` => `/path/`.

The `main` [PyInvoke][] task is used to run a full build process when the container starts. After the container finishes (or times-out), the container then `sleep`s indefinitely (see [`run.sh`](run.sh)).

## Environment Variables

Each site build is configured using a number of environment variables, as described below:

* `AWS_ACCESS_KEY_ID`: AWS access key for accessing the S3 bucket.
* `AWS_SECRET_ACCESS_KEY`: AWS secret key for accessing the S3 bucket.
* `AWS_DEFAULT_REGION`: AWS region.
* `BUCKET`: S3 bucket to upload the built site.
* `GITHUB_TOKEN` GitHub auth token for cloning the repository.
* `CACHE_CONTROL`: Value to set for the `Cache-Control` header of all published files.
* `CONFIG`: A yaml block of configuration to add to `_config.yml` before building. Currently only used in `jekyll` site builds.
* `GENERATOR`: The static generator to use to build the site (`'jekyll'`, `'hugo'`, or `'static'`).
* `FEDERALIST_BUILDER_CALLBACK`: The URL the container should use to let [federalist-builder][] know that it has finished.
* `STATUS_CALLBACK`: The URL the container should use to report the status of the completed build (ie, success or failure).
* `LOG_CALLBACK`: The URL the container should use to post build logs periodically during the build.
* `OWNER`: the GitHub account that owns the repository.
* `REPOSITORY`: the repository name.
* `BRANCH`: the branch being built.
* `SITE_PREFIX`: the S3 bucket "path" that the site files will be published to. It should **not** have a trailing or prefix slash.
  * for the live site: `site/<OWNER>/<REPOSITORY>`.
  * for the demo site: `demo/<OWNER>/<REPOSITORY>`.
  * for branch previews: `preview/<OWNER>/<REPOSITORY>/<BRANCH>`.
* `BASEURL`: the base URL that will be used by the build engine to determine the path for site assets.
  * for a live site with a custom URL, this will be empty.
  * for anything else, it will be the same as `SITE_PREFIX` but
    with a `/` at the beginning. ex: `/site/<OWNER>/<REPOSITORY>`.

### Variables exposed during builds

The following environment variables are available during site builds and when running the `federalist` npm script. They may be useful for customizing the display of certain information in the published site, for example, to display the current published branch name.

* `OWNER`
* `REPOSITORY`
* `BRANCH`
* `SITE_PREFIX`
* `BASEURL`

## Development

You'll need [Docker][] and [Docker Compose][] installed for development and testing.

### Environment variables

To make setting environment variables easier for local development,
create a new `.env` file based on the `.env.sample` and fill out the environment variables in it. Your `.env` file should **not be committed** to the repository
because it will contain sensitive information. It is ignored by `.gitignore`.

```sh
cp .env.sample .env
```

For the AWS S3 values needed, you might find it helpful to
spin up an [S3 service](https://cloud.gov/docs/services/s3/) in your [cloud.gov sandbox space](https://cloud.gov/overview/pricing/free-limited-sandbox/).

For the `GITHUB_TOKEN`, create a new [personal token for your GitHub account](https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/) and use that.

### Building and running

Build the development container using Docker Compose:

```sh
docker-compose build
```

The main builder application is called `app` within the Docker Compose environment.
You can run any commands within the `app` container by prefixing them with `docker-compose run app <THE COMMAND>`.

One of the easiest ways to run the container's code during development is to start
an interactive `bash` shell in the `app` container:

```sh
docker-compose run app bash
```

After running the above command, you will be in a shell inside of the `app` container. From there, you can easily run [PyInvoke][] tasks or execute the test suite.

```sh
invoke --help   # prints Invoke's usage
invoke --list   # lists all the available tasks
invoke main     # runs the full clone-build-publish pipeline
pytest          # run all the python tests
```

## Deploying to cloud.gov

For detailed instructions on deploying this build container to cloud.gov, see [https://federalist-docs.18f.gov/pages/how-federalist-works/cloud-gov-setup/](https://federalist-docs.18f.gov/pages/how-federalist-works/cloud-gov-setup/).

## Public domain

This project is in the worldwide [public domain](LICENSE.md). As stated in [CONTRIBUTING](CONTRIBUTING.md):

> This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
>
> All contributions to this project will be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.

[PyInvoke]: http://www.pyinvoke.org/
[Federalist]: https://federalist.18f.gov
[Docker Compose]: https://docs.docker.com/compose/install/
[Docker]: https://docs.docker.com/engine/installation/
[federalist-builder]: https://github.com/18f/federalist-builder
