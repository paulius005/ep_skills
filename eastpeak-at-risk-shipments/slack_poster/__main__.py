"""Preview or post an at-risk shipment report.

Dry run prints the chat.postMessage payloads and does not read SLACK_BOT_TOKEN.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .blocks import report_from_dict
from .post import post_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Post the East Peak at-risk shipment report with Slack Block Kit.",
    )
    parser.add_argument("--report", required=True, type=Path, help="Structured report JSON")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the payloads. Do not read the bot token and do not call Slack.",
    )
    args = parser.parse_args(argv)
    report = report_from_dict(json.loads(args.report.read_text(encoding="utf-8")))
    if args.dry_run:
        result = post_report(report, dry_run=True)
        json.dump(result["messages"], sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    result = post_report(report)
    json.dump(
        {"ok": True, "parent_ts": result["parent_ts"], "permalink": result["permalink"]},
        sys.stdout,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
