"""Unit tests for the Block Kit builder. No Slack network."""

import json
import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from slack_poster.blocks import (  # noqa: E402
    ADDRESS_LINE_LIMIT,
    CLONED_RESOLVE_ACTION,
    Shipment,
    address_section_text,
    context_line,
    conversation_blocks,
    conversation_fallback,
    format_header_date,
    order_blocks,
    pacific_calendar_date,
    parent_blocks,
    parent_header,
    plan_messages,
    report_from_dict,
    show_draft_button,
    show_usps_button,
    truncate_address_line2,
    truncate_display,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
STREET2_61 = "Guest: Tyler Maher, staying from 5th November - 11th November"


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


def joined(value) -> str:
    return "\n".join(strings(value))


def load(name: str):
    return report_from_dict(json.loads((FIXTURES / name).read_text(encoding="utf-8")))


def shipment(**overrides) -> Shipment:
    data = dict(
        order_number="8257",
        store_id="19002",
        order_key="18927830040707",
        order_status="fulfilled",
        processing_status="en_route",
        state="HI",
        flags=["at_risk"],
        service="USPS Priority Mail",
        editable=False,
        email="buyer-8257@example.com",
        phone="555-0101",
        street1="100 Example Ave",
    )
    data.update(overrides)
    return Shipment(**data)


class LayoutTests(unittest.TestCase):
    def test_parent_matches_target_hierarchy(self):
        report = load("in_transit.json")
        blocks = parent_blocks(report)
        self.assertEqual(
            [block["type"] for block in blocks],
            ["header", "section", "rich_text", "section"],
        )
        self.assertEqual(
            blocks[0]["text"]["text"],
            ":warning: At-risk shipments · Oct 30",
        )
        self.assertEqual(
            blocks[1]["text"]["text"],
            "Both orders shown are already in transit.\n"
            "Shipping services were left unchanged.",
        )
        quote = blocks[2]["elements"][0]
        self.assertEqual(quote["type"], "rich_text_quote")
        self.assertEqual(quote["elements"][0]["text"], "2 flagged orders shown")
        self.assertTrue(quote["elements"][0]["style"]["bold"])
        self.assertEqual(quote["elements"][1]["text"], "\n2 in transit · 0 service changes")
        self.assertEqual(blocks[3]["text"]["text"], "2 order details in thread →")

    def test_parent_link_uses_permalink_when_known(self):
        report = load("in_transit.json")
        link = "https://east-peak-workspace.slack.com/archives/C0CCJJGG6HK/p1"
        text = parent_blocks(report, link)[3]["text"]["text"]
        self.assertEqual(text, f"<{link}|2 order details in thread →>")

    def test_in_transit_order_card_hierarchy(self):
        report = load("in_transit.json")
        messages = [message for message in plan_messages(report) if message.kind == "order"]
        self.assertEqual([message.order_number for message in messages], ["8257", "8274"])
        first, second = messages
        self.assertEqual(
            [block["type"] for block in first.blocks],
            ["section", "context", "section", "context"],
        )
        body = first.blocks[0]["text"]["text"]
        self.assertIn("*Order #8257*  `At risk`", body)
        self.assertIn("*In transit → Hawaii*", body)
        self.assertIn("USPS Priority Mail", body)
        self.assertEqual(
            first.blocks[1]["elements"][0]["text"],
            "Service unchanged — shipment already en route.",
        )
        self.assertIn("View order in ShipMonk ↗", first.blocks[2]["text"]["text"])
        self.assertIn("18927830040707", first.blocks[2]["text"]["text"])
        self.assertEqual(first.blocks[3]["elements"][0]["text"], "Store 19002 · Fulfilled")
        self.assertNotIn("actions", [block["type"] for block in first.blocks])

        other = second.blocks[0]["text"]["text"]
        self.assertIn("*Order #8274*  `At risk`", other)
        self.assertIn("*In transit → California*", other)
        self.assertIn("ShipMonk Standard", other)
        self.assertEqual(
            second.blocks[1]["elements"][0]["text"],
            "Service unchanged — shipment already en route.",
        )
        self.assertEqual(second.blocks[3]["elements"][0]["text"], "Store 19002 · Fulfilled")

    def test_cloned_order_asks_a_person_to_resolve_at_risk(self):
        shipment = Shipment(
            order_number="8274",
            store_id="19002",
            order_key="18933995667587",
            order_status="fulfilled",
            processing_status="en_route",
            state="CA",
            flags=["at_risk"],
            service="ShipMonk Standard",
            replacement_pending_resolve=True,
        )
        self.assertEqual(CLONED_RESOLVE_ACTION, "Order has been cloned. Please Resolve At Risk")
        self.assertLessEqual(len(CLONED_RESOLVE_ACTION), 75)
        self.assertEqual(context_line(shipment), CLONED_RESOLVE_ACTION)
        blocks = order_blocks(shipment)
        self.assertEqual(blocks[1]["elements"][0]["text"], CLONED_RESOLVE_ACTION)
        self.assertNotIn("actions", [block["type"] for block in blocks])
        returned = Shipment(
            order_number="8257",
            store_id="19002",
            order_key="18927830040707",
            order_status="fulfilled",
            processing_status="en_route",
            state="HI",
            flags=["at_risk"],
            service="USPS Priority Mail",
            return_status="returned",
            replacement_pending_resolve=True,
        )
        self.assertEqual(context_line(returned), "Draft an email to the customer.")

    def test_context_elements_stay_within_slack_limit(self):
        for name in ("in_transit.json", "address_and_returned.json"):
            for message in plan_messages(load(name)):
                for block in message.blocks:
                    if block["type"] == "context":
                        for element in block["elements"]:
                            self.assertLessEqual(len(element["text"]), 75)


class DateFormatTests(unittest.TestCase):
    def test_header_uses_short_pacific_date(self):
        self.assertEqual(format_header_date(date(2026, 10, 30)), "Oct 30")
        self.assertEqual(format_header_date(date(2026, 1, 5)), "Jan 5")
        self.assertEqual(parent_header(date(2026, 10, 30)), "At-risk shipments · Oct 30")
        header = parent_blocks(load("in_transit.json"))[0]["text"]["text"]
        self.assertNotIn("2026-10-30", header)
        self.assertNotIn("🧵", header)
        self.assertNotIn("At Risk Shipments", header)

    def test_aware_datetime_uses_pacific_calendar(self):
        # 06:30 UTC on Oct 31 is still Oct 30 in Pacific Daylight Time.
        moment = datetime(2026, 10, 31, 6, 30, tzinfo=timezone.utc)
        self.assertEqual(pacific_calendar_date(moment), date(2026, 10, 30))
        later = datetime(2026, 10, 31, 7, 0, tzinfo=timezone.utc)
        self.assertEqual(pacific_calendar_date(later), date(2026, 10, 31))

    def test_naive_datetime_is_rejected(self):
        with self.assertRaises(ValueError):
            pacific_calendar_date(datetime(2026, 10, 30, 12, 0))


class AddressTruncationTests(unittest.TestCase):
    def test_sixty_one_character_guest_line_drops_the_stay_sentence(self):
        self.assertEqual(len(STREET2_61), 61)
        self.assertGreater(len(STREET2_61), ADDRESS_LINE_LIMIT)
        self.assertEqual(truncate_address_line2(STREET2_61), "Guest: Tyler Maher")
        self.assertEqual(len(truncate_address_line2(STREET2_61)), 18)
        self.assertLessEqual(len(truncate_address_line2(STREET2_61)), ADDRESS_LINE_LIMIT)

    def test_line_at_the_limit_is_unchanged(self):
        line = "G" * ADDRESS_LINE_LIMIT
        self.assertEqual(truncate_address_line2(line), line)

    def test_non_guest_line_breaks_on_a_word(self):
        line = "Warehouse dock appointment confirmed for the morning delivery window"
        self.assertGreater(len(line), ADDRESS_LINE_LIMIT)
        shortened = truncate_address_line2(line)
        self.assertLessEqual(len(shortened), ADDRESS_LINE_LIMIT)
        self.assertTrue(line.startswith(shortened))
        self.assertEqual(line[len(shortened)], " ")

    def test_display_truncation_keeps_the_sixty_one_character_line(self):
        self.assertEqual(truncate_display(STREET2_61), STREET2_61)
        long_line = "Guest: Tyler Maher, " + ("stay " * 80)
        shown = truncate_display(long_line)
        self.assertTrue(shown.endswith("…"))
        self.assertLessEqual(len(shown), 300)
        self.assertEqual(truncate_address_line2(long_line), "Guest: Tyler Maher")

    def test_address_section_shows_before_and_after_only(self):
        report = load("address_and_returned.json")
        order = report.shipments[0]
        text = address_section_text(order)
        self.assertIn("*Before:* " + STREET2_61, text)
        self.assertIn("*After:* Guest: Tyler Maher", text)
        self.assertIn("Address 2 is 61 characters. The limit is 50.", text)
        self.assertIn("Do not change the address until this is approved.", text)
        self.assertNotIn(order.email, text)
        self.assertNotIn(order.phone, text)
        self.assertNotIn(order.street1, text)
        messages = plan_messages(report)
        card = next(message for message in messages if message.kind == "order" and message.order_number == "8376")
        address = next(message for message in messages if message.kind == "address")
        self.assertEqual(address.blocks[0]["type"], "section")
        self.assertNotIn(STREET2_61, joined(card.blocks))
        self.assertIn(STREET2_61, joined(address.blocks))
        self.assertEqual(
            card.blocks[1]["elements"][0]["text"],
            "Address 2 exceeded limit of 50 characters.",
        )


class OmissionTests(unittest.TestCase):
    def test_email_phone_and_street_stay_out_of_every_block(self):
        report = load("address_and_returned.json")
        blob = joined(plan_messages(report))
        for shipment in report.shipments:
            self.assertNotIn(shipment.email, blob)
            self.assertNotIn(shipment.phone, blob)
            self.assertNotIn(shipment.street1, blob)
        self.assertNotIn("buyer-", blob)
        self.assertNotIn("555-", blob)

    def test_context_cannot_carry_an_email_or_phone(self):
        order = shipment(context="Email buyer-8257@example.com")
        with self.assertRaises(ValueError):
            context_line(order)


class ButtonVisibilityTests(unittest.TestCase):
    def _actions(self, **overrides):
        blocks = order_blocks(shipment(**overrides))
        actions = [block for block in blocks if block["type"] == "actions"]
        if not actions:
            return []
        return actions[0]["elements"]

    def test_editable_hawaii_gets_usps_priority_only(self):
        buttons = self._actions(
            editable=True,
            processing_status="unable_to_submit",
            order_status="unfulfilled",
            state="HI",
            return_status=None,
        )
        self.assertEqual([button["action_id"] for button in buttons], ["usps_priority"])
        self.assertEqual(buttons[0]["text"]["text"], "USPS Priority")
        value = json.loads(buttons[0]["value"])
        self.assertEqual(value, {
            "v": 1,
            "action": "usps_priority",
            "store_id": "19002",
            "order_key": "18927830040707",
        })
        self.assertTrue(show_usps_button(shipment(
            editable=True, processing_status="unable_to_submit", state="Alaska",
        )))

    def test_returned_hawaii_gets_the_draft_button_not_usps(self):
        buttons = self._actions(
            editable=True,
            processing_status="en_route",
            state="HI",
            service="USPS Priority Mail",
            return_status="returned",
            rma="712-884-506",
        )
        self.assertEqual([button["action_id"] for button in buttons], ["draft_address_check"])
        self.assertEqual(buttons[0]["text"]["text"], "Draft an email to the customer")
        value = json.loads(buttons[0]["value"])
        self.assertEqual(value["v"], 1)
        self.assertEqual(value["action"], "draft_address_check")
        self.assertEqual(value["rma"], "712-884-506")
        self.assertNotIn("email", value)
        self.assertNotIn("phone", value)
        self.assertFalse(show_usps_button(shipment(
            editable=True, state="HI", return_status="returned", rma="712-884-506",
        )))
        self.assertEqual(
            context_line(shipment(return_status="returned", rma="712-884-506")),
            "Draft an email to the customer.",
        )

    def test_saved_draft_omits_the_button(self):
        buttons = self._actions(return_status="returned", rma="712-884-506", draft_saved=True)
        self.assertEqual(buttons, [])
        self.assertEqual(
            context_line(shipment(return_status="returned", rma="712-884-506", draft_saved=True)),
            "The draft email is in your inbox.",
        )

    def test_en_route_packed_and_other_states_hide_usps(self):
        self.assertEqual(self._actions(editable=True, processing_status="en_route", state="HI"), [])
        self.assertEqual(self._actions(
            editable=True, processing_status="packed", state="AK", order_status="fulfilled",
        ), [])
        self.assertEqual(self._actions(
            editable=True, processing_status="unable_to_submit", state="CA",
        ), [])
        self.assertEqual(self._actions(
            editable=False, processing_status="unable_to_submit", state="HI",
        ), [])

    def test_buttons_are_never_combined_and_flavorcloud_is_absent(self):
        buttons = self._actions(
            editable=True,
            processing_status="unable_to_submit",
            state="HI",
            return_status="returned",
            rma="712-884-506",
        )
        self.assertEqual([button["action_id"] for button in buttons], ["draft_address_check"])
        self.assertNotIn("usps_priority", [button["action_id"] for button in buttons])
        blob = joined(order_blocks(shipment(
            editable=True, processing_status="unable_to_submit", state="AK",
        ))).lower()
        self.assertNotIn("flavorcloud", blob)
        self.assertFalse(show_draft_button(shipment()))
        self.assertFalse(show_usps_button(shipment()))


class ConversationTests(unittest.TestCase):
    def test_conversation_is_a_bold_lead_bullets_and_a_short_note(self):
        _text, blocks = conversation_blocks(
            "The unsent draft for order 8257 is ready for review.",
            ["Subject: shipping issue with order: #8257", "Not sent."],
            "The draft email is in your inbox.",
        )
        self.assertEqual([block["type"] for block in blocks], ["section", "section", "context"])
        self.assertEqual(
            blocks[0]["text"]["text"],
            "*The unsent draft for order 8257 is ready for review.*",
        )
        self.assertIn("• Subject: shipping issue with order: #8257", blocks[1]["text"]["text"])
        self.assertLessEqual(len(blocks[2]["elements"][0]["text"]), 75)
        fallback = conversation_fallback(
            "The unsent draft for order 8257 is ready for review.",
            ["Not sent."],
            "The draft email is in your inbox.",
        )
        self.assertNotIn("*", fallback)

    def test_conversation_rejects_a_long_note_and_an_empty_list(self):
        with self.assertRaises(ValueError):
            conversation_blocks("Ready.", ["One"], "x" * 76)
        with self.assertRaises(ValueError):
            conversation_blocks("Ready.", [], "Noted.")
        with self.assertRaises(ValueError):
            conversation_blocks("First line.\nSecond line.", ["One"], "Noted.")


if __name__ == "__main__":
    unittest.main()
