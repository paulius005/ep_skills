"""Map a Slack reply to one skill action, and never answer the bot.

East Peak Operations posts the daily parent and the order cards. Those posts
are not human actions. A human reply counts only when it @mentions that same
app and names an allowed action. Replies, when sent, use SLACK_BOT_TOKEN.
This module does not call ShipMonk and does not print the token.
"""

from __future__ import annotations

import json
import os
import re

from slack_poster.post import TOKEN_ENV, UrllibSlackTransport, post_thread_reply

BOT_APP_NAME = "East Peak Operations"
CHANNEL_ID = "C0CCJJGG6HK"
ALLOWED_STORES = {"19002", "18969"}

# Longer labels first so an exact match cannot be confused with a shorter one.
ACTION_LABELS = (
    ("Draft an email to the customer", "draft_address_check"),
    ("Draft address-check email", "draft_address_check"),
    ("guarded clone and submit", "guarded_clone_and_submit"),
    ("unsent Gmail draft", "unsent_gmail_draft"),
    ("USPS Priority", "usps_priority"),
)
BUTTON_ACTIONS = {"usps_priority", "draft_address_check"}

MENTION_RE = re.compile(r"<@([A-Z0-9]+)(?:\|([^>]*))?>")
TS_RE = re.compile(r"\d+\.\d+")
PARENT_MARK = "At-risk shipments ·"
ADDRESS_MARK = "Do not change the address until this is approved."


def classify(event: dict, bot_user_id: str | None = None) -> dict:
    """Return the mapped action, or action None with a reason. Never posts."""
    message = _unwrap(event)
    channel = _channel(message)
    if channel != CHANNEL_ID:
        return _decision(reason="wrong_channel")
    if _authored_by_operations(message, bot_user_id):
        return _decision(reason="bot")
    # A button click carries the order card inside `message`. That card is the
    # report the person clicked, not a second post to ignore.
    if message.get("type") != "block_actions" and _is_report_post(message):
        return _decision(reason="report_post")
    if message.get("type") == "block_actions":
        return _map_button(message)
    if message.get("subtype"):
        return _decision(reason="not_an_action")
    if message.get("type") not in {None, "message", "app_mention"}:
        return _decision(reason="not_an_action")
    if not _mentions_operations(message, bot_user_id):
        return _decision(reason="no_mention")
    mapped = _map_label(message.get("text") or "", message.get("thread_ts"))
    if mapped is None:
        return _decision(reason="not_an_action")
    action, label, order_ts = mapped
    return _decision(
        action=action,
        label=label,
        order_ts=order_ts,
        thread_ts=order_ts,
    )


def listen(
    event: dict,
    *,
    transport=None,
    token: str | None = None,
    bot_user_id: str | None = None,
    post: bool = False,
) -> dict:
    """Classify one event. Post a thread reply only when post=True and it mapped.

    When the token is present and bot_user_id was not passed, the bot user id
    comes from auth.test. The token stays on the Authorization header.
    """
    secret = token if token is not None else os.environ.get(TOKEN_ENV)
    if bot_user_id is None and (transport is not None or secret):
        if transport is None:
            transport = UrllibSlackTransport(secret)
        bot_user_id = _bot_user_id(transport)
    decision = classify(event, bot_user_id=bot_user_id)
    result = dict(decision)
    result["posted"] = False
    # No mapped action means no Slack call. A missing @mention, a bot post,
    # and a parent card all land here. Do not explain that in the channel.
    if not post or not decision["action"] or not decision.get("thread_ts"):
        return result
    posted = post_thread_reply(
        channel_id=CHANNEL_ID,
        thread_ts=str(decision["thread_ts"]),
        text=_reply_text(decision),
        transport=transport,
        token=secret,
    )
    result["posted"] = True
    result["ts"] = posted.get("ts")
    return result


def _bot_user_id(transport) -> str:
    payload = transport("auth.test", {})
    user_id = payload.get("user_id")
    if not user_id:
        raise RuntimeError("auth.test did not return user_id")
    return str(user_id)


def _reply_text(decision: dict) -> str:
    label = decision["label"] or decision["action"]
    return (
        f"Accepted {label} from a human @mention. "
        "The decision tree runs before any shipment change."
    )


def _unwrap(event: dict) -> dict:
    if event.get("type") == "event_callback" and isinstance(event.get("event"), dict):
        return event["event"]
    return event


def _channel(event: dict) -> str | None:
    channel = event.get("channel")
    if isinstance(channel, dict):
        return channel.get("id")
    if isinstance(channel, str):
        return channel
    return None


def _actor_id(event: dict) -> str | None:
    user = event.get("user")
    if isinstance(user, str):
        return user
    if isinstance(user, dict) and isinstance(user.get("id"), str):
        return user["id"]
    return None


