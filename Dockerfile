FROM 18fgsa/docker-ruby-ubuntu

RUN curl https://bootstrap.pypa.io/get-pip.py | python \
  && pip install awscli

# Copy the script files
COPY *.sh /app/

WORKDIR /src

# Run the build script when container starts
CMD ["bash", "/app/main.sh"]
