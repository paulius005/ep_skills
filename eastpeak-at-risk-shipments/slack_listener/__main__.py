"""Classify one Slack event. --no-post never calls chat.postMessage."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .listen import listen


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Classify an East Peak at-risk Slack event.",
    )
    parser.add_argument("--event", required=True, type=Path, help="Slack event JSON")
    parser.add_argument(
        "--no-post",
        action="store_true",
        help="Classify only. Do not post a stock reply.",
    )
    args = parser.parse_args(argv)
    event = json.loads(args.event.read_text(encoding="utf-8"))
    result = listen(event, post=not args.no_post)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
