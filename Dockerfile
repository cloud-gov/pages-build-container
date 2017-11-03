FROM python:3.6

# Install general dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      apt-utils build-essential git curl libssl-dev \
      libreadline-dev zlib1g-dev libffi-dev

# Install nvm and install versions 4 and 6
# TODO: Default to 6 LTS instead of 4
# Ref: https://github.com/18F/federalist/issues/1209
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
RUN gpg --keyserver hkp://keys.gnupg.net --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3 7D2BAF1CF37B13E2069D6956105BD0E739499BDB
RUN \curl -sSL https://get.rvm.io | bash -s stable
RUN /bin/bash -l -c 'rvm install $RUBY_VERSION && rvm use --default $RUBY_VERSION'
RUN echo rvm_silence_path_mismatch_check_flag=1 >> /etc/rvmrc

# skip installing gem documentation
RUN echo 'install: --no-document\nupdate: --no-document' >> "/etc/.gemrc"

WORKDIR /app

ADD requirements.txt ./

# TODO: For testing, we'll want to install requirements-dev.txt
# So we might need separate Dockerfiles, or maybe it can be done within
# the running testing container
RUN pip install -r requirements.txt

ADD . ./

CMD ["bash", "inv main"]
