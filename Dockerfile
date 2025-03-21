# syntax = docker/dockerfile:1.2
FROM ubuntu:22.04

# Install general dependencies
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  apt-utils build-essential git curl libssl-dev \
  libreadline-dev zlib1g-dev libffi-dev libgl1-mesa-glx \
  sudo gnupg ca-certificates ubuntu-advantage-tools \
  autoconf automake libgdbm-dev libncurses5-dev \
  libsqlite3-dev libtool libyaml-dev pkg-config libgmp-dev \
  libpq-dev libxi6 libjpeg-dev libpng-dev libtiff-dev libgif-dev \
  libwebp-dev wget python3 python3-dev python3-pip\
  # Ruby deps
  gawk bison sqlite3

# Deps for container hardening
RUN ln -sf "/usr/share/zoneinfo/$SYSTEM_TIMEZONE" /etc/localtime
COPY docker/ua-attach-config.sh .
RUN --mount=type=secret,id=UA_TOKEN ./ua-attach-config.sh && \
  ua attach --attach-config ua-attach-config.yaml && \
  rm ua-attach-config.yaml
RUN apt-get -y -q install usg

# Install and setup en_US.UTF-8 locale
# This is necessary so that output from node/ruby/python
# won't break or have weird indecipherable characters
RUN apt-get update && \
  apt-get install --reinstall -y locales && \
  sed -i 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
  locale-gen en_US.UTF-8

# Install headless chrome
ARG DEBIAN_FRONTEND=noninteractive
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
  && echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' >> /etc/apt/sources.list.d/google.list \
  && apt-get update \
  && apt-get install -y google-chrome-unstable --no-install-recommends \
  && rm -rf /var/lib/apt/lists/*

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US
ENV LC_ALL en_US.UTF-8

RUN dpkg-reconfigure --frontend noninteractive locales

SHELL ["/bin/bash", "-c"]

# Disable ipv6 to enable fetching gpg keys for rvm
# http://rvm.io/rvm/security#ipv6-issues
RUN mkdir -p /root/.gnupg \
  && echo 'disable-ipv6' >> /root/.gnupg/dirmngr.conf \
  && echo 'rvm_silence_path_mismatch_check_flag=1' >> /etc/rvmrc \
  && echo 'install: --no-document\nupdate: --no-document' >> /etc/.gemrc

RUN useradd --no-log-init --system --create-home --groups sudo system \
  && echo 'system ALL=(ALL:ALL) NOPASSWD:ALL' >> /etc/sudoers.d/system

RUN useradd --no-log-init --system --create-home customer

###############################################################
# Run these steps as the 'system' user
#
USER system

# Install rvm
RUN set -ex \
  && for key in \
    409B6B1796C275462A1703113804BB82D39DC0E3 \
    7D2BAF1CF37B13E2069D6956105BD0E739499BDB \
  ; do \
    sudo gpg --batch --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys "$key" || \
    sudo gpg --batch --keyserver hkp://pool.sks-keyservers.net:80 --recv-keys "$key" || \
    sudo gpg --batch --keyserver hkp://ipv4.pool.sks-keyservers.net --recv-keys "$key" || \
    sudo gpg --batch --keyserver hkp://pgp.mit.edu:80 --recv-keys "$key" || \
    sudo gpg --batch --keyserver hkp://keyserver.pgp.com --recv-keys "$key" ; \
  done \
  # We use 'sudo' here to support multi-user install
  # http://rvm.io/rvm/install#1-download-and-run-the-rvm-installation-script
  && \curl -sSL https://get.rvm.io | sudo -n bash -s stable

# Add 'customer' user to rvm group
RUN sudo usermod --append --groups rvm customer

###############################################################
# Run these steps as the customer user
#
USER customer

# Configure rvm and install default Ruby
ENV RUBY_VERSION 3.1.4
ENV RUBY_VERSION_MIN 3.0.6
RUN source /usr/local/rvm/scripts/rvm \
  # Fail if deps are missing, won't prompt for sudo
  && rvm autolibs read-fail \
  && rvm install --no-docs $RUBY_VERSION \
  && rvm use --default $RUBY_VERSION \
  # Make rvm available in non-login bash shells
  && echo 'source /usr/local/rvm/scripts/rvm' >> ~/.bashrc

# Update to the latest RubyGems
RUN source /usr/local/rvm/scripts/rvm && \
    rvm rubygems 3.4.22

# Default to Node 20
ENV NODE_VERSION lts/iron
RUN curl https://raw.githubusercontent.com/nvm-sh/nvm/v0.37.2/install.sh | bash \
  && \. "$HOME/.nvm/nvm.sh" \
  && nvm install $NODE_VERSION


###############################################################
# Run these steps and the container as the 'root' user
#
# This is necessary because the build code needs to have
# rights to switch to 'customer' user
#
USER root

WORKDIR /app

COPY ./requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt \
  && rm ./requirements.txt

RUN ln -s /usr/bin/python3 /usr/bin/python

COPY ./src ./

# Container Hardening
RUN usg fix cis_level1_server
RUN apt-get purge --auto-remove -y ubuntu-advantage-tools
