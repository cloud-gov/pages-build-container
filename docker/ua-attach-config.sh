UA_TOKEN=`cat /run/secrets/UA_TOKEN`

echo "Configuring ua attach config"
cat <<EOF >> ua-attach-config.yaml
token: $UA_TOKEN
enable_services:
- usg
- esm-infra