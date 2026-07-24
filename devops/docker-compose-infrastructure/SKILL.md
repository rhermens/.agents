---
name: docker-compose-infrastructure
description: Modify and verify Docker Compose infrastructure services, ports, volumes, and local dependency containers.
---

# Docker Compose Infrastructure

Use this skill when adding or changing local infrastructure in `docker-compose.yaml` / `compose.yaml`: databases, Redis/Valkey, queues, pub/sub brokers, object storage, mail catchers, tunnels, or supporting containers.

## Workflow

1. Locate the compose file with file search before editing.
2. Read the full compose file to understand existing service naming, port conventions, volumes, profiles, and network mode.
3. Search for related env vars and app configuration so the service name and exposed ports match how the app will consume it.
4. Make the smallest scoped YAML change:
   - add a distinct service name;
   - avoid host-port collisions;
   - add a separate named volume when persistence/isolation matters;
   - keep existing services unchanged unless explicitly requested.
5. Verify with Docker Compose itself:

```bash
docker compose config --quiet
```

6. Report the exact service/port/volume changes and the real verification result.

## Pitfalls

- Do not treat TypeScript/ESLint project lint as meaningful validation for Compose YAML. It may exit successfully while warning that the YAML file was ignored. For Compose correctness, cite `docker compose config --quiet`.
- Keep queue Redis and ephemeral pub/sub Redis separate unless the user explicitly asks to reuse one instance. Queue durability/retry policy and transient socket fan-out behavior have different operational concerns.
- For a second local Redis/Valkey service, expose a different host port, e.g. host `6380` to container `6379`, while Docker-network clients use the service name and container port.

## References

- `references/redis-pubsub-compose.md` — dedicated Redis/Valkey pub/sub instance pattern for apps that already use Redis for queues.
