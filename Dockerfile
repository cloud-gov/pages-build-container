# FROM 18fgsa/docker-ruby-ubuntu
FROM python:3.6

# Install general dependencies and configure locales
# TODO: Why is this locale stuff necessary?
# TODO: I see this error: bash: warning: setlocale: LC_ALL: cannot change locale (en_US.UTF-8)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      apt-utils build-essential git curl libssl-dev \
      libreadline-dev zlib1g-dev libffi-dev locales \
    && locale-gen en_US en_US.UTF-8 \
    && dpkg-reconfigure locales

# -- from https://github.com/18F/docker-ruby-ubuntu/blob/master/Dockerfile -----
# Moved the following RUN up above
# RUN locale-gen en_US en_US.UTF-8 \
#   && dpkg-reconfigure locales

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# # Install general dependencies
# RUN apt-get update && apt-get install -y build-essential git curl libssl-dev libreadline-dev zlib1g-dev python3-dev

# install nvm and install versions 4 and 6
ENV NVM_DIR /usr/local/nvm
ENV NODE_DEFAULT_VERSION 4
RUN curl https://raw.githubusercontent.com/creationix/nvm/v0.31.3/install.sh | bash \
  && . "$NVM_DIR/nvm.sh" \
  && nvm install $NODE_DEFAULT_VERSION \
  && nvm install 6 \
  && nvm use $NODE_DEFAULT_VERSION \
  && echo 'export OLD_PREFIX=$PREFIX && unset PREFIX' > $HOME/.profile \
  && echo '[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"' >> $HOME/.profile \
  && echo 'export PREFIX=$OLD_PREFIX && unset OLD_PREFIX' >> $HOME/.profile

# Install ruby via rvm
ENV RUBY_VERSION 2.3.1
RUN \curl -sSL https://get.rvm.io | bash -s stable
RUN /bin/bash -l -c 'rvm install $RUBY_VERSION && rvm use --default $RUBY_VERSION'
RUN echo rvm_silence_path_mismatch_check_flag=1 >> /etc/rvmrc
# -- end https://github.com/18F/docker-ruby-ubuntu/blob/master/Dockerfile ----

# Defaults for ENV variables
ENV AWS_DEFAULT_REGION "us-east-1"

# skip installing gem documentation
RUN echo 'install: --no-document\nupdate: --no-document' >> "/etc/.gemrc"

# Install the AWS SDK and MIME for publishing
RUN bin/bash -l -c "gem install aws-sdk mime-types"

# --- This section is the previous Dockerfile for this repo ---
# # node-gyp needs Python 2.7
# RUN apt-get install -y python2.7
# ENV PYTHON /usr/bin/python2.7

# # Copy the script files
# COPY *.sh /app/
# COPY *.rb /app/

# # Add the working directory
# WORKDIR /src

# # Run the build script when container starts
# CMD ["bash", "/app/run.sh"]
# --------------

# install hugo
ENV HUGO_VERSION 0.23
RUN curl -sSL https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_${HUGO_VERSION}_Linux-64bit.deb -o hugo.deb \
  && dpkg -i hugo.deb

WORKDIR /app

ADD requirements.txt ./
RUN pip install -r requirements.txt

ADD . ./

# TODO: the run args should come from environment vars set by federalist-builder
CMD PYTHONPATH='.' luigi --module main RunAll --repo-owner jseppi --repo-name hugoBasicExample --branch master --build-engine hugo --work-dir ./tmp --local-scheduler --log-level INFO
