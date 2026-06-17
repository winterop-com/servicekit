# Core CLI example

Uses the framework-agnostic core - `Database`, `Repository`, and `Manager` - directly, with no FastAPI layer. Shows how to define an `Entity`, its `EntityIn`/`EntityOut` schemas, and drive CRUD through a `Manager` from a plain async script.

## Run

```bash
uv run main.py
```

The script builds an in-memory SQLite database, creates and queries `Product` records, and prints the results.
