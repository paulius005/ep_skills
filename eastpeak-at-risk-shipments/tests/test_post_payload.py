"""Functional tests for the poster. They assert payloads and never call Slack."""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from slack_poster.blocks import conversation_blocks, plan_messages, report_from_dict  # noqa: E402
from slack_poster.post import (  # noqa: E402
    SlackAPIError,
    UrllibSlackTransport,
    post_reply,
    post_report,
    post_thread_reply,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
ROOT = Path(__file__).resolve().parents[1]
STREET2_61 = "Guest: Tyler Maher, staying from 5th November - 11th November"
HIDDEN = (
    "buyer-8257@example.com",
    "buyer-8274@example.com",
    "buyer-8376@example.com",
    "555-0101",
    "555-0102",
    "555-0199",
    "100 Example Ave",
    "200 Example Ave",
    "300 Example Ave",
)


def load(name: str):
    return report_from_dict(json.loads((FIXTURES / name).read_text(encoding="utf-8")))


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from strings(item)
    elif hasattr(value, "__dataclass_fields__"):
        for item in vars(value).values():
            yield from strings(item)


class RecordingTransport:
    def __init__(self):
        self.calls = []
        self._n = 0

    def __call__(self, method, body):
        self.calls.append((method, json.loads(json.dumps(body))))
        self._n += 1
        return {"ok": True, "ts": f"1700000000.000{self._n}", "channel": body.get("channel")}


class PayloadTests(unittest.TestCase):
    def test_fixture_payloads_for_address_and_returned_orders(self):
        report = load("address_and_returned.json")
        self.assertEqual(len(report.shipments[0].street2), 61)
        messages = plan_messages(report)
        self.assertEqual(
            [(message.kind, message.order_number) for message in messages],
            [("parent", None), ("order", "8376"), ("address", "8376"), ("order", "8257")],
        )
        blob = "\n".join(strings([message.as_dict() for message in messages]))
        for hidden in HIDDEN:
            self.assertNotIn(hidden, blob)
        self.assertIn("At-risk shipments · Oct 30", blob)
        self.assertIn("*Before:* " + STREET2_61, blob)
        self.assertIn("*After:* Guest: Tyler Maher", blob)
        self.assertNotIn(STREET2_61, "\n".join(strings(messages[1].blocks)))

        returned = messages[3]
        self.assertIn("USPS Priority Mail", returned.text)
        self.assertIn("Draft an email to the customer.", returned.text)
        self.assertIn("*In transit → Hawaii*", returned.blocks[0]["text"]["text"])
        actions = [block for block in returned.blocks if block["type"] == "actions"]
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["elements"][0]["action_id"], "draft_address_check")
        self.assertNotIn("usps_priority", json.dumps(returned.blocks))
        card_8376 = messages[1].blocks
        self.assertNotIn("actions", [block["type"] for block in card_8376])
        self.assertIn("Not set (requested Standard)", messages[1].text)
        self.assertIn("Store 19002 · Unfulfilled", messages[1].text)

    def test_post_records_chat_post_message_without_network(self):
        report = load("address_and_returned.json")
        transport = RecordingTransport()
        with mock.patch("urllib.request.urlopen", side_effect=AssertionError("network")):
            result = post_report(report, transport=transport)
        self.assertFalse(result["dry_run"])
        methods = [method for method, _body in transport.calls]
        self.assertEqual(methods, [
            "chat.postMessage",
            "chat.update",
            "chat.postMessage",
            "chat.postMessage",
            "chat.postMessage",
        ])
        parent_body = transport.calls[0][1]
        self.assertEqual(parent_body["channel"], "C0CCJJGG6HK")
        self.assertNotIn("thread_ts", parent_body)
        self.assertIn("blocks", parent_body)
        self.assertIn("At-risk shipments · Oct 30", parent_body["text"])
        update = transport.calls[1][1]
        self.assertEqual(update["ts"], result["parent_ts"])
        self.assertIn(result["permalink"], update["blocks"][3]["text"]["text"])
        self.assertIn("2 order details in thread →", update["blocks"][3]["text"]["text"])
        self.assertIn("1 of 2 orders shown are already in transit.", update["text"])
        self.assertIn("1 in transit · 0 service changes", update["text"])
        for method, body in transport.calls[2:]:
            self.assertEqual(method, "chat.postMessage")
            self.assertEqual(body["thread_ts"], result["parent_ts"])
            self.assertEqual(body["channel"], "C0CCJJGG6HK")
        posted = "\n".join(strings([call[1] for call in transport.calls]))
        for hidden in HIDDEN:
            self.assertNotIn(hidden, posted)
        self.assertIn(STREET2_61, transport.calls[3][1]["text"])
        self.assertNotIn(STREET2_61, transport.calls[2][1]["text"])
        draft = transport.calls[4][1]
        self.assertIn("draft_address_check", json.dumps(draft["blocks"]))
        self.assertNotIn("usps_priority", json.dumps(draft["blocks"]))

    def test_screenshot_orders_post_the_target_copy(self):
        report = load("in_transit.json")
        transport = RecordingTransport()
        post_report(report, transport=transport)
        update = transport.calls[1][1]
        self.assertEqual(
            update["blocks"][0]["text"]["text"],
            ":warning: At-risk shipments · Oct 30",
        )
        self.assertEqual(
            update["blocks"][1]["text"]["text"],
            "Both orders shown are already in transit.\n"
            "Shipping services were left unchanged.",
        )
        quote = update["blocks"][2]["elements"][0]["elements"]
        self.assertEqual(quote[0]["text"], "2 flagged orders shown")
        self.assertEqual(quote[1]["text"], "\n2 in transit · 0 service changes")
        hawaii = transport.calls[2][1]
        california = transport.calls[3][1]
        self.assertIn("*In transit → Hawaii*", hawaii["blocks"][0]["text"]["text"])
        self.assertIn("USPS Priority Mail", hawaii["blocks"][0]["text"]["text"])
        self.assertIn("*In transit → California*", california["blocks"][0]["text"]["text"])
        self.assertIn("ShipMonk Standard", california["blocks"][0]["text"]["text"])
        for body in (hawaii, california):
            self.assertEqual(
                body["blocks"][1]["elements"][0]["text"],
                "Service unchanged — shipment already en route.",
            )
            self.assertEqual(body["blocks"][-1]["elements"][0]["text"], "Store 19002 · Fulfilled")
            self.assertNotIn("actions", [block["type"] for block in body["blocks"]])

    def test_urllib_transport_targets_chat_post_message_and_keeps_the_token_out_of_the_body(self):
        captured = {}

        class Response:
            def read(self):
                return b'{"ok": true, "ts": "1.2"}'

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def opener(request, timeout):
            captured["url"] = request.full_url
            captured["auth"] = request.get_header("Authorization")
            captured["body"] = request.data.decode("utf-8")
            captured["timeout"] = timeout
            return Response()

        token = "xoxb-test-token-not-a-secret"
        transport = UrllibSlackTransport(token, opener=opener)
        transport("chat.postMessage", {"channel": "C0CCJJGG6HK", "text": "fallback", "blocks": []})
        self.assertEqual(captured["url"], "https://slack.com/api/chat.postMessage")
        self.assertEqual(captured["auth"], "Bearer " + token)
        self.assertNotIn(token, captured["body"])
        self.assertEqual(json.loads(captured["body"])["text"], "fallback")

        def denied(request, timeout):
            class Denied:
                def read(self):
                    return b'{"ok": false, "error": "invalid_auth"}'

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    return False

            return Denied()

        transport = UrllibSlackTransport(token, opener=denied)
        with self.assertRaises(SlackAPIError) as caught:
            transport("chat.postMessage", {"text": "fallback"})
        self.assertNotIn(token, str(caught.exception))
        self.assertIn("invalid_auth", str(caught.exception))

    def test_dry_run_does_not_read_the_token_or_open_the_network(self):
        report = load("in_transit.json")
        previous = os.environ.get("SLACK_BOT_TOKEN")
        os.environ["SLACK_BOT_TOKEN"] = "xoxb-dry-run-must-not-leak"
        try:
            with mock.patch("urllib.request.urlopen", side_effect=AssertionError("network")):
                result = post_report(report, dry_run=True)
        finally:
            if previous is None:
                os.environ.pop("SLACK_BOT_TOKEN", None)
            else:
                os.environ["SLACK_BOT_TOKEN"] = previous
        self.assertTrue(result["dry_run"])
        self.assertNotIn("xoxb-dry-run-must-not-leak", json.dumps(result))
        self.assertGreaterEqual(len(result["messages"]), 3)

    def test_missing_token_names_the_env_var_and_does_not_call_slack(self):
        report = load("in_transit.json")
        previous = os.environ.pop("SLACK_BOT_TOKEN", None)
        try:
            with mock.patch("urllib.request.urlopen", side_effect=AssertionError("network")):
                with self.assertRaises(RuntimeError) as caught:
                    post_report(report)
        finally:
            if previous is not None:
                os.environ["SLACK_BOT_TOKEN"] = previous
        self.assertIn("SLACK_BOT_TOKEN", str(caught.exception))

    def test_cli_dry_run_prints_fixture_payloads(self):
        env = os.environ.copy()
        env.pop("SLACK_BOT_TOKEN", None)
        env["PYTHONPATH"] = str(ROOT)
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "slack_poster",
                "--dry-run",
                "--report",
                str(FIXTURES / "address_and_returned.json"),
            ],
            cwd=ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload[0]["kind"], "parent")
        self.assertIn("At-risk shipments · Oct 30", payload[0]["text"])
        self.assertEqual(payload[2]["kind"], "address")
        self.assertIn(STREET2_61, payload[2]["text"])
        self.assertIn("Guest: Tyler Maher", payload[2]["text"])
        for hidden in HIDDEN:
            self.assertNotIn(hidden, completed.stdout)
        self.assertEqual(completed.stderr, "")

    def test_thread_reply_passes_blocks_and_sets_no_username(self):
        text, blocks = conversation_blocks(
            "The unsent draft for order 8257 is ready for review.",
            ["Not sent."],
            "The draft email is in your inbox.",
        )
        transport = RecordingTransport()
        result = post_thread_reply(
            channel_id="C0CCJJGG6HK",
            thread_ts="1700000000.000100",
            text=text,
            blocks=blocks,
            transport=transport,
        )
        self.assertEqual(result["ts"], "1700000000.0001")
        method, body = transport.calls[0]
        self.assertEqual(method, "chat.postMessage")
        self.assertEqual(body["channel"], "C0CCJJGG6HK")
        self.assertEqual(body["thread_ts"], "1700000000.000100")
        self.assertEqual(body["blocks"], blocks)
        self.assertNotIn("username", body)
        with self.assertRaises(RuntimeError):
            post_thread_reply(
                channel_id="C0OTHER",
                thread_ts="1700000000.000100",
                text="No.",
                blocks=blocks,
                transport=transport,
            )

    def test_conversation_reply_is_a_bold_lead_with_bullets(self):
        text, blocks = conversation_blocks(
            "I updated how I reply.",
            [
                "A question gets an answer.",
                "A request to adjust me updates the skill.",
            ],
            "The shipment was not changed.",
        )
        self.assertEqual(blocks[0]["text"]["text"], "*I updated how I reply.*")
        self.assertIn("• A question gets an answer.", blocks[1]["text"]["text"])
        self.assertEqual(blocks[2]["type"], "context")
        self.assertLessEqual(len(blocks[2]["elements"][0]["text"]), 75)
        self.assertIn("I updated how I reply.", text)

        calls = []

        def transport(method, body):
            calls.append((method, body))
            return {"ok": True, "ts": "1700000003.000500"}

        result = post_reply("1700000000.000100", text, blocks, transport=transport)
        self.assertTrue(result["posted"])
        self.assertEqual(result["ts"], "1700000003.000500")
        method, body = calls[0]
        self.assertEqual(method, "chat.postMessage")
        self.assertEqual(body["channel"], "C0CCJJGG6HK")
        self.assertEqual(body["thread_ts"], "1700000000.000100")
        self.assertNotIn("username", body)
        self.assertEqual(body["blocks"], blocks)


if __name__ == "__main__":
    unittest.main()
