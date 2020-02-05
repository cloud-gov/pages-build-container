# Make sure local registry is running on localhost:5000
CONTAINER_NAME=federalist-garden-build
APP_NAME=federalist-build-container-staging
REGISTRY_HOST=localhost:5000
REGISTRY_NAME=federalist-registry-staging.fr.cloud.gov

docker build --no-cache --tag $CONTAINER_NAME .
docker tag $CONTAINER_NAME $REGISTRY_HOST/$CONTAINER_NAME
docker push $REGISTRY_HOST/$CONTAINER_NAME
cf t -o gsa-18f-federalist -s staging
cf push $APP_NAME-1 --no-route -u none -m 2G -k 4G -o "$REGISTRY_NAME/$CONTAINER_NAME"
cf push $APP_NAME-2 --no-route -u none -m 2G -k 4G -o "$REGISTRY_NAME/$CONTAINER_NAME"