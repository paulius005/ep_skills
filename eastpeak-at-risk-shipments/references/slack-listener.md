# Slack listener contract

Use this when a Slack reply on an at-risk order message is the trigger. Do not reply to East Peak Operations. Reply to every human @mention. An exact action label or a button runs a shipment action. Any other mention is a conversation: answer it in the thread. A conversation does not, by itself, change a shipment.

If the incoming message does not @mention East Peak Operations, stop with no Slack message. Do not post "No changes made". Do not explain order-message timestamps. Do not use Cursor's Send to Slack tool. A reply is posted only through `slack_poster.post_thread_reply` with the secret `SLACK_BOT_TOKEN` (`chat.postMessage`). Slack then shows East Peak Operations.

The listener posts as **East Peak Operations**, the same Slack app that posts the cards. The bot token is the secret `SLACK_BOT_TOKEN`. Do not create a second bot. Never print, log, or commit the token. When that token is present, resolve the bot user id with `auth.test` before deciding who spoke. The token stays on the Authorization header. Do not set `username` on the reply.

Ignore all of the following. None of them is a human action, and the listener does not reply to them:

- A message whose user id is the bot user id from `auth.test`.
- A message whose `username`, `bot_profile.name`, or `bot_profile.username` is East Peak Operations.
- A message with subtype `bot_message`.
- The daily parent (`At-risk shipments · [Date]`) and the order-card posts themselves, including the address before/after follow-up.

Require an @mention of East Peak Operations before replying or taking an action. Ignore channel messages and thread replies that do not mention that bot. A mention is the Slack form `<@bot user id>` or `<@bot user id|East Peak Operations>`. A human message that @mentions East Peak Operations still follows this skill: map it below, apply the decision tree in [the skill](../SKILL.md), and update that ShipMonk shipment only when the tree allows the update. The daily parent and the order message are reports. They do not change a shipment.

Read [the incident record](incident-record.md) and take the exclusive claim before any mutation. Re-read the live order immediately before writing. ShipMonk calls use the skill's API rules: curl or a non-Python-urllib client, East Peak store `19002` or Manual Store `18969`, secret `SHIPMONK_API_KEY` never printed. The order must be on the Action Required alert.

The order-message card is [the Slack blocks reference](slack-blocks.md). This file is the action map and the click contract.

## What the listener accepts

Channel **C0CCJJGG6HK** in the East Peak workspace only. Stop if the workspace or channel differs.

An action input names **one** order message, comes from a person, and is not one of the ignored bot posts above.

1. A Slack `block_actions` payload whose `channel.id` is `C0CCJJGG6HK`, whose `message.thread_ts` is the day's parent `ts`, and whose `message.ts` is that order message. The clicker is `user.id`. Ignore the click when that id is the bot. A button click is already aimed at East Peak Operations, so it does not need a second @mention in the text.
2. A message event whose `channel` is `C0CCJJGG6HK` and whose text @mentions East Peak Operations. After the mention is removed, an exact action label below is that shipment action. The same label after `<order message ts>` and one space is that action for the named order message. Any other remaining text is a conversation.
3. A conversation still needs the @mention. Answer the question, show what they asked to see, or change this skill when they ask you to adjust yourself. Do not run a shipment action unless the words clearly ask for one. If a shipment change names zero orders or more than one, ask which order and do not guess. A conversation or a skill change still gets a reply when it names no order.

A channel message or thread reply with no @mention does not map, even when the words are an allowed action. That includes the daily parent and every later parent the same day. Produce no Slack reply at all. Do not stay silent on a human @mention because the words are not an exact label, or because the message names no order.

Do not pick a shipment when the message names zero orders or more than one. Ask which order. Do not auto-merge orders, shipments, incidents, or Slack messages. Do not fold the reply or the result into the parent. One shipment change updates at most the one order that message already identified. A question, a request to see a draft, or a request to change the skill still gets a flexible reply when it @mentions East Peak Operations, including when it names no order.

## How a conversation is formatted

Post the reply with `slack_poster.post_thread_reply` and blocks from `conversation_blocks`. Do not post a paragraph. Do not use Cursor's Send to Slack tool.

1. Lead: one sentence, rendered bold. It answers the ask.
2. Bullets: the few facts they need, one per line.
3. Note: one context line, 75 characters or fewer, for the limit or the next step.

A request to adjust yourself uses that same shape. The lead says the skill was updated. The bullets say what changed. The note names a limit that stayed, or says the shipment was not changed.

## Return stage

Do not treat `processing_status` as the shipment stage when the order lists any `returns[].rma`. For each RMA, read `GET /v1/integrations/returns-list?rma={rma}`. Exact status `returned` means the shipment was returned, even when `processing_status` is still `en_route`. That order gets the draft-email button and does not get USPS Priority. Before a draft exists, the context line is `Draft an email to the customer.` After the draft is saved and read back, the line is `The draft email is in your inbox.` and the button is omitted. Do not match the substring "return" in a city, note, or tracking line. Other return statuses are not this gate.

