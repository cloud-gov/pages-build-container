FROM 18fgsa/docker-ruby-ubuntu
RUN apt-get update

# Create a federalist urser
RUN useradd -G rvm federalist
RUN mkdir /home/federalist
RUN chown -R federalist /home/federalist

# Defaults for ENV vairables
ENV AWS_DEFAULT_REGION "us-east-1"

# skip installing gem documentation
RUN echo 'install: --no-document\nupdate: --no-document' >> "/home/federalist/.gemrc"

# Install the AWS CLI
RUN curl https://bootstrap.pypa.io/get-pip.py | python3 \
  && pip install awscli

# node-gyp needs Python 2.7
RUN apt-get install -y python2.7
ENV PYTHON /usr/bin/python2.7

# Copy the script files
COPY *.sh /app/
RUN chmod -R 555 /app

# Add the working directory
WORKDIR /src
RUN chown -R federalist /src

# Change to the Federalist user
USER federalist

# Run the build script when container starts
CMD ["bash", "/app/main.sh"]
