FROM python:3.8

# Install general dependencies
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  apt-utils build-essential git curl libssl-dev \
  libreadline-dev zlib1g-dev libffi-dev libgl1-mesa-glx

# Install and setup en_US.UTF-8 locale
# This is necessary so that output from node/ruby/python
# won't break or have weird indecipherable characters
RUN apt-get update && \
  apt-get install --reinstall -y locales && \
  sed -i 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
  locale-gen en_US.UTF-8

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US
ENV LC_ALL en_US.UTF-8

RUN dpkg-reconfigure --frontend noninteractive locales

RUN groupadd customer \
  && useradd --no-log-init -m -g customer -s /bin/bash customer

RUN groupadd -r pages \
  && useradd --no-log-init -g pages -r -s /bin/bash pages

###############################################################
# Run these steps as the customer user
#
USER customer

# Default to Node 12 (erbium)
# ENV NVM_DIR /usr/local/nvm
# RUN mkdir $NVM_DIR \
RUN curl https://raw.githubusercontent.com/nvm-sh/nvm/v0.37.2/install.sh | bash
RUN bash -c "source ~/.bashrc && nvm install 'lts/erbium'"

# # Install ruby via rvm
# ENV RUBY_VERSION 2.6.6
# RUN gpg --keyserver hkp://pool.sks-keyservers.net --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3 7D2BAF1CF37B13E2069D6956105BD0E739499BDB \
#   && \curl -sSL https://get.rvm.io | bash -s stable \
#   && /bin/bash -l -c 'rvm install $RUBY_VERSION && rvm use --default $RUBY_VERSION' \
#   && echo rvm_silence_path_mismatch_check_flag=1 >> /etc/rvmrc \
#   && echo 'install: --no-document\nupdate: --no-document' >> "/etc/.gemrc"

# # Install headless chrome
# RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
#   && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
#   && apt-get update \
#   && apt-get install -y google-chrome-unstable --no-install-recommends \
#   && rm -rf /var/lib/apt/lists/*


# ###############################################################
# # Run these steps and the container as the pages user
# #
# USER pages

# WORKDIR /app

# COPY ./requirements.txt ./requirements.txt

# RUN pip install -r requirements.txt
# RUN rm ./requirements.txt

# COPY ./src ./

# # RUN useradd -m -s /bin/bash customer \
# #   && mkdir /tmp/work && chmod 777 /tmp/work \
# #   && chmod 775 $NVM_DIR \
# #   && mkdir /.gem && chmod 777 /.gem \
# #   && chmod 777 /usr/local/rvm \
# #   && chmod 777 /usr/local/rvm/gems \
# #   && chmod 774 /etc/rvmrc \
# #   && chmod 774 /etc/.gemrc \