## How a reply maps to an action

Match the button `action_id`, the exact action label, or plain language that clearly asks for that same action. Slack text does not establish the halted reason; the live ShipMonk reason does. A human @mention that matches none of these is `reason: conversation`. Reply to it. Do not update the shipment from a conversation unless they asked for one of these actions. `posted: false` from `--no-post` means the stock line was not sent. Silence is only for no mention, the bot, a report post, or the wrong channel.

| Reply | Existing action | What the tree then does |
| --- | --- | --- |
| `action_id` `usps_priority`, or label `USPS Priority` | Hawaii/Alaska USPS Priority selection | Verified HI/AK only, and the return status is not `returned`. If the exact live reason is `halted awaiting carrier processing`, the reply does not submit by itself: set USPS Priority on the eligible replacement, and clone and submit only after the duplicate, original, and cost gates. If the reason is anything else and the shipment is still editable, set USPS Priority, verify it, then save an unsent Gmail draft and never send it. If the shipment is not editable, or Priority cannot be verified, flag it, leave the service unchanged, and do not substitute another carrier. |
| Label `guarded clone and submit` | Replacement branch | Only when the exact live reason is `halted awaiting carrier processing`. Clone and submit only after the duplicate, original, and cost gates. For verified HI/AK, set USPS Priority on the eligible replacement before submission. Do not create a customer draft when that replacement succeeds unless separately requested. |
| Label `unsent Gmail draft` | Draft branch | Every reason other than that exact halted reason. For verified HI/AK, when the shipment is still editable and not returned, select and verify USPS Priority first, then save the draft. **DRAFT ONLY — NEVER SEND.** |
| `action_id` `draft_address_check`, or label `Draft an email to the customer`, or label `Draft address-check email` | Returned-shipment customer email | Only when the return status is exactly `returned`. Re-read the return before drafting. Save the unsent draft below from `hello@runeastpeak.com`. Do not send it. Do not change the shipping service. Then set the context line to `The draft email is in your inbox.` |

`USPS Priority` is the only Hawaii/Alaska service option this skill defines. Show it as a button only when the verified destination state is HI or AK (or the unambiguous full name), the shipment is still editable, the processing status is not `en_route` or `packed`, and the return status is not `returned`. Handed-off, returned, or otherwise uneditable HI/AK shipments are flagged in the order message and get no USPS Priority button. Do not add a FlavorCloud button or any other service button. Do not invent a button for clone, cancel, refund, or merge. The customer-email button is the one draft button, and only for return status `returned`. Its label is `Draft an email to the customer.` Its `action_id` stays `draft_address_check`. Do not add a button that edits the address. The address-line section is a report. It is not an action label, and it does not change `ship_to`.

A mapped reply is still not approval for a new charge. Unknown or uncovered fees stop for owner approval. Never charge the customer again.

## Address fix proposal

When a person asks what is wrong with an address, or asks how to correct it before they approve a change, the reply shows the before and after. Copy every ship-to line that would change. Label the old text Before and the new text After. If a line would be removed, show the old line and say the new line is empty. Do not describe the line only by its length. Leave email and phone out. Do not change the order in that proposal. Apply the change only after the person says to.

## Skill feedback

A reply in this channel that asks to change the skill is skill feedback. It is not one of the fixed shipment labels above. Do not update the ShipMonk shipment from the feedback alone, and do not auto-merge orders or shipments because of it. If the same message also asks for one named order's fixed draft or shipment action, do that fixed action too.

Update `SKILL.md` and the references so the feedback is part of the skill, then add those files to the repo and commit. Reply in the thread with `conversation_blocks`: a bold lead, bullets for what changed, and a context note. Leave the pull request unmerged unless the user asks to merge. Never commit or print the API key. If the feedback would send customer email, use FlavorCloud, skip the halted-reason gates, or charge the customer again, record the reply, say which limit stayed, and leave that part unchanged. A request to answer ordinary questions, or to adjust yourself, is not one of those limits. That reply is still sent when the message names no order. If the same message also asks for one named order's fixed draft or shipment action, do that fixed action too.

