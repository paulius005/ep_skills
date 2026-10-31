"""Post a planned report with chat.postMessage. Tests pass a transport."""

from __future__ import annotations

import json
import os
import urllib.request

from .blocks import Report, plan_messages, parent_blocks, parent_fallback, slack_permalink

TOKEN_ENV = "SLACK_BOT_TOKEN"
SLACK_API = "https://slack.com/api/"


class SlackAPIError(RuntimeError):
    def __init__(self, method: str, error_code: str):
        super().__init__(f"Slack {method} failed: {error_code}")
        self.method = method
        self.error_code = error_code


class UrllibSlackTransport:
    """POST JSON to the Slack Web API. The token stays on the Authorization header."""

    def __init__(self, token: str, opener=None):
        if not token:
            raise RuntimeError(f"{TOKEN_ENV} is not set")
        self._token = token
        self._opener = opener or urllib.request.urlopen

    def __call__(self, method: str, body: dict) -> dict:
        url = SLACK_API + method
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            method="POST",
        )
        request.add_header("Authorization", f"Bearer {self._token}")
        request.add_header("Content-Type", "application/json; charset=utf-8")
        with self._opener(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not payload.get("ok"):
            raise SlackAPIError(method, str(payload.get("error") or "unknown"))
        return payload


def _message_body(channel_id: str, text: str, blocks: list, thread_ts: str | None = None) -> dict:
    body = {
        "channel": channel_id,
        "text": text,
        "blocks": blocks,
        "unfurl_links": False,
        "unfurl_media": False,
    }
    if thread_ts:
        body["thread_ts"] = thread_ts
    return body


def post_report(report: Report, *, transport=None, token: str | None = None, dry_run: bool = False) -> dict:
    """Post the parent, then one thread reply per order and any address section.

    `dry_run` returns the payloads and does not read the token or call Slack.
    Pass `transport` in tests. A transport is `callable(method, body) -> dict`.
    """
    planned = plan_messages(report)
    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "messages": [message.as_dict() for message in planned],
        }
    if transport is None:
        secret = token if token is not None else os.environ.get(TOKEN_ENV)
        if not secret:
            raise RuntimeError(f"{TOKEN_ENV} is not set")
        transport = UrllibSlackTransport(secret)

    parent = planned[0]
    posted = transport("chat.postMessage", _message_body(
        report.channel_id, parent.text, parent.blocks,
    ))
    parent_ts = str(posted["ts"])
    permalink = slack_permalink(report.channel_id, parent_ts)
    transport("chat.update", {
        "channel": report.channel_id,
        "ts": parent_ts,
        "text": parent_fallback(report, permalink),
        "blocks": parent_blocks(report, permalink),
        "unfurl_links": False,
        "unfurl_media": False,
    })
    results = [{"kind": "parent", "ts": parent_ts, "permalink": permalink}]
    for message in planned[1:]:
        reply = transport("chat.postMessage", _message_body(
            report.channel_id, message.text, message.blocks, thread_ts=parent_ts,
        ))
        results.append({
            "kind": message.kind,
            "order_number": message.order_number,
            "ts": reply.get("ts"),
        })
    return {
        "ok": True,
        "dry_run": False,
        "parent_ts": parent_ts,
        "permalink": permalink,
        "results": results,
    }
