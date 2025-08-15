# Quick start

See [docs/quickstart.md](docs/quickstart.md) for full instructions.

## Metrics stack

Graphite and Grafana services are included in `docker/docker-compose.yml` but are
disabled by default. Start by generating a `.env` with strong credentials (run `./docker/gen-env.sh` or copy `.env.example` and edit). Then start the monitoring stack with the `metrics` profile:

```bash
./docker/gen-env.sh               # generate .env with random secrets
# or
cp .env.example .env              # edit values manually
docker compose --profile metrics up
```

Grafana is available at [http://localhost:3001](http://localhost:3001) and the
Graphite web UI is bound to [http://localhost:8083](http://localhost:8083).
Both services authenticate using the credentials supplied in the `.env` file
and include a sample alert rule. Postgres (5432) and MariaDB (3306) are bound to 127.0.0.1 for local access only. For production deploys, put a TLS-terminating proxy with authentication in front of all HTTP services.
