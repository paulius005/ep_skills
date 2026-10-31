# Slack Block Kit cards

Use this payload when the sender accepts `blocks`. The parent message stays the one-line daily title. These blocks are the thread reply for one order.

Do not add a store id field. Do not put the address, email, or phone in any block, including `value`. The `value` may carry `order_number`, `order_key`, and `rma` so the listener can re-read the order.

Plain words, not raw status keys. Omit a field object when it does not apply. A section `fields` array holds at most 10 items.

## Reply card

```json
{
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Order #8257*"
      }
    },
    {
      "type": "section",
      "fields": [
        {"type": "mrkdwn", "text": "*Status*\nFulfilled"},
        {"type": "mrkdwn", "text": "*Processing*\nEn route"},
        {"type": "mrkdwn", "text": "*Return*\nReturned · received Oct 21"},
        {"type": "mrkdwn", "text": "*Action required*\nAt risk"},
        {"type": "mrkdwn", "text": "*Ship to*\nHawaii"},
        {"type": "mrkdwn", "text": "*Service*\nUSPS Priority Mail"}
      ]
    },
    {
      "type": "context",
      "elements": [
        {
          "type": "mrkdwn",
          "text": "Draft an email to the customer. Ask them to check the address."
        }
      ]
    },
    {
      "type": "actions",
      "block_id": "order_8257",
      "elements": [
        {
          "type": "button",
          "action_id": "draft_address_check",
          "text": {"type": "plain_text", "text": "Draft address-check email", "emoji": true},
          "value": "{\"v\":1,\"action\":\"draft_address_check\",\"store_id\":\"19002\",\"order_key\":\"18927830040707\",\"rma\":\"712-884-506\"}"
        },
        {
          "type": "button",
          "action_id": "view_order",
          "text": {"type": "plain_text", "text": "View order in ShipMonk", "emoji": true},
          "url": "https://app.shipmonk.com/orders/lookup/19002/18927830040707"
        }
      ]
    }
  ]
}
```

`Return` is present because this order's return status is `returned` even though processing is still en route. Drop that field when there is no return.

The context line is the human instruction. Use the Caterpillar English rules in the skill. For a returned order, use one of these:

- No verified draft: `Draft an email to the customer. Ask them to check the address.`
- Verified unsent draft: `The draft email is in your inbox. It is not sent.`

Do not write `Already en route. Service left unchanged.` Do not put the button label on the context line. The example above is the no-draft shape. After a saved draft, switch to the inbox line and add the Draft field. Do not say the email was sent.

`Service` is "Not set (requested Standard)" when ShipMonk has not resolved a method.

Add a *Draft* field, "DRAFT ONLY / unsent", only after a draft is saved. Do not say one was saved because the button is on the card.

## Buttons

| Button | When | Behavior |
| --- | --- | --- |
| View order in ShipMonk | Every order | `url` button. Opens the order. No listener. |
| Draft address-check email | Return status exactly `returned` | `action_id` `draft_address_check`. Runs the listener. Saves an unsent draft from `hello@runeastpeak.com`. Does not send. |
| USPS Priority | Verified editable Hawaii or Alaska, and not returned | `action_id` `usps_priority`. Does not run for an en route, packed, or returned order. Does not use FlavorCloud. |

Put at most those buttons in `actions.elements`. Slack allows five. Do not include an `action_id` button unless a click will reach an agent that runs the listener. A URL button still works without that.

`value` is a JSON string under 2000 characters. `action_id` is unique inside the actions block.

## Markdown fallback

Use this only when the sender cannot post `blocks`. Same facts, no fake buttons.

```
*Order #8257*
*Status:* Fulfilled
*Processing:* En route
*Return:* Returned · received Oct 21
*Action required:* At risk
*Ship to:* Hawaii
*Service:* USPS Priority Mail
Draft an email to the customer. Ask them to check the address.
<https://app.shipmonk.com/orders/lookup/19002/18927830040707|View order in ShipMonk>
```
