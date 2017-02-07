FROM 18fgsa/docker-ruby-ubuntu
RUN apt-get update

# Defaults for ENV vairables
ENV AWS_DEFAULT_REGION "us-east-1"

# Preload recent Jekyll versions and install github-pages gem
RUN gem install jekyll jekyll:3.0.1 jekyll:3.0.0 jekyll:2.5.3 jekyll:2.4.0 github-pages

# Install the AWS CLI
RUN curl https://bootstrap.pypa.io/get-pip.py | python3 \
  && pip install awscli

# node-gyp needs Python 2.7
RUN apt-get install -y python2.7
ENV PYTHON /usr/bin/python2.7

# Copy the script files
COPY *.sh /app/

WORKDIR /src

# Run the build script when container starts
CMD ["bash", "/app/main.sh"]
