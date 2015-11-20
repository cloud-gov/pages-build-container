FROM jekyll/jekyll:pages

# Copy the script files
COPY *.sh /app/

# Install Bash
RUN apk --update add bash

# Install the AWS CLI
# source: https://github.com/anigeo/docker-awscli/blob/master/Dockerfile
RUN mkdir -p /aws
RUN apk --update add py-pip
RUN pip install awscli
RUN apk --purge -v del py-pip

# Run the build script when container starts
CMD ["bash", "/app/main.sh"]
