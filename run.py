"""Start the integrated website with PyCharm's Run button or `python run.py`."""

import os
from pathlib import Path
import sys

from starlette.config import Config
import uvicorn


ROOT = Path(__file__).resolve().parent


def main():
    env_file = ROOT / ".env"
    if env_file.is_file():
        # Use the existing FastAPI dependency; keep configured environment values.
        for name, value in Config(env_file=env_file).file_values.items():
            os.environ.setdefault(name, value)

    try:
        port = int(os.environ.get("FUTURESKILL_PORT", "5000"))
    except ValueError:
        raise SystemExit("FUTURESKILL_PORT must be an integer between 1 and 65535.") from None
    if not 1 <= port <= 65535:
        raise SystemExit("FUTURESKILL_PORT must be an integer between 1 and 65535.")

    # Resolve src from this file, so the launcher's working directory can vary.
    sys.path.insert(0, str(ROOT / "src"))
    uvicorn.run("main:app", host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