The fixed reply list and the flexible human reply live in [Reply baseline](../SKILL.md#reply-baseline). If an automation prompt still names the old returned-order subject `Can you double-check the address for order {order_number}?`, or treats an unmatched @mention as silence, follow the skill. The prompt should be changed to the current subject `shipping issue with order: #{order_number}` and to a reply on every human @mention.

The daily report posts an Address line 2 suggestion as its own reply under the daily parent. That reply is a report, not an action label. Do not map it to a shipment action, and do not edit the address because that reply exists. Changing the address remains outside this listener. The report only suggests the fix, as specified in the skill.

## Button payload on the order message

Post the order message with the Block Kit poster, which calls `chat.postMessage`. Do not use Cursor's Send to Slack tool for this report. `text` is the fallback. Put no email or phone in `text`, blocks, or `value`. The order card omits the street. The address follow-up is the exception: it shows the before and after street lines and still has no email or phone. The card footer is `Store {store_id} · {status}`. Store id may also be inside `value` and inside the ShipMonk URL.

`value` is a JSON string. `v` is `1`. `action` equals the `action_id`. `store_id` is `19002` or `18969`. `order_key` matches the order. Add `rma` only for `draft_address_check`. Add `shipment_id` only when the live record has a verified shipment id.

The **View order in ShipMonk** control is a link. It does not map to a shipment action and it has no `action_id`.

Include `usps_priority` only for an editable verified HI/AK shipment that is not returned, en route, or packed. Include `draft_address_check` only when the return status is exactly `returned` and no draft has been saved. Do not include both. The card layout is in [the Slack blocks reference](slack-blocks.md).

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
  "user": "<human user id>",
  "ts": "<reply ts>",
  "thread_ts": "<order message ts>",
  "text": "<@bot user id> USPS Priority"
}
```

The message must @mention East Peak Operations. After that mention is removed, an exact label is a shipment action: `USPS Priority`, `guarded clone and submit`, `unsent Gmail draft`, `Draft an email to the customer`, or `Draft address-check email`. Any other text is a conversation. The listener classifies it as `conversation` and does not post a stock acceptance line. Write the reply with `conversation_blocks` and post it with `slack_poster.post_thread_reply`. A `posted: false` result on a conversation means the stock line was not sent. It does not mean to stay silent.

Same-thread fallback, when the reply can only sit under the daily parent:

```json
{
  "type": "message",
  "channel": "C0CCJJGG6HK",
  "user": "<human user id>",
  "ts": "<reply ts>",
  "thread_ts": "<daily parent ts>",
  "text": "<@bot user id> <order message ts> USPS Priority"
}
```

The same other labels may replace `USPS Priority` in that text. Nothing else maps to a shipment action. Any other human @mention is a conversation, answered on that thread. A bot-authored copy of either payload does not map. When someone asks to see a draft, quote the saved unsent draft's subject and body in the thread, say it is in the inbox, and do not send it. The standing order card still omits the street, email, and phone.

After a mapped action, post the verified result or the exact blocker as a further reply tied to that order message. Post that reply with `slack_poster.post_thread_reply` (`chat.postMessage`) as East Peak Operations, using `SLACK_BOT_TOKEN`. Do not use Cursor's Send to Slack tool. Do not set a different `username`. Do not edit the parent. Do not mark the shipment resolved because the reply was posted. Do not answer the bot's own follow-up. A message with no @mention produces no reply.

## Draft address-check email

On `draft_address_check` only:

1. Re-read the return. If the status is no longer exactly `returned`, stop and say so. Do not draft from a stale button.
2. Re-read the order. The recipient is `customer_email` when the ship-to email is empty. If both are present and differ, or neither is present, stop and ask which address to use. Never guess.
3. The From account must be `hello@runeastpeak.com`. If that mailbox is not the one available, stop. Do not draft from another account.
4. Search hello@runeastpeak.com for an existing unsent draft for this order. Match the subject below, and also the previous subject `Can you double-check the address for order {order_number}?`. Update that draft in place, including when the subject changes. Do not save a second copy. If a matching message was already sent, stop and report it. Do not send another.
5. Save **DRAFT ONLY — NEVER SEND**. Read back the draft id, From, To, subject, body, and unsent state.
6. Reply on that order message: `The draft email is in your inbox.` Include the draft link when one exists. Do not include the address, email, or phone on that order card. Do not say the draft was sent. When a person asks to see the draft, quote the saved unsent subject and body in the thread and say it was not sent.

Subject, only for a returned order:

```
shipping issue with order: #{order_number}
```

Body:

```
Hi {first_name},

Your East Peak order {order_number} was returned to sender on {returned_date}. We have the package, and we haven't shipped it again.

The address on the label is:

{street1}
{street2 line only when present}
{city}, {state} {zip}

Would you look it over when you have a minute? Reply if we should send it there. If you'd like a different address on the label, reply with that address and we'll update it before we ship.

Thanks,
East Peak
```

Use the first name from the verified recipient. If it cannot be split safely, open with "Hi there,". `{returned_date}` is the return's received date in `America/Los_Angeles`, written as a calendar date. The address lines are the order's current ship-to, copied exactly. Do not claim the address failed validation, and do not invent a carrier reason. The known return reason may be unknown.

Say `was returned to sender`. Do not say `came back to us`. Do not use `If that's right, reply and let us know. If it isn't, reply with the corrected address.`

### Voice

No language guide named Thor is in this repo or in hello@runeastpeak.com. Write the returned-order draft in the short voice of sent mail from that mailbox, and in the usual support standard: fact first, specific, human, one next step.

- First name, contractions, and short sentences.
- Name the order, the return date, and that we have not shipped it again.
- Ask them to look the address over. A reply that it is right is enough, and then we send it again. If a line should change, they reply with the address they want.
- Sign `Thanks,` then `East Peak`. Do not sign as a teammate.

A saved draft is waiting for a person to review it. It does not reship the order and it does not clear the alert.
