## Docker

### Build Image

```shell
sudo docker build --tag mes-opcuax .
```

### Create Network

```shell
docker network create mes
```

### Run Server

```shell
docker run -d --name=mes-opcua-server -p 4840:4840 \
  --network mes \
  --restart unless-stopped \
  -e OPCUA_SERVER_URL="opc.tcp://0.0.0.0:4840" \
  -e OPCUA_SERVER_NAME="Monash Automation OPC UA Server" \
  -e OPCUA_SERVER_NAMESPACE='http://monashautomation.com/opcua/server' \
  -e METADATA_FILE="/app/objects.toml" \
  mes-opcuax server
```

```shell
docker run -d --name mes-redis --network mes redis
```

### Run Worker

```shell
docker run --rm --name=mes-opcua-worker \
  --network mes \
  -e OPCUA_SERVER_URL="opc.tcp://mes-opcua-server:4840" \
  -e REDIS_URL="redis://mes-redis:6379" \
  mes-opcuax cache
```

Check Redis objects

```shell
docker exec -it mes-redis redis-cli hgetall printer1
```

### Grafana Dashboard

```shell
docker run -d --name=mes-grafana -p 3080:3000 \
  --network mes \
  -v grafana:/var/lib/mes-grafana \
  -e "GF_INSTALL_PLUGINS=grafana-clock-panel, grafana-simple-json-datasource, redis-datasource" \
  grafana/grafana-oss
```

Open `localhost:3080`, username is `admin` and password is `1234`
