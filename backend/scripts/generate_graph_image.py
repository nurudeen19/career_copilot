"""Write a PNG of the career workflow graph (Mermaid render via LangGraph)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=BACKEND_ROOT / "graphs" / "career_workflow.png",
        help="Output PNG path (default: backend/graphs/career_workflow.png)",
    )
    args = parser.parse_args()

    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))

    from app.graph.career_graph_builder import compile_career_graph_for_visualization

    args.output.parent.mkdir(parents=True, exist_ok=True)
    app = compile_career_graph_for_visualization()
    png: bytes = app.get_graph().draw_mermaid_png()
    args.output.write_bytes(png)
    print(f"Wrote {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
