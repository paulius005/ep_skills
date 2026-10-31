# Slack listener contract

Use this when a Slack reply on an at-risk order message is the trigger. The daily parent and the order message are reports. They do not change a shipment. The listener reads one reply, maps it to one existing action, applies the decision tree in [the skill](../SKILL.md), and updates that ShipMonk shipment only when the tree allows the update.

Read [the incident record](incident-record.md) and take the exclusive claim before any mutation. Re-read the live order immediately before writing. ShipMonk calls use the skill's API rules: curl or a non-Python-urllib client, store `19830`, secret `SHIPMONK_API_KEY` never printed.

## What the listener accepts

Channel **C0CCJJGG6HK** in the East Peak workspace only. Stop if the workspace or channel differs.

An action input names **one** order message:

1. A Slack `block_actions` payload whose `channel.id` is `C0CCJJGG6HK`, whose `message.thread_ts` is the day's parent `ts`, and whose `message.ts` is that order message.
2. A message event whose `channel` is `C0CCJJGG6HK` and whose `thread_ts` is that order message's `ts`.
3. When the Slack client can only post inside the daily thread, a message whose `thread_ts` is the day's parent and whose text is exactly `<order message ts>` plus one space plus one action label below. The first token must equal the order message `ts`. The remainder must equal the label, with no extra words.

If the event names zero order messages, or more than one, record it and stop. Do not pick a shipment. Do not auto-merge orders, shipments, incidents, or Slack messages. Do not fold the reply or the result into the parent. One reply updates at most the one shipment that order message already identified.

## How a reply maps to an action

Match the button `action_id` or the exact action label. Do not paraphrase. Slack text does not establish the halted reason; the live ShipMonk reason does. An unmapped reply is recorded on that order message and does not update the shipment.

| Reply | Existing action | What the tree then does |
| --- | --- | --- |
| `action_id` `usps_priority`, or label `USPS Priority` | Hawaii/Alaska USPS Priority selection | Verified HI/AK only. If the exact live reason is `halted awaiting carrier processing`, the reply does not submit by itself: set USPS Priority on the eligible replacement, and clone and submit only after the duplicate, original, and cost gates. If the reason is anything else and the shipment is still editable, set USPS Priority, verify it, then save an unsent Gmail draft and never send it. If the shipment is not editable, or Priority cannot be verified, flag it, leave the service unchanged, and do not substitute another carrier. |
| Label `guarded clone and submit` | Replacement branch | Only when the exact live reason is `halted awaiting carrier processing`. Clone and submit only after the duplicate, original, and cost gates. For verified HI/AK, set USPS Priority on the eligible replacement before submission. Do not create a customer draft when that replacement succeeds unless separately requested. |
| Label `unsent Gmail draft` | Draft branch | Every reason other than that exact halted reason. For verified HI/AK, when the shipment is still editable, select and verify USPS Priority first, then save the draft. **DRAFT ONLY — NEVER SEND.** |

`USPS Priority` is the only Hawaii/Alaska service option this skill defines. Show it as a button only when the verified destination state is HI or AK (or the unambiguous full name) and the shipment is still editable. Handed-off or otherwise uneditable HI/AK shipments are flagged in the order message and get no button. Do not add a FlavorCloud button or any other service button. Do not invent a button for clone, draft, cancel, refund, or merge.

A mapped reply is still not approval for a new charge. Unknown or uncovered fees stop for owner approval. Never charge the customer again.

## Button payload on the order message

Post the order message with `chat.postMessage` (or the equivalent) as a reply on the daily parent. Include the button only for an editable verified HI/AK shipment. `text` is the fallback. Put no street address, email, or phone in `text`, blocks, or `value`.

```json
{
  "channel": "C0CCJJGG6HK",
  "thread_ts": "<daily parent ts>",
  "text": "<order number> <exact risk reason>",
  "blocks": [
    {
      "type": "section",
      "block_id": "order",
      "text": {
        "type": "mrkdwn",
        "text": "<order link and order number>\n<exact risk reason>\nDestination state: HI or AK\nShipment still editable"
      }
    },
    {
      "type": "actions",
      "block_id": "hialaska-actions",
      "elements": [
        {
          "type": "button",
          "action_id": "usps_priority",
          "text": { "type": "plain_text", "text": "USPS Priority", "emoji": false },
          "value": "{\"v\":1,\"action\":\"usps_priority\",\"store_id\":\"19830\",\"order_key\":\"<order_key>\"}"
        }
      ]
    }
  ]
}
```

Add `"shipment_id":"<id>"` inside `value` only when the live record has a verified shipment id. Omit the `actions` block when the shipment is not an editable HI/AK shipment. Do not send a second button.

## Button payload the listener reads

Slack delivers the click as `block_actions`. The listener requires `type`, `channel.id`, `message.ts`, `message.thread_ts`, `actions[0].action_id`, and `actions[0].value`. Ignore other fields. `value` must parse as the JSON object above, with `v` equal to `1` and `action` equal to `usps_priority`. `store_id` must be `19830`. `order_key` must match the order message. Then re-read that order and apply the table.

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
      "block_id": "hialaska-actions",
      "value": "{\"v\":1,\"action\":\"usps_priority\",\"store_id\":\"19830\",\"order_key\":\"<order_key>\"}"
    }
  ]
}
```

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

`text` must be exactly `USPS Priority`, `guarded clone and submit`, or `unsent Gmail draft`.

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

The same two other labels may replace `USPS Priority` in that text. Nothing else maps.

After a mapped action, post the verified result or the exact blocker as a further reply tied to that order message. Do not edit the parent. Do not mark the shipment resolved because the reply was posted.
