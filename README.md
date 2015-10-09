# Docker Builder for federalist

This is a Docker image that runs Jekyll to build a site. It's used to allow Jekyll sites to build with user-provided plugins in a safe space.

The build script reads source files from S3, runs Jekyll, and uploads the generated `_site` files back to S3, then `POST`s the results to a URL.

Configure the build process with following environment variables:

- `AWS_ACCESS_KEY_ID` AWS access key
- `AWS_SECRET_ACCESS_KEY` AWS secret key
- `S3_PATH` S3 bucket prefix for build files (no leading slash, include trailing slash)
- `FINISHED_URL` a URL that will receive a `POST` request with a JSON body including the `status` code and output `message` from the Jekyll process

The AWS variables are unset in the Jekyll subprocess so Jekyll and its plugins do not have access to this information.


### Public domain

This project is in the worldwide [public domain](LICENSE.md). As stated in [CONTRIBUTING](CONTRIBUTING.md):

> This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
>
> All contributions to this project will be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.
