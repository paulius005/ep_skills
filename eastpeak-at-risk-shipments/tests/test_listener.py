"""Listener tests. They never call Slack and never print a bot token."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from slack_poster.blocks import plan_messages, report_from_dict  # noqa: E402
from slack_poster.post import TOKEN_ENV, UrllibSlackTransport  # noqa: E402
from slack_listener import BOT_APP_NAME, classify, listen  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
BOT_USER = "UBOT"
HUMAN = "UHUMAN"
PARENT_TS = "1700000000.000100"
ORDER_TS = "1700000000.000200"


def load(name: str):
    return report_from_dict(json.loads((FIXTURES / name).read_text(encoding="utf-8")))


def posted_event(message, ts, thread_ts=None, **extra):
    event = {
        "type": "message",
        "channel": "C0CCJJGG6HK",
        "user": BOT_USER,
        "bot_id": "BBOT",
        "username": BOT_APP_NAME,
        "bot_profile": {"id": "BBOT", "name": BOT_APP_NAME},
        "subtype": "bot_message",
        "ts": ts,
        "text": message.text,
        "blocks": message.blocks,
    }
    if thread_ts:
        event["thread_ts"] = thread_ts
    event.update(extra)
    return event


def human_reply(text, **extra):
    event = {
        "type": "message",
        "channel": "C0CCJJGG6HK",
        "user": HUMAN,
        "ts": "1700000001.000300",
        "thread_ts": ORDER_TS,
        "text": text,
    }
    event.update(extra)
    return event


class ListenerTests(unittest.TestCase):
    def setUp(self):
        self._token = os.environ.pop(TOKEN_ENV, None)

    def tearDown(self):
        if self._token is None:
            os.environ.pop(TOKEN_ENV, None)
        else:
            os.environ[TOKEN_ENV] = self._token

    def test_bot_card_is_not_an_action_and_a_human_mention_is(self):
        report = load("address_and_returned.json")
        planned = plan_messages(report)
        parent, order, address, returned = planned
        self.assertEqual(
            [message.kind for message in planned],
            ["parent", "order", "address", "order"],
        )
        cards = [
            posted_event(parent, PARENT_TS),
            posted_event(order, ORDER_TS, PARENT_TS),
            posted_event(address, "1700000000.000250", PARENT_TS),
            posted_event(returned, "1700000000.000260", PARENT_TS),
        ]
        calls = []

        def transport(method, body):
            calls.append(method)
            raise AssertionError(method)

        for card in cards:
            decision = listen(card, bot_user_id=BOT_USER, transport=transport, post=True)
            self.assertIsNone(decision["action"])
            self.assertIn(decision["reason"], {"bot", "report_post"})
            self.assertFalse(decision["posted"])
        self.assertEqual(calls, [])

        # The returned card says "Draft an email to the customer." A human
        # mention of the real label still maps; the card itself did not.
        self.assertIn("Draft an email to the customer.", returned.text)
        human = listen(
            human_reply(f"<@{BOT_USER}> Draft an email to the customer"),
            bot_user_id=BOT_USER,
            post=False,
        )
        self.assertEqual(human["action"], "draft_address_check")
        self.assertEqual(human["order_ts"], ORDER_TS)
        self.assertFalse(human["posted"])
        self.assertEqual(human["app_name"], BOT_APP_NAME)

    def test_each_bot_identity_and_the_report_shape_are_ignored(self):
        text = f"<@{BOT_USER}> USPS Priority"
        identities = [
            {"user": BOT_USER, "text": text},
            {"subtype": "bot_message", "user": "UOTHER", "text": text},
            {"username": BOT_APP_NAME, "user": "UOTHER", "text": text},
            {
                "user": "UOTHER",
                "bot_profile": {"name": BOT_APP_NAME},
                "text": text,
            },
        ]
        for extra in identities:
            event = human_reply("USPS Priority")
            event.update(extra)
            decision = classify(event, bot_user_id=BOT_USER)
            self.assertIsNone(decision["action"], extra)
            self.assertEqual(decision["reason"], "bot")

        bare_card = {
            "type": "message",
            "channel": "C0CCJJGG6HK",
            "user": "UOTHER",
            "ts": ORDER_TS,
            "thread_ts": PARENT_TS,
            "text": "\n".join([
                "Order #8257",
                "At risk",
                "In transit → Hawaii",
                "USPS Priority Mail",
                "Draft an email to the customer.",
                "View order in ShipMonk: https://app.shipmonk.com/orders/lookup/19002/x",
                "Store 19002 · Fulfilled",
            ]),
        }
        self.assertIsNone(classify(bare_card)["action"])
        self.assertEqual(classify(bare_card)["reason"], "report_post")

        parent = {
            "type": "message",
            "channel": "C0CCJJGG6HK",
            "ts": PARENT_TS,
            "text": "At-risk shipments · Oct 30\n2 flagged orders shown",
        }
        self.assertEqual(classify(parent)["reason"], "report_post")

        address = plan_messages(load("address_and_returned.json"))[2]
        bare_address = posted_event(address, "1700000000.000250", PARENT_TS)
        bare_address.pop("subtype")
        bare_address.pop("username")
        bare_address.pop("bot_profile")
        bare_address["user"] = "UOTHER"
        self.assertEqual(classify(bare_address)["reason"], "report_post")

    def test_mention_is_required_before_an_action(self):
        unlabeled = classify(human_reply("USPS Priority"), bot_user_id=BOT_USER)
        self.assertIsNone(unlabeled["action"])
        self.assertEqual(unlabeled["reason"], "no_mention")

        other_person = classify(
            human_reply("<@UOTHER> USPS Priority"),
            bot_user_id=BOT_USER,
        )
        self.assertEqual(other_person["reason"], "no_mention")

        channel_message = human_reply(
            f"<@{BOT_USER}> USPS Priority",
            thread_ts=None,
        )
        channel_message.pop("thread_ts")
        # No order thread, so this is not a shipment action. It is still a reply.
        unbound = classify(channel_message, bot_user_id=BOT_USER)
        self.assertEqual(unbound["action"], "conversation")
        self.assertEqual(unbound["label"], "USPS Priority")

        mentioned = classify(
            human_reply(f"<@{BOT_USER}> USPS Priority"),
            bot_user_id=BOT_USER,
        )
        self.assertEqual(mentioned["action"], "usps_priority")
        self.assertEqual(mentioned["label"], "USPS Priority")

        named = classify(
            human_reply("<@U12345|East Peak Operations> guarded clone and submit"),
        )
        self.assertEqual(named["action"], "guarded_clone_and_submit")

        same_thread = classify(
            human_reply(
                f"<@{BOT_USER}> {ORDER_TS} unsent Gmail draft",
                thread_ts=PARENT_TS,
            ),
            bot_user_id=BOT_USER,
        )
        self.assertEqual(same_thread["action"], "unsent_gmail_draft")
        self.assertEqual(same_thread["order_ts"], ORDER_TS)

        self_mention = classify(
            human_reply(f"<@{BOT_USER}> USPS Priority", user=BOT_USER),
            bot_user_id=BOT_USER,
        )
        self.assertEqual(self_mention["reason"], "bot")

        resolved = classify(
            human_reply(f"<@{BOT_USER}> resolve as undeliverable"),
            bot_user_id=BOT_USER,
        )
        self.assertEqual(resolved["action"], "resolve_as_undeliverable")
        self.assertEqual(resolved["label"], "resolve as undeliverable")
        self.assertEqual(resolved["order_ts"], ORDER_TS)

        learn = classify(
            human_reply(
                f"<@{BOT_USER}> For 8257 figure out resolve as undeliverable via API and adjust your skill"
            ),
            bot_user_id=BOT_USER,
        )
        self.assertEqual(learn["action"], "conversation")
        self.assertEqual(learn["reason"], "conversation")

    def test_a_question_is_a_conversation_and_does_not_post_a_stock_line(self):
        question = human_reply(
            f"<@{BOT_USER}>  for 8257 can you show me the draft?",
            thread_ts=PARENT_TS,
        )
        decision = classify(question, bot_user_id=BOT_USER)
        self.assertEqual(decision["action"], "conversation")
        self.assertEqual(decision["label"], "for 8257 can you show me the draft?")
        self.assertEqual(decision["thread_ts"], PARENT_TS)
        self.assertEqual(decision["reason"], "conversation")

        calls = []

        def transport(method, body):
            calls.append(method)
            raise AssertionError(method)

        result = listen(question, bot_user_id=BOT_USER, transport=transport, post=True)
        self.assertEqual(result["action"], "conversation")
        self.assertFalse(result["posted"])
        self.assertEqual(calls, [])

        blank = classify(human_reply(f"<@{BOT_USER}>"), bot_user_id=BOT_USER)
        self.assertIsNone(blank["action"])
        self.assertEqual(blank["reason"], "not_an_action")

    def test_a_skill_change_about_drafts_is_a_conversation(self):
        ask = human_reply(
            f"<@{BOT_USER}> Please adjust your skill so you don't refuse a reply. "
            "Check the shipment and ask if you are not sure why a draft is needed."
        )
        decision = classify(ask, bot_user_id=BOT_USER)
        self.assertEqual(decision["action"], "conversation")
        self.assertEqual(decision["reason"], "conversation")
        result = listen(ask, bot_user_id=BOT_USER, post=False)
        self.assertFalse(result["posted"])

    def test_a_signature_change_is_a_conversation_and_the_template_signs_george(self):
        ask = human_reply(
            f"<@{BOT_USER}> Are all of your skill updates merged? "
            "Also adjust yourself so you sign the emails,\n\nBest,\nGeorge\n\nNot East Peak"
        )
        decision = classify(ask, bot_user_id=BOT_USER)
        self.assertEqual(decision["action"], "conversation")
        self.assertEqual(decision["reason"], "conversation")
        result = listen(ask, bot_user_id=BOT_USER, post=False)
        self.assertFalse(result["posted"])
        reference = (
            Path(__file__).resolve().parents[1] / "references" / "slack-listener.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Best,\nGeorge", reference)
        self.assertNotIn("Sign `Thanks for your help!` then `East Peak`.", reference)

    def test_reply_posts_as_the_same_app_and_does_not_print_the_token(self):
        token = "xoxb-listener-test-value"
        calls = []

        def opener(request, timeout):
            calls.append({
                "url": request.full_url,
                "auth": request.get_header("Authorization"),
                "body": request.data.decode("utf-8"),
            })
            method = request.full_url.rsplit("/", 1)[-1]
            if method == "auth.test":
                raw = b'{"ok": true, "user_id": "UBOT", "bot_id": "BBOT"}'
            else:
                raw = b'{"ok": true, "ts": "1700000002.000400"}'

            class Response:
                def read(self):
                    return raw

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    return False

            return Response()

        transport = UrllibSlackTransport(token, opener=opener)
        result = listen(
            human_reply(f"<@{BOT_USER}> USPS Priority"),
            transport=transport,
            token=token,
            post=True,
        )
        self.assertEqual(result["action"], "usps_priority")
        self.assertTrue(result["posted"])
        self.assertEqual(result["ts"], "1700000002.000400")
        self.assertEqual(
            [call["url"] for call in calls],
            ["https://slack.com/api/auth.test", "https://slack.com/api/chat.postMessage"],
        )
        reply = json.loads(calls[1]["body"])
        self.assertEqual(reply["channel"], "C0CCJJGG6HK")
        self.assertEqual(reply["thread_ts"], ORDER_TS)
        self.assertNotIn("username", reply)
        self.assertNotIn(token, calls[1]["body"])
        self.assertNotIn(token, calls[0]["body"])
        self.assertEqual(calls[0]["auth"], "Bearer " + token)
        self.assertNotIn(token, json.dumps(result))
        self.assertEqual(result["app_name"], BOT_APP_NAME)

        before = len(calls)
        echo = listen(
            {
                "type": "message",
                "channel": "C0CCJJGG6HK",
                "user": BOT_USER,
                "ts": "1700000002.000400",
                "thread_ts": ORDER_TS,
                "text": reply["text"],
            },
            transport=transport,
            bot_user_id=BOT_USER,
            post=True,
        )
        self.assertIsNone(echo["action"])
        self.assertFalse(echo["posted"])
        self.assertEqual(len(calls), before)

        with mock.patch("urllib.request.urlopen", side_effect=AssertionError("network")):
            with self.assertRaises(RuntimeError) as caught:
                listen(
                    human_reply(f"<@{BOT_USER}> USPS Priority"),
                    bot_user_id=BOT_USER,
                    post=True,
                )
        self.assertIn(TOKEN_ENV, str(caught.exception))
        self.assertNotIn("xoxb", str(caught.exception))

    def test_human_button_on_a_bot_card_still_maps(self):
        card = plan_messages(load("in_transit.json"))[1]
        payload = {
            "type": "block_actions",
            "user": {"id": HUMAN, "name": "A person"},
            "channel": {"id": "C0CCJJGG6HK"},
            "message": {
                "ts": ORDER_TS,
                "thread_ts": PARENT_TS,
                "user": BOT_USER,
                "bot_profile": {"name": BOT_APP_NAME},
                "text": card.text,
                "blocks": card.blocks,
            },
            "actions": [
                {
                    "type": "button",
                    "action_id": "usps_priority",
                    "value": json.dumps({
                        "v": 1,
                        "action": "usps_priority",
                        "store_id": "19002",
                        "order_key": "18927830040707",
                    }),
                }
            ],
        }
        decision = classify(payload, bot_user_id=BOT_USER)
        self.assertEqual(decision["action"], "usps_priority")
        self.assertEqual(decision["order_key"], "18927830040707")

        payload["user"] = {"id": BOT_USER, "name": BOT_APP_NAME}
        self.assertEqual(classify(payload, bot_user_id=BOT_USER)["reason"], "bot")

    def test_cli_no_post_does_not_send_a_stock_line(self):
        event = {
            "type": "message",
            "channel": "C0CCJJGG6HK",
            "user": HUMAN,
            "ts": "1700000000.000300",
            "thread_ts": PARENT_TS,
            "text": f"<@{BOT_USER}|{BOT_APP_NAME}> please show the wording",
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
            json.dump(event, handle)
            event_path = handle.name
        env = os.environ.copy()
        env.pop("SLACK_BOT_TOKEN", None)
        env.pop("SHIPMONK_API_KEY", None)
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "slack_listener",
                "--event",
                str(event_path),
                "--no-post",
            ],
            cwd=Path(__file__).resolve().parents[1],
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(completed.stdout)
        self.assertFalse(result["posted"])
        self.assertEqual(result["action"], "conversation")
        self.assertEqual(result["reason"], "conversation")
        self.assertEqual(result["thread_ts"], PARENT_TS)
        self.assertEqual(completed.stderr, "")

    def test_free_text_mention_is_a_conversation_and_does_not_stock_post(self):
        decision = classify(
            human_reply(f"<@{BOT_USER}> can you show me the draft for 8257?"),
            bot_user_id=BOT_USER,
        )
        self.assertEqual(decision["action"], "conversation")
        self.assertEqual(decision["reason"], "conversation")
        self.assertEqual(decision["thread_ts"], ORDER_TS)

        transport_calls = []

        def transport(method, body):
            transport_calls.append(method)
            return {"ok": True, "ts": "1700000000.000900"}

        result = listen(
            human_reply(f"<@{BOT_USER}> please change the wording"),
            bot_user_id=BOT_USER,
            transport=transport,
            post=True,
        )
        self.assertEqual(result["reason"], "conversation")
        self.assertFalse(result["posted"])
        self.assertEqual(transport_calls, [])

    def test_parent_card_without_mention_posts_nothing_and_mention_uses_bot_token(self):
        calls = []

        def reject(method, body):
            calls.append(method)
            raise AssertionError(method)

        parents = [
            {
                "type": "message",
                "channel": "C0CCJJGG6HK",
                "user": "UOTHER",
                "ts": "1793481649.569669",
                "text": "At-risk shipments · Oct 31",
            },
            {
                "type": "message",
                "channel": "C0CCJJGG6HK",
                "ts": "1793485200.000100",
                "text": "At-risk shipments · Oct 31\n2 flagged orders shown",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": ":warning: At-risk shipments · Oct 31",
                        },
                    }
                ],
            },
        ]
        for parent in parents:
            decision = listen(parent, bot_user_id=BOT_USER, transport=reject, post=True)
            self.assertIsNone(decision["action"])
            self.assertFalse(decision["posted"])
            self.assertNotIn("<@", parent["text"])
            self.assertIn(decision["reason"], {"report_post", "no_mention", "bot"})
        self.assertEqual(calls, [])

        token = "xoxb-mention-path-test"
        seen = []

        def opener(request, timeout):
            seen.append({
                "url": request.full_url,
                "auth": request.get_header("Authorization"),
                "body": request.data.decode("utf-8"),
            })
            method = request.full_url.rsplit("/", 1)[-1]
            raw = (
                b'{"ok": true, "user_id": "UBOT"}'
                if method == "auth.test"
                else b'{"ok": true, "ts": "1793485300.000200"}'
            )

            class Response:
                def read(self):
                    return raw

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    return False

            return Response()

        transport = UrllibSlackTransport(token, opener=opener)
        mentioned = listen(
            human_reply(f"<@{BOT_USER}> USPS Priority"),
            transport=transport,
            token=token,
            post=True,
        )
        self.assertEqual(mentioned["action"], "usps_priority")
        self.assertTrue(mentioned["posted"])
        self.assertEqual(
            [item["url"] for item in seen],
            ["https://slack.com/api/auth.test", "https://slack.com/api/chat.postMessage"],
        )
        reply = json.loads(seen[1]["body"])
        self.assertEqual(reply["channel"], "C0CCJJGG6HK")
        self.assertEqual(reply["thread_ts"], ORDER_TS)
        self.assertNotIn("username", reply)
        self.assertNotIn("blocks", reply)
        self.assertEqual(seen[1]["auth"], "Bearer " + token)
        self.assertNotIn(token, seen[1]["body"])
        self.assertNotIn(token, json.dumps(mentioned))
        self.assertNotIn("No changes made", reply["text"])


if __name__ == "__main__":
    unittest.main()
