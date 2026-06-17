# Job scheduler example

FastAPI service demonstrating the async job scheduler via `BaseServiceBuilder.with_jobs()`. Submits background computations, tracks them through the `/api/v1/jobs` endpoints, and streams live status updates over Server-Sent Events.

## Run

```bash
uv run main.py
```

Then submit a job and watch it progress:

```bash
curl -X POST http://localhost:8000/api/v1/compute -H "Content-Type: application/json" -d '{"duration": 5}'
```

Import `postman_collection.json` for the full request set.

## Docker

```bash
docker compose up --build
```
