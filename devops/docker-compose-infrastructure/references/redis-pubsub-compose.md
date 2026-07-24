# Dedicated Redis/Valkey Pub/Sub in Docker Compose

Use this pattern when a service already has Redis for BullMQ or another queue system, and a new feature needs ephemeral pub/sub fan-out for websocket/global event delivery.

## Recommendation

Create a separate Redis/Valkey service for pub/sub instead of reusing queue Redis:

- Queue Redis: jobs, retries, backoff, queue metadata, operational policies for durable-ish work.
- Pub/sub Redis: small transient messages, websocket fan-out, no replay/durability expectations.

This separation prevents pub/sub traffic and reconnect behavior from interfering with BullMQ policies.

## Compose snippet

```yaml
  socket-pubsub-redis:
    image: redis:latest
    restart: unless-stopped
    ports:
      - '6380:6379'
    volumes:
      - socket_pubsub_redis_v2_data:/data

volumes:
  socket_pubsub_redis_v2_data: {}
```

Use a host port that does not conflict with the existing Redis service. If the main Redis is already mapped as `6379:6379`, map the pub/sub Redis as `6380:6379`.

## App env convention

Prefer dedicated env vars instead of overloading `REDIS_*`:

```text
SOCKET_EVENT_BUS_REDIS_HOST=
SOCKET_EVENT_BUS_REDIS_PORT=6379
SOCKET_EVENT_BUS_REDIS_USER=
SOCKET_EVENT_BUS_REDIS_PASSWORD=
SOCKET_EVENT_BUS_REDIS_FAMILY=6
```

For local host-driven app processes, `SOCKET_EVENT_BUS_REDIS_HOST=localhost` and `SOCKET_EVENT_BUS_REDIS_PORT=6380` may be appropriate. For containers on the same compose network, use `SOCKET_EVENT_BUS_REDIS_HOST=socket-pubsub-redis` and port `6379`.

## Verification

Run:

```bash
docker compose config --quiet
```

If also running repo lint, do not present an ESLint “file ignored because no matching configuration was supplied” warning as YAML validation. The Compose config command is the authoritative local syntax/config check.
