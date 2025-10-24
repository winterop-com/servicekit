# Servicekit

[![CI](https://img.shields.io/badge/CI-passing-brightgreen)](https://github.com/winterop-com/servicekit/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/winterop-com/servicekit/branch/main/graph/badge.svg)](https://codecov.io/gh/winterop-com/servicekit)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

Async SQLAlchemy framework with FastAPI integration - reusable foundation for building data services.

## Quick Start

```python
from servicekit.api import BaseServiceBuilder, ServiceInfo

app = (
    BaseServiceBuilder(info=ServiceInfo(display_name="My Service"))
    .with_health()
    .with_database("sqlite+aiosqlite:///./data.db")
    .build()
)
```

Run with: `fastapi dev your_file.py`

## Installation

```bash
uv add servicekit
```

## Links

- [Repository](https://github.com/winterop-com/servicekit)
- [Issues](https://github.com/winterop-com/servicekit/issues)
- [API Reference](api-reference.md)
- [Chapkit](https://github.com/dhis2-chap/chapkit) - ML and data service modules built on servicekit ([docs](https://dhis2-chap.github.io/chapkit))

## License

AGPL-3.0-or-later
