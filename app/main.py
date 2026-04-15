"""Dev entry: run stub pipeline."""

from app.core import init_app
from app.pipeline import run_turn


def main() -> None:
    init_app()
    out = run_turn("I'm a backend dev — should I move into AI?")
    for key in ("plan", "research", "analysis", "critique", "synthesis"):
        print(f"\n=== {key} ===\n{out[key]}")


if __name__ == "__main__":
    main()
