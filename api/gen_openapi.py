"""Generate the OpenAPI specification file from the FastAPI app.

Output is written to ``api/openapi.json`` (configurable via the OUTPUT env
var). This file is committed to the repository so the Telegram bot can build a
client from a stable spec.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from app.main import app


def main() -> None:
    output = Path(os.environ.get("OUTPUT", "openapi.json"))
    spec = app.openapi()
    output.write_text(
        json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"OpenAPI spec written to {output}")


if __name__ == "__main__":
    main()
