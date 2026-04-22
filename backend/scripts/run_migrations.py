"""Run Alembic from the backend root (uses ``DATABASE_URL`` from settings / ``.env``)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    alembic_ini = BACKEND_ROOT / "alembic.ini"
    if not alembic_ini.is_file():
        print(f"Missing {alembic_ini}", file=sys.stderr)
        return 1

    args = sys.argv[1:]
    if not args:
        args = ["upgrade", "head"]

    cmd = [sys.executable, "-m", "alembic", "-c", str(alembic_ini), *args]
    return subprocess.call(cmd, cwd=str(BACKEND_ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
