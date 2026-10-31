# Slack listener contract

Use this when a Slack reply on an at-risk order message is the trigger. The daily parent and the order message are reports. They do not change a shipment. The listener reads one reply, maps it to one existing action, applies the decision tree in [the skill](../SKILL.md), and updates that ShipMonk shipment only when the tree allows the update.

Read [the incident record](incident-record.md) and take the exclusive claim before any mutation. Re-read the live order immediately before writing. ShipMonk calls use the skill's API rules: curl or a non-Python-urllib client, East Peak store `19002` or Manual Store `18969`, secret `SHIPMONK_API_KEY` never printed. The order must be on the Action Required alert. Before posting about that order or saving a draft, run the inbox check in the skill for this one order. Report the result on the reply. The check does not send mail.

The order-message card is [the Slack blocks reference](slack-blocks.md). This file is the action map and the click contract.

## What the listener accepts

Channel **C0CCJJGG6HK** in the East Peak workspace only. Stop if the workspace or channel differs.

An action input names **one** order message:

1. A Slack `block_actions` payload whose `channel.id` is `C0CCJJGG6HK`, whose `message.thread_ts` is the day's parent `ts`, and whose `message.ts` is that order message.
2. A message event whose `channel` is `C0CCJJGG6HK` and whose `thread_ts` is that order message's `ts`.
3. When the Slack client can only post inside the daily thread, a message whose `thread_ts` is the day's parent and whose text is exactly `<order message ts>` plus one space plus one action label below. The first token must equal the order message `ts`. The remainder must equal the label, with no extra words.

If the event names zero order messages, or more than one, record it and stop. Do not pick a shipment. Do not auto-merge orders, shipments, incidents, or Slack messages. Do not fold the reply or the result into the parent. One reply updates at most the one shipment that order message already identified.

## Return stage

Do not treat `processing_status` as the shipment stage when the order lists any `returns[].rma`. For each RMA, read `GET /v1/integrations/returns-list?rma={rma}`. Exact status `returned` means the shipment was returned after attempted delivery, even when `processing_status` is still `en_route`. That order gets the address-check button and does not get USPS Priority. The order-message context line is exactly `Returned after attempted delivery. Suggestion: draft an address-check email to the customer. Service left unchanged.` Do not write "Already en route" on that line, and do not append the packed or en-route tracking suggestion. Do not match the substring "return" in a city, note, or tracking line. Other return statuses are not this gate.

## How a reply maps to an action

Match the button `action_id` or the exact action label. Do not paraphrase. Slack text does not establish the halted reason; the live ShipMonk reason does. An unmapped reply is recorded on that order message and does not update the shipment.

| Reply | Existing action | What the tree then does |
| --- | --- | --- |
| `action_id` `usps_priority`, or label `USPS Priority` | Hawaii/Alaska USPS Priority selection | Verified HI/AK only, and the return status is not `returned`. If the exact live reason is `halted awaiting carrier processing`, the reply does not submit by itself: set USPS Priority on the eligible replacement, and clone and submit only after the duplicate, original, and cost gates. If the reason is anything else and the shipment is still editable, set USPS Priority, verify it, then save an unsent Gmail draft and never send it. If the shipment is not editable, or Priority cannot be verified, flag it, leave the service unchanged, and do not substitute another carrier. |
| Label `guarded clone and submit` | Replacement branch | Only when the exact live reason is `halted awaiting carrier processing`. Clone and submit only after the duplicate, original, and cost gates. For verified HI/AK, set USPS Priority on the eligible replacement before submission. Do not create a customer draft when that replacement succeeds unless separately requested. |
| Label `unsent Gmail draft` | Draft branch | Every reason other than that exact halted reason. For verified HI/AK, when the shipment is still editable and not returned, select and verify USPS Priority first, then save the draft. **DRAFT ONLY — NEVER SEND.** |
| `action_id` `draft_address_check`, or label `Draft address-check email` | Returned-shipment address check | Only when the return status is exactly `returned`. Re-read the return before drafting. Save the unsent draft below from `hello@runeastpeak.com`. Do not send it. Do not change the shipping service. |

`USPS Priority` is the only Hawaii/Alaska service option this skill defines. Show it as a button only when the verified destination state is HI or AK (or the unambiguous full name), the shipment is still editable, and the return status is not `returned`. Handed-off, returned, or otherwise uneditable HI/AK shipments are flagged in the order message and get no USPS Priority button. Do not add a FlavorCloud button or any other service button. Do not invent a button for clone, cancel, refund, or merge. The address-check button is the one draft button, and only for return status `returned`.

A mapped reply is still not approval for a new charge. Unknown or uncovered fees stop for owner approval. Never charge the customer again.

## Skill feedback

A reply in this channel that asks to change the skill is skill feedback. It is not one of the action labels above. Do not update the ShipMonk shipment from it, and do not auto-merge orders or shipments because of it.

