
### Notes

- http://docs.pyinvoke.org/en/latest/

- TODO: pytest
- TODO: send logs after each step
- TODO: capture errors and post logs:
  https://gist.github.com/66Ton99/b13c2867adef506554a4
- TODO: use mypy?
- TODO: gemnasium, circle, etc.
- TODO: dockerize for both dev and deploy
- TODO: write README. can use lots of old one.
    - update development section

## Environment Variables

### Variables available to build bngines

The following environment variables may be accessed during a site's build. They may be useful for customizing the display of certain information in the published site, for example, to display the current published branch name.

1. `OWNER`: the GitHub account that owns the repository.
1. `REPOSITORY`: the repository name.
1. `BRANCH`: the branch being built.
1. `SITE_PREFIX`: the S3 bucket "path" that the site files will be published to.
  - for the live site: `site/<OWNER>/<REPOSITORY>`.
  - for the demo site: `demo/<OWNER>/<REPOSITORY>`.
  - for branch previews: `preview/<OWNER>/<REPOSITORY>/<BRANCH>`.
1. `BASEURL`: the base URL that will be used by the build engine to determine the path for site assets.
  - for a live site with a custom URL, this will be empty.
  - for anything else, it will be the same as `SITE_PREFIX` but
    with a `/` at the beginning. ex: `/site/<OWNER>/<REPOSITORY>`.
1. `LANG`: `C.UTF-8` (necessary to avoid encoding issues in Ruby/Jekyll).

### Private variables

TODO: fill out

## Development

Use Docker Compose for local development and testing.

To make setting environment variables easier for local development,
create a new `.env` file based on the `.env.sample`:

```sh
cp .env.sample .env
```

Then fill out the values in it. Be careful not to commit this file because
it might have sensitive information in it. It is ignored by the `.gitignore` file.

```
docker-compose build
docker-compose run app
```

Run `docker-compose run app bash` to start up bash in a transient `app` container.

For testing:

```sh
docker-compose run app pytest
```