# Auth example

Demonstrates API key authentication with `BaseServiceBuilder.with_auth()`, covering every supported key source. `main.py` uses the recommended environment-variable source by default; the other sources are shown as commented variants.

## Key sources

| Source | How | When to use |
| --- | --- | --- |
| Environment variable | `.with_auth()` reads `SERVICEKIT_API_KEYS` (comma-separated) | Recommended for production; supports zero-downtime rotation |
| Inline keys | `.with_auth(api_keys=[...])` | Local development only - never commit real keys |
| Custom header | `.with_auth(header_name="X-Custom-Auth-Token")` | Legacy integration or compliance requirements |
| Docker secrets / file | `.with_auth(api_key_file="/run/secrets/api_keys")` | Containers (Compose, Swarm, Kubernetes) |

The default header is `X-API-Key`.

## Run

```bash
cp .env.example .env        # then edit SERVICEKIT_API_KEYS
uv run --env-file .env main.py
```

Call an authenticated endpoint:

```bash
curl -H "X-API-Key: sk_dev_abc123" http://localhost:8000/api/v1/system
```

To try the Docker-secrets variant locally, copy `secrets/api_keys.txt.example` to `secrets/api_keys.txt` and switch `main.py` to the `api_key_file` variant.

## Docker

```bash
docker compose up --build
```
