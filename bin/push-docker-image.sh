# Make sure local registry is running on localhost:5000
docker build --no-cache --tag federalist-garden-build .
docker tag federalist-garden-build localhost:5000/federalist-garden-build
docker push localhost:5000/federalist-garden-build
