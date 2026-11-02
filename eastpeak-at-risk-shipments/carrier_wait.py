"""Decide whether an order has sat on Awaiting Carrier Processing for more than 10 days.

The integrations order is enough for the check. The app log list is used when
it is present. This module does not call ShipMonk and does not change a shipment.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone

THRESHOLD_DAYS = 10
# The Resolve At Risk dialog has no "at risk" value. After a replacement is
# created, the original at-risk order is resolved as undeliverable.
RESOLVE_ORIGINAL_AS = "undeliverable"
THRESHOLD = timedelta(days=THRESHOLD_DAYS)

# The order-page timeline has no En Route step. After Picked Up, the current
# step is Awaiting Carrier Processing until Delivered. The status badge can
# still say En Route. Both processing values are that step.
STAGE_STATUSES = frozenset({"awaiting_carrier_processing", "en_route"})

PICKUP_RE = re.compile(r"marked order \S+ as picked up", re.IGNORECASE)
SUBMITTED_RE = re.compile(r"(?:^|\b)order \S+ submitted\.?$", re.IGNORECASE)
AT_RISK_RE = re.compile(r"moved to at-risk", re.IGNORECASE)


@dataclass(frozen=True)
class CarrierWaitAssessment:
    """Result of one stuck-time check. `stuck` is None when the clock is missing."""

    in_stage: bool
    stuck: bool | None
    processing_status: str | None
    started_at: str | None
    started_from: str | None
    submitted_at: str | None
    elapsed_days: float | None
    threshold_days: int
    detail: str

    def as_dict(self) -> dict:
        return asdict(self)


def assess_awaiting_carrier_processing(
    order: dict,
    *,
    now: datetime,
    logs: list | None = None,
    threshold_days: int = THRESHOLD_DAYS,
) -> CarrierWaitAssessment:
    """Return whether `order` is on Awaiting Carrier Processing for longer than the threshold.

    `order` is a `GET /v1/integrations/orders` payload. `logs` are app log rows
    with `datetime` and `message`. `now` must be timezone-aware.

    The clock is the pickup log when one was read. Otherwise it is `shipped_at`.
    `ordered_at`, `updated_at`, and a "moved to At-Risk" row are not the clock.
    A return whose status is exactly `returned` is not this stage.
    """
    if now.tzinfo is None:
        raise ValueError("now must include a timezone")
    if threshold_days < 1:
        raise ValueError("threshold_days must be at least 1")
    status = order.get("processing_status")
    status_text = str(status) if status else None
    submitted_at = _submitted_at(logs or [])
    if _has_returned(order):
        return _result(
            in_stage=False,
            stuck=False,
            status=status_text,
            submitted_at=submitted_at,
            threshold_days=threshold_days,
            detail="A returned order is not the Awaiting Carrier Processing step.",
        )
    if status_text not in STAGE_STATUSES:
        return _result(
            in_stage=False,
            stuck=False,
            status=status_text,
            submitted_at=submitted_at,
            threshold_days=threshold_days,
            detail="The order is not on Awaiting Carrier Processing.",
        )
    started_at, started_from = _stage_start(order, logs or [])
    if started_at is None:
        return _result(
            in_stage=True,
            stuck=None,
            status=status_text,
            submitted_at=submitted_at,
            threshold_days=threshold_days,
            detail="The order is on that step, and the pickup log and shipped_at are both missing.",
        )
    if submitted_at is not None and started_at < submitted_at:
        return _result(
            in_stage=True,
            stuck=None,
            status=status_text,
            submitted_at=submitted_at,
            threshold_days=threshold_days,
            detail="The stage clock is earlier than submission, so the duration is not established.",
        )
    elapsed = now.astimezone(timezone.utc) - started_at
    elapsed_days = elapsed.total_seconds() / 86400
    stuck = elapsed > timedelta(days=threshold_days)
    if stuck:
        detail = (
            f"On Awaiting Carrier Processing for {elapsed_days:.1f} days, "
            f"counted from {started_from} after submission."
        )
    else:
        detail = (
            f"On Awaiting Carrier Processing for {elapsed_days:.1f} days, "
            f"which is not more than {threshold_days} days."
        )
    return _result(
        in_stage=True,
        stuck=stuck,
        status=status_text,
        started_at=started_at,
        started_from=started_from,
        submitted_at=submitted_at,
        elapsed_days=round(elapsed_days, 3),
        threshold_days=threshold_days,
        detail=detail,
    )


def at_risk_job_action(order: dict, assessment: CarrierWaitAssessment) -> dict:
    """Decide the daily-job action for one surfaced order.

    Clone and resolve only when this job surfaced the order, `at_risk` is true,
    and the carrier-wait assessment is stuck. The clone is the replacement.
    The resolve call is for the original order, with resolveAs undeliverable.
    """
    flags = order.get("actions_required") or {}
    at_risk = bool(flags.get("at_risk")) if isinstance(flags, dict) else False
    if assessment.stuck is True and at_risk:
        return {
            "action": "clone_and_resolve_original",
            "clone": True,
            "resolve_original": True,
            "resolve_as": RESOLVE_ORIGINAL_AS,
            "detail": (
                "At-risk order is past the carrier-wait threshold. "
                "Clone a replacement, then resolve the original as undeliverable."
            ),
        }
    return {
        "action": None,
        "clone": False,
        "resolve_original": False,
        "resolve_as": None,
        "detail": "No clone. The order is not an at-risk shipment past the carrier-wait threshold.",
    }


def _stage_start(order: dict, logs: list) -> tuple[datetime | None, str | None]:
    for row in logs:
        message = str(_field(row, "message") or "")
        if AT_RISK_RE.search(message):
            continue
        if PICKUP_RE.search(message):
            started = _parse_dt(_field(row, "datetime"))
            if started is not None:
                return started, "pickup_log"
    shipped = _parse_dt(order.get("shipped_at"))
    if shipped is not None:
        return shipped, "shipped_at"
    return None, None


def _submitted_at(logs: list) -> datetime | None:
    found = []
    for row in logs:
        message = str(_field(row, "message") or "")
        if SUBMITTED_RE.search(message.strip()):
            parsed = _parse_dt(_field(row, "datetime"))
            if parsed is not None:
                found.append(parsed)
    if not found:
        return None
    return min(found)


def _has_returned(order: dict) -> bool:
    returns = order.get("returns") or []
    if not isinstance(returns, list):
        return False
    for item in returns:
        if isinstance(item, dict) and item.get("status") == "returned":
            return True
    return False


def _field(row, key: str):
    if isinstance(row, dict):
        return row.get(key)
    return None


def _parse_dt(value) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat()


def _result(
    *,
    in_stage: bool,
    stuck: bool | None,
    status: str | None,
    threshold_days: int,
    detail: str,
    started_at: datetime | None = None,
    started_from: str | None = None,
    submitted_at: datetime | None = None,
    elapsed_days: float | None = None,
) -> CarrierWaitAssessment:
    return CarrierWaitAssessment(
        in_stage=in_stage,
        stuck=stuck,
        processing_status=status,
        started_at=_iso(started_at),
        started_from=started_from,
        submitted_at=_iso(submitted_at),
        elapsed_days=elapsed_days,
        threshold_days=threshold_days,
        detail=detail,
    )
