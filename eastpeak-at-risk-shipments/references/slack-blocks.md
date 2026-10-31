# Slack Block Kit cards

The daily report is posted by `eastpeak-at-risk-shipments/slack_poster`. Cursor's built-in Send to Slack tool posts plain text only, so it cannot send this payload. The poster calls `chat.postMessage` with `blocks` and a plain-text `text` fallback. The Slack app name is East Peak Operations.

Channel `C0CCJJGG6HK`. One parent per Pacific day. Each order is a thread reply. An address-line fix is a second reply under that same parent, immediately after its order card.

Do not put email or phone in any block, including `value`. Do not put the street on the order card. The address follow-up is the only place a street line appears, and only the lines that would change. The footer shows the store id. `value` may carry `order_key`, `store_id`, `rma`, and `shipment_id` so the listener can re-read the order.

Plain words, not raw status keys. A context element is at most 75 characters.

## Parent

Header date is the Pacific calendar date as a short month and day: `Oct 30`, not `2026-10-30`. Summary lines and the quote follow the orders in the report. The thread link is `{n} order details in thread →`. After Slack returns the parent `ts`, `chat.update` turns that line into the message permalink.

```json
{
  "text": "At-risk shipments · Oct 30\nBoth orders shown are already in transit.\nShipping services were left unchanged.\n2 flagged orders shown\n2 in transit · 0 service changes\n2 order details in thread →",
  "blocks": [
    {
      "type": "header",
      "text": {"type": "plain_text", "text": ":warning: At-risk shipments · Oct 30", "emoji": true}
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "Both orders shown are already in transit.\nShipping services were left unchanged."
      }
    },
    {
      "type": "rich_text",
      "elements": [
        {
          "type": "rich_text_quote",
          "elements": [
            {"type": "text", "text": "2 flagged orders shown", "style": {"bold": true}},
            {"type": "text", "text": "\n2 in transit · 0 service changes"}
          ]
        }
      ]
    },
    {
      "type": "section",
      "text": {"type": "mrkdwn", "text": "2 order details in thread →"}
    }
  ]
}
```

## Order card

In transit, with no built-in action, the card has no `actions` block. `View order in ShipMonk` is a link.

```json
{
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Order #8257*  `At risk`\n*In transit → Hawaii*\nUSPS Priority Mail"
      }
    },
    {
      "type": "context",
      "elements": [
        {"type": "mrkdwn", "text": "Service unchanged — shipment already en route."}
      ]
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "<https://app.shipmonk.com/orders/lookup/19002/18927830040707|View order in ShipMonk ↗>"
      }
    },
    {
      "type": "context",
      "elements": [
        {"type": "mrkdwn", "text": "Store 19002 · Fulfilled"}
      ]
    }
  ]
}
```

Order `#8274` uses the same hierarchy with `In transit → California`, `ShipMonk Standard`, and the same context and footer.

`Service` is `Not set (requested Standard)` when ShipMonk has not resolved a method. The route uses `In transit` for `en_route` and the full state name.

## Address section

When the address flag is true and address line 2 is longer than 50 characters, this is a separate thread reply. It is one section. The order card does not include the street.

```json
{
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Order #8376*\nAddress 2 is 61 characters. The limit is 50.\n*Before:* Guest: Tyler Maher, staying from 5th November - 11th November\n*After:* Guest: Tyler Maher\nDo not change the address until this is approved."
      }
    }
  ]
}
```

A `Guest: Name, ...` line keeps `Guest: Name` as `After`. Any other over-long line is shortened on a word boundary. A displayed `Before` line longer than 300 characters is cut with an ellipsis. The length in the sentence is the full line.

When address line 2 is over 50 characters, the card context line is `Address 2 exceeded limit of 50 characters.` The suggested fix is a separate reply under that order, not a field on the card and not a button. The card omits the street. That reply shows `Before:` and `After:` for the lines that would change. Leave email and phone out of both messages. See [Address line limits](../SKILL.md#address-line-limits).

## Buttons

| Button | When | Behavior |
| --- | --- | --- |
| View order in ShipMonk | Every order | Link. Opens the order. No listener. |
| Draft an email to the customer | Return status exactly `returned`, and no saved draft yet | `action_id` `draft_address_check`. Saves an unsent draft from `hello@runeastpeak.com`. Does not send. |
| USPS Priority | Verified editable Hawaii or Alaska, and not returned, and not en route or packed | `action_id` `usps_priority`. Does not use FlavorCloud. |

Returned wins over USPS Priority. Do not include both. Do not add a button that edits the address. After the draft is saved and read back, omit the draft button and set the context line to `The draft email is in your inbox.` Before that, the context line is `Draft an email to the customer.`

Put the button in `actions.elements` only when its gate passes. Slack allows five. `value` is a JSON string under 2000 characters. `action_id` is unique inside the actions block.

`value` for USPS Priority:

```json
{"v":1,"action":"usps_priority","store_id":"19002","order_key":"18927830040707"}
```

`value` for the draft button adds `"rma":"<rma>"`. Add `shipment_id` only when the live record has a verified shipment id. `store_id` is `19002` or `18969`. `action` equals the `action_id`. `v` is `1`.

The listener reads that JSON from the Slack `block_actions` payload. See [the listener contract](slack-listener.md).

## Plain-text fallback

`text` repeats the same facts for notifications. It has no fake buttons. Email, phone, and the street stay out of the order fallback. The address follow-up fallback includes `Before:` and `After:` only.