Update `SKILL.md` and the references so the feedback is part of the skill, then add those files to the repo and commit. Leave the pull request unmerged unless the user asks to merge. Never commit or print the API key. If the feedback would send customer email, use FlavorCloud, skip the halted-reason gates, or invent a shipment action, record the reply and do not change the skill.

## Button payload on the order message

Post the order message with `chat.postMessage` when a bot token can send `blocks`. Otherwise use the markdown fallback in the blocks reference and do not invent a dead action button. `text` is the fallback. Put no street address, email, or phone in `text`, blocks, or `value`. Store id may be inside `value` and inside the ShipMonk URL. Do not print it as a field.

`value` is a JSON string. `v` is `1`. `action` equals the `action_id`. `store_id` is `19002` or `18969`. `order_key` matches the order. Add `rma` only for `draft_address_check`. Add `shipment_id` only when the live record has a verified shipment id.

The **View order in ShipMonk** control is a `url` button with `action_id` `view_order`. It does not map to a shipment action.

Include `usps_priority` only for an editable verified HI/AK shipment that is not returned. Include `draft_address_check` only when the return status is exactly `returned`. Do not include both. The card layout is in [the Slack blocks reference](slack-blocks.md).

## Button payload the listener reads

Slack delivers the click as `block_actions`. The listener requires `type`, `channel.id`, `message.ts`, `message.thread_ts`, `actions[0].action_id`, and `actions[0].value`. Ignore other fields. `value` must parse as JSON with `v` equal to `1` and `action` equal to that `action_id`. `store_id` must be `19002` or `18969` and must match the order. `order_key` must match the order message. `view_order` is not a shipment action. Then re-read that order and apply the table.

```json
{
  "type": "block_actions",
  "channel": { "id": "C0CCJJGG6HK" },
  "message": {
    "ts": "<order message ts>",
    "thread_ts": "<daily parent ts>"
  },
  "actions": [
    {
      "type": "button",
      "action_id": "usps_priority",
      "block_id": "order_<order number>",
      "value": "{\"v\":1,\"action\":\"usps_priority\",\"store_id\":\"<19002 or 18969>\",\"order_key\":\"<order_key>\"}"
    }
  ]
}
```

The address-check click is the same shape with `action_id` `draft_address_check` and `"action":"draft_address_check"` plus `"rma":"<rma>"`.

## Text reply the listener reads

Nested reply, when the client can set `thread_ts` to the order message:

```json
{
  "type": "message",
  "channel": "C0CCJJGG6HK",
  "user": "<slack user id>",
  "ts": "<reply ts>",
  "thread_ts": "<order message ts>",
  "text": "USPS Priority"
}
```

`text` must be exactly `USPS Priority`, `guarded clone and submit`, `unsent Gmail draft`, or `Draft address-check email`.

Same-thread fallback, when the reply can only sit under the daily parent:

```json
{
  "type": "message",
  "channel": "C0CCJJGG6HK",
  "user": "<slack user id>",
  "ts": "<reply ts>",
  "thread_ts": "<daily parent ts>",
  "text": "<order message ts> USPS Priority"
}
```

The same other labels may replace `USPS Priority` in that text. Nothing else maps.

After a mapped action, post the verified result or the exact blocker as a further reply tied to that order message. Do not edit the parent. Do not mark the shipment resolved because the reply was posted.

## Draft address-check email

On `draft_address_check` only:

1. Re-read the return. If the status is no longer exactly `returned`, stop and say so. Do not draft from a stale button.
2. Re-read the order. The recipient is `customer_email` when the ship-to email is empty. If both are present and differ, or neither is present, stop and ask which address to use. Never guess.
3. The From account must be `hello@runeastpeak.com`. If that mailbox is not the one available, stop. Do not draft from another account.
4. Run the inbox check for this order number and order key, then search for an existing unsent draft whose subject is the subject below. Update that draft in place. If a matching message was already sent, stop and report it as correspondence. Do not send another.
5. Save **DRAFT ONLY — NEVER SEND**. Read back the draft id, From, To, subject, body, and unsent state.
6. Reply on that order message that the draft exists, labeled **DRAFT ONLY / unsent**, with the draft link when one exists. Do not include the address, email, or phone in that reply.

Subject:

```
Can you double-check the address for order {order_number}?
```

Body:

```
Hi {first_name},

Your East Peak order {order_number} came back to us on {returned_date}. Before we send it again, can you double-check the shipping address?

{street1}
{street2 line only when present}
{city}, {state} {zip}

If that's right, reply and let us know. If it isn't, reply with the corrected address.

We haven't reshipped it.

Thanks,
East Peak
```

Use the first name from the verified recipient. If it cannot be split safely, open with "Hi there,". `{returned_date}` is the return's received date in `America/Los_Angeles`, written as a calendar date. The address lines are the order's current ship-to, copied exactly. Do not claim the address failed validation, and do not invent a carrier reason. The known return reason may be unknown.

A saved draft is waiting for a person to review it. It does not reship the order and it does not clear the alert.
