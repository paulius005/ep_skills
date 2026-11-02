"""The awaiting-carrier-processing clock. These tests do not call ShipMonk."""

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from carrier_wait import (  # noqa: E402
    assess_awaiting_carrier_processing,
    at_risk_job_action,
)

NOW = datetime(2026, 11, 2, 2, 47, tzinfo=timezone.utc)
SHIPPED = "2026-10-10T17:57:31+00:00"
PICKUP = "2026-10-11T00:38:00+00:00"
SUBMITTED = "2026-10-10T14:36:00+00:00"
AT_RISK = "2026-10-21T06:35:22+00:00"


def order(**overrides):
    payload = {
        "order_number": "8274",
        "processing_status": "en_route",
        "order_status": "fulfilled",
        "ordered_at": "2026-10-10T14:31:51+00:00",
        "shipped_at": SHIPPED,
        "updated_at": AT_RISK,
        "returns": [],
        "actions_required": {"at_risk": True},
    }
    payload.update(overrides)
    return payload


def logs():
    return [
        {"datetime": AT_RISK, "message": "Order 2228133536 moved to At-Risk."},
        {"datetime": PICKUP, "message": "Marked order 8274 as picked up."},
        {"datetime": SUBMITTED, "message": "Order 2228133536 submitted."},
    ]


class CarrierWaitTests(unittest.TestCase):
    def test_en_route_order_uses_shipped_at_when_logs_are_missing(self):
        result = assess_awaiting_carrier_processing(order(), now=NOW)

        self.assertTrue(result.in_stage)
        self.assertTrue(result.stuck)
        self.assertEqual(result.started_from, "shipped_at")
        self.assertEqual(result.started_at, "2026-10-10T17:57:31+00:00")
        self.assertGreater(result.elapsed_days, 7)
        self.assertNotIn("2026-10-21", result.started_at)

    def test_pickup_log_is_the_clock_and_the_at_risk_row_is_not(self):
        result = assess_awaiting_carrier_processing(order(), now=NOW, logs=logs())

        self.assertTrue(result.stuck)
        self.assertEqual(result.started_from, "pickup_log")
        self.assertEqual(result.started_at, "2026-10-11T00:38:00+00:00")
        self.assertEqual(result.submitted_at, "2026-10-10T14:36:00+00:00")

    def test_six_days_after_shipped_at_is_not_stuck(self):
        result = assess_awaiting_carrier_processing(
            order(),
            now=datetime.fromisoformat(SHIPPED) + timedelta(days=6),
        )

        self.assertTrue(result.in_stage)
        self.assertFalse(result.stuck)

    def test_exactly_ten_days_is_not_more_than_ten(self):
        result = assess_awaiting_carrier_processing(
            order(),
            now=datetime.fromisoformat(SHIPPED) + timedelta(days=10),
        )

        self.assertFalse(result.stuck)

    def test_eight_days_is_not_stuck(self):
        result = assess_awaiting_carrier_processing(
            order(),
            now=datetime.fromisoformat(SHIPPED) + timedelta(days=8),
        )

        self.assertFalse(result.stuck)

    def test_explicit_awaiting_status_uses_the_same_clock(self):
        result = assess_awaiting_carrier_processing(
            order(processing_status="awaiting_carrier_processing"),
            now=NOW,
        )

        self.assertTrue(result.in_stage)
        self.assertTrue(result.stuck)
        self.assertEqual(result.started_from, "shipped_at")

    def test_returned_en_route_order_is_not_this_stage(self):
        result = assess_awaiting_carrier_processing(
            order(returns=[{"rma": "712-884-506", "status": "returned"}]),
            now=NOW,
        )

        self.assertFalse(result.in_stage)
        self.assertFalse(result.stuck)

    def test_delivered_order_is_not_this_stage(self):
        result = assess_awaiting_carrier_processing(
            order(processing_status="delivered"),
            now=NOW,
        )

        self.assertFalse(result.in_stage)
        self.assertFalse(result.stuck)

    def test_missing_shipped_at_and_pickup_log_does_not_invent_a_duration(self):
        result = assess_awaiting_carrier_processing(
            order(shipped_at=None),
            now=NOW,
        )

        self.assertTrue(result.in_stage)
        self.assertIsNone(result.stuck)
        self.assertIsNone(result.elapsed_days)

    def test_packed_order_is_not_on_the_carrier_step(self):
        result = assess_awaiting_carrier_processing(
            order(processing_status="packed", shipped_at=None),
            now=NOW,
        )

        self.assertFalse(result.in_stage)
        self.assertFalse(result.stuck)

    def test_stage_clock_before_submission_is_not_established(self):
        early_pickup = [
            {"datetime": "2026-10-09T00:00:00+00:00", "message": "Marked order 8274 as picked up."},
            {"datetime": SUBMITTED, "message": "Order 2228133536 submitted."},
        ]
        result = assess_awaiting_carrier_processing(order(), now=NOW, logs=early_pickup)

        self.assertTrue(result.in_stage)
        self.assertIsNone(result.stuck)

    def test_at_risk_order_past_ten_days_is_cloned_and_the_original_is_resolved(self):
        assessment = assess_awaiting_carrier_processing(order(), now=NOW)
        action = at_risk_job_action(order(), assessment)

        self.assertTrue(assessment.stuck)
        self.assertEqual(action["action"], "clone_and_resolve_original")
        self.assertTrue(action["clone"])
        self.assertTrue(action["resolve_original"])
        self.assertEqual(action["resolve_as"], "undeliverable")

    def test_order_that_is_not_at_risk_is_not_cloned(self):
        payload = order(actions_required={"at_risk": False})
        assessment = assess_awaiting_carrier_processing(payload, now=NOW)
        action = at_risk_job_action(payload, assessment)

        self.assertTrue(assessment.stuck)
        self.assertIsNone(action["action"])
        self.assertFalse(action["clone"])

    def test_at_risk_order_under_ten_days_is_not_cloned(self):
        payload = order()
        assessment = assess_awaiting_carrier_processing(
            payload,
            now=datetime.fromisoformat(SHIPPED) + timedelta(days=8),
        )
        action = at_risk_job_action(payload, assessment)

        self.assertFalse(assessment.stuck)
        self.assertIsNone(action["action"])


if __name__ == "__main__":
    unittest.main()
