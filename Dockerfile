FROM 18fgsa/docker-ruby-ubuntu

# Preload recent Jekyll versions
RUN gem install jekyll jekyll:3.0.1 jekyll:3.0.0 jekyll:2.5.3 jekyll:2.4.0

RUN curl https://bootstrap.pypa.io/get-pip.py | python \
  && pip install awscli

# Copy the script files
COPY *.sh /app/

WORKDIR /src

# Run the build script when container starts
CMD ["bash", "/app/main.sh"]
