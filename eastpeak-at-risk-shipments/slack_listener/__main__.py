"""Classify one Slack event and post only through slack_poster.

A message that does not map to an allowed shipment action prints `"posted": false`
and does not call chat.postMessage. A conversation still needs a reply from the
agent. This command never prints SLACK_BOT_TOKEN.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .listen import listen

PUBLIC_KEYS = ("action", "label", "order_ts", "thread_ts", "reason", "posted", "ts", "app_name")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reply in #at-risk-shipments only through the East Peak Operations bot token.",
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
    public = {key: result.get(key) for key in PUBLIC_KEYS}
    json.dump(public, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
