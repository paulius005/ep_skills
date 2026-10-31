"""Build Slack Block Kit for the daily at-risk shipment report.

The layout matches the East Peak Operations target: a warning header, two
summary lines, a quote count, a thread link, then one order card per shipment.
Address before/after is a separate section. Email and phone are never rendered.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from zoneinfo import ZoneInfo

CHANNEL_ID = "C0CCJJGG6HK"
WORKSPACE_HOST = "east-peak-workspace.slack.com"
ALLOWED_STORES = {"19002", "18969"}
ADDRESS_LINE_LIMIT = 50
ADDRESS_DISPLAY_MAX = 300
CONTEXT_MAX = 75
SECTION_MAX = 3000
BUTTON_VALUE_MAX = 2000
PACIFIC = ZoneInfo("America/Los_Angeles")

MONTHS = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)

ROUTE_STAGE = {
    "en_route": "In transit",
    "packed": "Packed",
    "unable_to_submit": "Unable to submit",
    "queued_to_submit": "Queued to submit",
    "submitted": "Submitted",
    "awaiting_carrier_processing": "Awaiting carrier",
    "pick_in_progress": "Picking",
    "picked": "Picked",
}

NOT_EDITABLE_PROCESSING = {"en_route", "packed"}

FLAG_LABELS = {
    "at_risk": "At risk",
    "address": "Address",
    "item_mapping": "Item mapping",
    "shipping_mapping": "Shipping mapping",
    "customs": "Customs",
    "hs_code": "HS code",
    "routing": "Routing",
    "pending_b2b_routing": "Pending B2B routing",
    "freight_quote": "Freight quote",
    "freight_info": "Freight info",
    "ship_short": "Ship short",
    "global_e_label": "Global-e label",
    "automation_rule": "Automation rule",
    "value_added_service_problem": "Value-added service",
}

ORDER_STATUS = {
    "fulfilled": "Fulfilled",
    "unfulfilled": "Unfulfilled",
    "cancelled": "Cancelled",
    "on_hold": "On hold",
}

US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
}


def humanize(value: str) -> str:
    return " ".join(part.capitalize() for part in value.replace("_", " ").split())


def format_header_date(value: date) -> str:
    """Pacific calendar date as in the header, for example `Oct 30`."""
    return f"{MONTHS[value.month - 1]} {value.day}"


def pacific_calendar_date(value: datetime) -> date:
    """Calendar date in America/Los_Angeles. `value` must be timezone-aware."""
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(PACIFIC).date()


def parent_header(value: date) -> str:
    return f"At-risk shipments · {format_header_date(value)}"


def is_hi_ak(state: str) -> bool:
    key = (state or "").strip().lower().rstrip(".")
    return key in {"hi", "ak", "hawaii", "alaska"}


def state_name(state: str) -> str:
    cleaned = (state or "").strip()
    if len(cleaned) == 2 and cleaned.upper() in US_STATES:
        return US_STATES[cleaned.upper()]
    return cleaned


def truncate_address_line2(street2: str, limit: int = ADDRESS_LINE_LIMIT) -> str:
    """Shorten address line 2 to the ShipMonk limit without cutting a word.

    A `Guest: Name, ...` line keeps `Guest: Name` and drops the rest.
    """
    if street2 is None:
        return ""
    if len(street2) <= limit:
        return street2
    if street2.startswith("Guest:") and "," in street2:
        head = street2.split(",", 1)[0].rstrip()
        if 0 < len(head) <= limit:
            return head
    window = street2[:limit]
    if limit < len(street2) and not street2[limit].isspace() and " " in window:
        window = window.rsplit(" ", 1)[0]
    return window.rstrip()


def truncate_display(text: str, max_len: int = ADDRESS_DISPLAY_MAX) -> str:
    """Cap a displayed address line. The 61-character fixture is left whole."""
    if text is None or len(text) <= max_len:
        return text or ""
    return text[: max_len - 1].rstrip() + "…"


@dataclass
class Shipment:
    order_number: str
    store_id: str
    order_key: str
    order_status: str
    processing_status: str
    state: str
    flags: list[str] = field(default_factory=list)
    service: str | None = None
    requested_service: str | None = None
    country: str = "US"
    editable: bool = False
    return_status: str | None = None
    rma: str | None = None
    shipment_id: str | None = None
    email: str | None = None
    phone: str | None = None
    street1: str | None = None
    street2: str | None = None
    draft_saved: bool = False
    service_changed: bool = False
    context: str | None = None
    shipmonk_url: str | None = None

    def __post_init__(self) -> None:
        self.store_id = str(self.store_id)
        if self.store_id not in ALLOWED_STORES:
            raise ValueError(f"store_id must be one of {sorted(ALLOWED_STORES)}")
        self.flags = list(self.flags or [])


@dataclass
class Report:
    pacific_date: date
    shipments: list[Shipment]
    channel_id: str = CHANNEL_ID

    def __post_init__(self) -> None:
        if self.channel_id != CHANNEL_ID:
            raise ValueError(f"channel_id must be {CHANNEL_ID}")


@dataclass
class PlannedMessage:
    kind: str
    text: str
    blocks: list
    order_number: str | None = None

    def as_dict(self) -> dict:
        payload = {"kind": self.kind, "text": self.text, "blocks": self.blocks}
        if self.order_number is not None:
            payload["order_number"] = self.order_number
        return payload


def _section(text: str) -> dict:
    if not text or len(text) > SECTION_MAX:
        raise ValueError("section text must be 1 to 3000 characters")
    return {"type": "section", "text": {"type": "mrkdwn", "text": text}}


def _context(text: str) -> dict:
    if not text or len(text) > CONTEXT_MAX:
        raise ValueError("context text must be 1 to 75 characters")
    return {"type": "context", "elements": [{"type": "mrkdwn", "text": text}]}


def _scrub(text: str, shipment: Shipment) -> str:
    for hidden in (shipment.email, shipment.phone, shipment.street1):
        if hidden and hidden in text:
            raise ValueError("refusing to render email, phone, or street")
    return text


def _in_transit(shipment: Shipment) -> bool:
    return shipment.processing_status == "en_route"


def service_change_count(report: Report) -> int:
    return sum(1 for shipment in report.shipments if shipment.service_changed)


def in_transit_count(report: Report) -> int:
    return sum(1 for shipment in report.shipments if _in_transit(shipment))


def summary_lines(report: Report) -> list[str]:
    count = len(report.shipments)
    transit = in_transit_count(report)
    if count == 0:
        transit_line = "No flagged orders shown."
    elif transit == count and count == 1:
        transit_line = "The order shown is already in transit."
    elif transit == count and count == 2:
        transit_line = "Both orders shown are already in transit."
    elif transit == count:
        transit_line = f"All {count} orders shown are already in transit."
    elif transit == 0:
        transit_line = "No orders shown are in transit."
    else:
        transit_line = f"{transit} of {count} orders shown are already in transit."
    changes = service_change_count(report)
    if changes == 0:
        service_line = "Shipping services were left unchanged."
    elif changes == 1:
        service_line = "1 shipping service was changed."
    else:
        service_line = f"{changes} shipping services were changed."
    return [transit_line, service_line]


def quote_lines(report: Report) -> tuple[str, str]:
    count = len(report.shipments)
    order_word = "order" if count == 1 else "orders"
    changes = service_change_count(report)
    change_word = "change" if changes == 1 else "changes"
    title = f"{count} flagged {order_word} shown"
    detail = f"{in_transit_count(report)} in transit · {changes} service {change_word}"
    return title, detail


def thread_link_label(count: int) -> str:
    noun = "detail" if count == 1 else "details"
    return f"{count} order {noun} in thread →"


def slack_permalink(channel_id: str, ts: str, host: str = WORKSPACE_HOST) -> str:
    return f"https://{host}/archives/{channel_id}/p{ts.replace('.', '')}"


def show_usps_button(shipment: Shipment) -> bool:
    if shipment.return_status == "returned":
        return False
    if not shipment.editable:
        return False
    if shipment.processing_status in NOT_EDITABLE_PROCESSING:
        return False
    return is_hi_ak(shipment.state)


def show_draft_button(shipment: Shipment) -> bool:
    return shipment.return_status == "returned" and not shipment.draft_saved


def address_over_limit(shipment: Shipment) -> bool:
    street2 = shipment.street2 or ""
    return "address" in shipment.flags and len(street2) > ADDRESS_LINE_LIMIT


def context_line(shipment: Shipment) -> str:
    if shipment.context:
        line = shipment.context
    elif shipment.draft_saved:
        line = "The draft email is in your inbox."
    elif shipment.return_status == "returned":
        line = "Draft an email to the customer."
    elif address_over_limit(shipment):
        line = "Address 2 exceeded limit of 50 characters."
    elif shipment.processing_status == "en_route" and not shipment.service_changed:
        line = "Service unchanged — shipment already en route."
    elif show_usps_button(shipment):
        place = state_name(shipment.state)
        line = f"Choose USPS Priority for {place}."
    elif "address" in shipment.flags:
        line = "Correct the address so ShipMonk can submit it."
    else:
        line = "Review this order before it ships."
    if len(line) > CONTEXT_MAX:
        raise ValueError("context line exceeds 75 characters")
    return _scrub(line, shipment)


def route_line(shipment: Shipment) -> str:
    stage = ROUTE_STAGE.get(shipment.processing_status, humanize(shipment.processing_status))
    place = state_name(shipment.state)
    country = (shipment.country or "US").strip()
    if country.upper() not in {"US", "USA", "UNITED STATES"}:
        place = f"{place}, {country}"
    return f"{stage} → {place}"


def service_line(shipment: Shipment) -> str:
    if shipment.service:
        return shipment.service
    if shipment.requested_service:
        return f"Not set (requested {shipment.requested_service})"
    return "Not set"


def footer_line(shipment: Shipment) -> str:
    status = ORDER_STATUS.get(shipment.order_status, humanize(shipment.order_status))
    return f"Store {shipment.store_id} · {status}"


def order_url(shipment: Shipment) -> str:
    if shipment.shipmonk_url:
        return shipment.shipmonk_url
    return f"https://app.shipmonk.com/orders/lookup/{shipment.store_id}/{shipment.order_key}"


def flag_chips(flags: list[str]) -> str:
    labels = [FLAG_LABELS.get(flag, humanize(flag)) for flag in flags] or ["Action required"]
    return "  ".join(f"`{label}`" for label in labels)


def button_value(shipment: Shipment, action: str) -> str:
    payload = {
        "v": 1,
        "action": action,
        "store_id": shipment.store_id,
        "order_key": shipment.order_key,
    }
    if action == "draft_address_check":
        if not shipment.rma:
            raise ValueError("draft_address_check requires rma")
        payload["rma"] = shipment.rma
    if shipment.shipment_id:
        payload["shipment_id"] = shipment.shipment_id
    encoded = json.dumps(payload, separators=(",", ":"))
    if len(encoded) > BUTTON_VALUE_MAX:
        raise ValueError("button value exceeds 2000 characters")
    for hidden in (shipment.email, shipment.phone, shipment.street1, shipment.street2):
        if hidden and hidden in encoded:
            raise ValueError("button value must not include email, phone, or address")
    return encoded


def action_buttons(shipment: Shipment) -> list[dict]:
    buttons = []
    if show_draft_button(shipment):
        buttons.append({
            "type": "button",
            "action_id": "draft_address_check",
            "text": {
                "type": "plain_text",
                "text": "Draft an email to the customer",
                "emoji": True,
            },
            "value": button_value(shipment, "draft_address_check"),
        })
    elif show_usps_button(shipment):
        buttons.append({
            "type": "button",
            "action_id": "usps_priority",
            "text": {"type": "plain_text", "text": "USPS Priority", "emoji": True},
            "value": button_value(shipment, "usps_priority"),
        })
    return buttons


def _quote_block(title: str, detail: str) -> dict:
    return {
        "type": "rich_text",
        "elements": [
            {
                "type": "rich_text_quote",
                "elements": [
                    {"type": "text", "text": title, "style": {"bold": True}},
                    {"type": "text", "text": "\n" + detail},
                ],
            }
        ],
    }


def parent_blocks(report: Report, permalink: str | None = None) -> list[dict]:
    header = f":warning: {parent_header(report.pacific_date)}"
    lines = summary_lines(report)
    title, detail = quote_lines(report)
    label = thread_link_label(len(report.shipments))
    link = f"<{permalink}|{label}>" if permalink else label
    return [
        {"type": "header", "text": {"type": "plain_text", "text": header, "emoji": True}},
        _section("\n".join(lines)),
        _quote_block(title, detail),
        _section(link),
    ]


def parent_fallback(report: Report, permalink: str | None = None) -> str:
    title, detail = quote_lines(report)
    label = thread_link_label(len(report.shipments))
    if permalink:
        label = f"{label} {permalink}"
    lines = [parent_header(report.pacific_date), *summary_lines(report), title, detail, label]
    return "\n".join(lines)


def order_blocks(shipment: Shipment) -> list[dict]:
    title = f"*Order #{shipment.order_number}*  {flag_chips(shipment.flags)}"
    body = f"{title}\n*{route_line(shipment)}*\n{service_line(shipment)}"
    link = f"<{order_url(shipment)}|View order in ShipMonk ↗>"
    blocks = [
        _section(_scrub(body, shipment)),
        _context(context_line(shipment)),
        _section(_scrub(link, shipment)),
    ]
    buttons = action_buttons(shipment)
    if buttons:
        blocks.append({
            "type": "actions",
            "block_id": f"order_{shipment.order_number}",
            "elements": buttons,
        })
    blocks.append(_context(_scrub(footer_line(shipment), shipment)))
    return blocks


def order_fallback(shipment: Shipment) -> str:
    labels = [FLAG_LABELS.get(flag, humanize(flag)) for flag in shipment.flags]
    lines = [
        f"Order #{shipment.order_number}",
        ", ".join(labels),
        route_line(shipment),
        service_line(shipment),
        context_line(shipment),
        f"View order in ShipMonk: {order_url(shipment)}",
        footer_line(shipment),
    ]
    return _scrub("\n".join(line for line in lines if line), shipment)


def address_section_text(shipment: Shipment) -> str | None:
    if not address_over_limit(shipment):
        return None
    street2 = shipment.street2 or ""
    after = truncate_address_line2(street2)
    before = truncate_display(street2)
    text = (
        f"*Order #{shipment.order_number}*\n"
        f"Address 2 is {len(street2)} characters. The limit is {ADDRESS_LINE_LIMIT}.\n"
        f"*Before:* {before}\n"
        f"*After:* {after}\n"
        "Do not change the address until this is approved."
    )
    return _scrub(text, shipment)


def address_blocks(shipment: Shipment) -> list[dict] | None:
    text = address_section_text(shipment)
    if text is None:
        return None
    return [_section(text)]


def plan_messages(report: Report, permalink: str | None = None) -> list[PlannedMessage]:
    messages = [
        PlannedMessage(
            kind="parent",
            text=parent_fallback(report, permalink),
            blocks=parent_blocks(report, permalink),
        )
    ]
    for shipment in report.shipments:
        messages.append(PlannedMessage(
            kind="order",
            order_number=str(shipment.order_number),
            text=order_fallback(shipment),
            blocks=order_blocks(shipment),
        ))
        address_text = address_section_text(shipment)
        if address_text is not None:
            messages.append(PlannedMessage(
                kind="address",
                order_number=str(shipment.order_number),
                text=address_text.replace("*", ""),
                blocks=[_section(address_text)],
            ))
    return messages


def _as_date(value) -> date:
    if isinstance(value, datetime):
        return pacific_calendar_date(value)
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise ValueError("pacific_date must be a date")


def shipment_from_dict(data: dict) -> Shipment:
    required = (
        "order_number", "store_id", "order_key", "order_status",
        "processing_status", "state",
    )
    missing = [key for key in required if not data.get(key)]
    if missing:
        raise ValueError(f"shipment missing {', '.join(missing)}")
    return Shipment(
        order_number=str(data["order_number"]),
        store_id=str(data["store_id"]),
        order_key=str(data["order_key"]),
        order_status=str(data["order_status"]),
        processing_status=str(data["processing_status"]),
        state=str(data["state"]),
        flags=list(data.get("flags") or []),
        service=data.get("service"),
        requested_service=data.get("requested_service"),
        country=data.get("country") or "US",
        editable=bool(data.get("editable", False)),
        return_status=data.get("return_status"),
        rma=data.get("rma"),
        shipment_id=data.get("shipment_id"),
        email=data.get("email"),
        phone=data.get("phone"),
        street1=data.get("street1"),
        street2=data.get("street2"),
        draft_saved=bool(data.get("draft_saved", False)),
        service_changed=bool(data.get("service_changed", False)),
        context=data.get("context"),
        shipmonk_url=data.get("shipmonk_url"),
    )


def report_from_dict(data: dict) -> Report:
    if "pacific_date" not in data:
        raise ValueError("pacific_date is required")
    shipments = [shipment_from_dict(item) for item in data.get("shipments") or []]
    return Report(
        pacific_date=_as_date(data["pacific_date"]),
        shipments=shipments,
        channel_id=str(data.get("channel_id") or CHANNEL_ID),
    )
