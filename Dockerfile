from jekyll/jekyll:pages

# Copy the build file
COPY build.sh /

# Install the AWS CLI
# source: https://github.com/anigeo/docker-awscli/blob/master/Dockerfile
RUN \
	mkdir -p /aws && \
	apk -Uuv add groff less python py-pip && \
	pip install awscli && \
	apk --purge -v del py-pip && \
	rm /var/cache/apk/*

# Run the build script when container starts
CMD ["/build.sh"]