def _authored_by_operations(event: dict, bot_user_id: str | None) -> bool:
    if bot_user_id and _actor_id(event) == bot_user_id:
        return True
    if event.get("subtype") == "bot_message":
        return True
    names = []
    if isinstance(event.get("username"), str):
        names.append(event["username"])
    profile = event.get("bot_profile")
    if isinstance(profile, dict):
        for key in ("name", "username"):
            if isinstance(profile.get(key), str):
                names.append(profile[key])
    return BOT_APP_NAME in names


def _is_report_post(event: dict) -> bool:
    text = event.get("text") or ""
    blocks = event.get("blocks") if isinstance(event.get("blocks"), list) else []
    if _is_parent(text, blocks):
        return True
    return _is_order_or_address(text, _flatten(blocks))


def _is_parent(text: str, blocks: list) -> bool:
    if text.strip().startswith(PARENT_MARK):
        return True
    for block in blocks:
        if not isinstance(block, dict) or block.get("type") != "header":
            continue
        header = (block.get("text") or {}).get("text") or ""
        if PARENT_MARK in header:
            return True
    return False


def _is_order_or_address(text: str, blocks_blob: str) -> bool:
    first = text.strip().split("\n", 1)[0]
    cardish = "View order in ShipMonk" in text or ADDRESS_MARK in text
    if first.startswith("Order #") and cardish:
        return True
    blockish = "View order in ShipMonk" in blocks_blob or ADDRESS_MARK in blocks_blob
    if "*Order #" in blocks_blob and blockish:
        return True
    if first.startswith("Order #") and ADDRESS_MARK in blocks_blob:
        return True
    return False


def _mentions_operations(event: dict, bot_user_id: str | None) -> bool:
    mentions = list(_iter_mentions(event))
    if bot_user_id:
        return any(user_id == bot_user_id for user_id, _label in mentions)
    if event.get("type") == "app_mention":
        return True
    return any(label.strip() == BOT_APP_NAME for _user_id, label in mentions)


def _iter_mentions(value):
    if isinstance(value, str):
        for match in MENTION_RE.finditer(value):
            yield match.group(1), match.group(2) or ""
        return
    if isinstance(value, dict):
        if value.get("type") == "user" and isinstance(value.get("user_id"), str):
            yield value["user_id"], ""
        for item in value.values():
            yield from _iter_mentions(item)
        return
    if isinstance(value, list):
        for item in value:
            yield from _iter_mentions(item)


def _map_label(text: str, thread_ts: str | None):
    cleaned = " ".join(MENTION_RE.sub(" ", text).split())
    for label, action in ACTION_LABELS:
        if cleaned == label:
            if not thread_ts:
                return None
            return action, label, str(thread_ts)
    parts = cleaned.split(" ", 1)
    if len(parts) == 2 and TS_RE.fullmatch(parts[0]):
        for label, action in ACTION_LABELS:
            if parts[1] == label:
                return action, label, parts[0]
    return None


def _map_button(event: dict) -> dict:
    actions = event.get("actions") if isinstance(event.get("actions"), list) else []
    message = event.get("message") if isinstance(event.get("message"), dict) else {}
    if len(actions) != 1:
        return _decision(reason="not_an_action")
    action = actions[0]
    action_id = action.get("action_id")
    if action_id not in BUTTON_ACTIONS:
        return _decision(reason="not_an_action")
    if not message.get("ts") or not message.get("thread_ts"):
        return _decision(reason="not_an_action")
    try:
        value = json.loads(action.get("value") or "")
    except (TypeError, json.JSONDecodeError):
        return _decision(reason="not_an_action")
    if not isinstance(value, dict):
        return _decision(reason="not_an_action")
    if value.get("v") != 1 or value.get("action") != action_id:
        return _decision(reason="not_an_action")
    store_id = str(value.get("store_id") or "")
    if store_id not in ALLOWED_STORES or not value.get("order_key"):
        return _decision(reason="not_an_action")
    label = next(name for name, mapped in ACTION_LABELS if mapped == action_id)
    return _decision(
        action=action_id,
        label=label,
        order_ts=str(message["ts"]),
        thread_ts=str(message["ts"]),
        order_key=str(value["order_key"]),
        store_id=store_id,
    )


def _decision(
    *,
    action: str | None = None,
    label: str | None = None,
    order_ts: str | None = None,
    thread_ts: str | None = None,
    reason: str | None = None,
    order_key: str | None = None,
    store_id: str | None = None,
) -> dict:
    return {
        "action": action,
        "label": label,
        "order_ts": order_ts,
        "thread_ts": thread_ts,
        "reason": reason,
        "order_key": order_key,
        "store_id": store_id,
        "app_name": BOT_APP_NAME,
    }


def _flatten(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return "\n".join(_flatten(item) for item in value.values())
    if isinstance(value, list):
        return "\n".join(_flatten(item) for item in value)
    return ""
