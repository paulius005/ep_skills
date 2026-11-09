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

Post the reply with `slack_poster.post_thread_reply` and blocks from `conversation_blocks`. Do not post a paragraph. Do not use Cursor's Send to Slack tool. A request to see a saved draft does not use this shape. Use `draft_quote_blocks` for that reply, described below.

1. Lead: one sentence, rendered bold. It answers the ask in ordinary coworker English.
2. Bullets: the few facts they need, one per line. Do not repeat the lead. Do not put an email body, a street address, or any other copied passage into these bullets.
3. Note: one context line, 75 characters or fewer, for the limit or the next step.

### Voice

Write that reply the way a teammate would. Contractions and "I" and "you" are normal. Do not use Caterpillar English, Simplified Technical English, or any other controlled language. The 2026-10-31 instruction that human instructions use Caterpillar English is retired. On 2026-11-09 the ask was to talk like a person.

Say a limit once, in plain words. "An address-check draft is only saved when the return status is exactly returned" is retired wording. Do not use it to turn down an email. The card button is still only for a returned order. When a person asks for an email, check the shipment and ask a follow-up if the reason is not clear.

Order-card lines and button labels stay as written. Change the customer email only when they ask to change that email. This voice is for conversation replies. Still never say a draft was sent, and still never send it. If a memory still says to use Caterpillar English, follow this section and [Reply voice](../SKILL.md#reply-voice).

A request to adjust yourself uses that same shape. The lead says the skill was updated. The bullets say what changed. The note names a limit that stayed, or says the shipment was not changed. Write it in this voice.

## When a person asks for a draft

On 2026-11-09 the owner said not to refuse when someone asks for a customer email. Do not answer that the carrier still has the package, so no draft was saved.

1. Read the live shipment before you decide. That is the ShipMonk order, any return, the service, and the carrier's latest event when tracking is on the order or they shared a tracking page.
2. If that status makes the reason clear, save or update one unsent draft from `hello@runeastpeak.com`. A return status of exactly `returned` uses the returned-order template below. A carrier invalid-address or undeliverable scan is also a clear reason, even when the carrier still has the package and the order has no return. Say what the carrier reported. Do not say the order was returned.
3. If the status does not make the reason clear, ask what the email should cover. Do not guess a reason. Do not refuse the reply.
4. The card button is still only for a returned order. A person's ask uses this check instead of that refusal.
5. Still never send. Keep one unsent draft and update it in place. If both a ship-to email and a customer email exist and they differ, or neither exists, ask which address to use. Do not guess. If the ship-to email is empty, use the customer email.
6. The closing line does not reship the order, change the service, clone a replacement, charge the customer again, or clear the alert. Do not do those things because the draft says we will ship another out.

Closing line, for a returned order and for a carrier address problem:

```
If everything looks right, reply to confirm and we'll ship another out. Once you send the correct address, we'll ship another out.
```

Do not write `so we can work out the next steps.`

## Return stage

Do not treat `processing_status` as the shipment stage when the order lists any `returns[].rma`. For each RMA, read `GET /v1/integrations/returns-list?rma={rma}`. Exact status `returned` means the shipment was returned, even when `processing_status` is still `en_route`. That order gets the draft-email button and does not get USPS Priority. Before a draft exists, the context line is `Draft an email to the customer.` After the draft is saved and read back, the line is `The draft email is in your inbox.` and the button is omitted. Do not match the substring "return" in a city, note, or tracking line. Other return statuses are not this gate.

## How a reply maps to an action

Match the button `action_id`, the exact action label, or plain language that clearly asks for that same action. Slack text does not establish the halted reason; the live ShipMonk reason does. A human @mention that matches none of these is `reason: conversation`. Reply to it. Do not update the shipment from a conversation unless they asked for one of these actions. `posted: false` from `--no-post` means the stock line was not sent. Silence is only for no mention, the bot, a report post, or the wrong channel.

| Reply | Existing action | What the tree then does |
| --- | --- | --- |
| `action_id` `usps_priority`, or label `USPS Priority` | Hawaii/Alaska USPS Priority selection | Verified HI/AK only, and the return status is not `returned`. If the exact live reason is `halted awaiting carrier processing`, the reply does not submit by itself: set USPS Priority on the eligible replacement, and clone and submit only after the duplicate, original, and cost gates. If the reason is anything else and the shipment is still editable, set USPS Priority, verify it, then save an unsent Gmail draft and never send it. If the shipment is not editable, or Priority cannot be verified, flag it, leave the service unchanged, and do not substitute another carrier. |
| Label `guarded clone and submit` | Replacement branch | Only when the exact live reason is `halted awaiting carrier processing`. Clone and submit only after the duplicate, original, and cost gates. For verified HI/AK, set USPS Priority on the eligible replacement before submission. Do not create a customer draft when that replacement succeeds unless separately requested. |
| Label `unsent Gmail draft` | Draft branch | Every reason other than that exact halted reason. For verified HI/AK, when the shipment is still editable and not returned, select and verify USPS Priority first, then save the draft. **DRAFT ONLY — NEVER SEND.** |
| `action_id` `draft_address_check`, or label `Draft an email to the customer`, or label `Draft address-check email` | Returned-shipment customer email | The button runs only when the return status is exactly `returned`. Re-read the return before that draft. If a person asks for a customer email and the order is not returned, do not refuse. Follow [When a person asks for a draft](#when-a-person-asks-for-a-draft). Save the unsent draft from `hello@runeastpeak.com`. Do not send it. Do not change the shipping service. Then set the context line to `The draft email is in your inbox.` |
| Label `resolve as undeliverable` | Returned-order at-risk clear | Only when the return status is exactly `returned`, and only for that one order. POST `https://app.shipmonk.com/api/v1/orders/{shipmonkOrderId}/resolve-at-risk` with `{"resolveAs":"undeliverable"}` and the app JWT. Do not use the dialog default `enRoute`. Do not change the shipping service and do not send email. The integrations API key cannot make this call. If the JWT or the numeric order id is missing, stop and say the alert was not cleared. Read the call back before claiming it. Details are in [Resolve at risk as undeliverable](../SKILL.md#resolve-at-risk-as-undeliverable). |

`USPS Priority` is the only Hawaii/Alaska service option this skill defines. Show it as a button only when the verified destination state is HI or AK (or the unambiguous full name), the shipment is still editable, the processing status is not `en_route` or `packed`, and the return status is not `returned`. Handed-off, returned, or otherwise uneditable HI/AK shipments are flagged in the order message and get no USPS Priority button. Do not add a FlavorCloud button or any other service button. Do not invent a button for clone, cancel, refund, or merge. The customer-email button is the one draft button, and only for return status `returned`. Its label is `Draft an email to the customer.` Its `action_id` stays `draft_address_check`. Do not add a button that edits the address. The address-line section is a report. It is not an action label, and it does not change `ship_to`.

A mapped reply is still not approval for a new charge. Unknown or uncovered fees stop for owner approval. Never charge the customer again.

## Address fix proposal

When a person asks what is wrong with an address, or asks how to correct it before they approve a change, the reply shows the before and after. Copy every ship-to line that would change. Label the old text Before and the new text After. If a line would be removed, show the old line and say the new line is empty. Do not describe the line only by its length. Leave email and phone out. Do not change the order in that proposal. Apply the change only after the person says to.

## Stuck duration

A question about how long an order has been stuck is a conversation. Answer it from the order logs in [How long an order has been stuck](../SKILL.md#how-long-an-order-has-been-stuck). For Awaiting Carrier Processing, use [the carrier-wait assessment](../SKILL.md#awaiting-carrier-processing-for-more-than-10-days). The clock is the pickup log, or `shipped_at` when that log was not read. Do not answer it from `updated_at` or `ordered_at`. If the order is on that step and both clocks are missing, say the duration is not established. Leave address text out of the reply. The duration does not by itself change the shipment. When this job surfaced the order, `at_risk` is true, and the 10-day assessment is stuck, the action is clone one replacement and then resolve the original as undeliverable. A missing app JWT does not block that one replacement. If the replacement already exists, do not create another. When the original is still at risk, the Block Kit suggested action is `Order has been cloned. Please Resolve At Risk`. Use that sentence as the context note. Do not say the alert was cleared. The daily thread checks every at-risk order for `{order_number}-R1` and, when that order exists, the readout is `Order has been cloned.`

## Skill feedback

A reply in this channel that asks to change the skill is skill feedback. It is not one of the fixed shipment labels above. Do not update the ShipMonk shipment from the feedback alone, and do not auto-merge orders or shipments because of it. If the same message also asks for one named order's fixed draft or shipment action, do that fixed action too.

Update `SKILL.md` and the references so the feedback is part of the skill, then add those files to the repo and commit. Reply in the thread with `conversation_blocks`: a bold lead, bullets for what changed, and a context note, in the coworker voice above. Leave the pull request unmerged unless the user asks to merge. Never commit or print the API key. If the feedback would send customer email, use FlavorCloud, skip the halted-reason gates, or charge the customer again, record the reply, say which limit stayed, and leave that part unchanged. A request to answer ordinary questions, or to adjust yourself, is not one of those limits. That reply is still sent when the message names no order. If the same message also asks for one named order's fixed draft or shipment action, do that fixed action too.

The fixed reply list and the flexible human reply live in [Reply baseline](../SKILL.md#reply-baseline). If an automation prompt still names an old returned-order subject `Can you double-check the address for order {order_number}?` or `shipping issue with order: #{order_number}`, or treats an unmatched @mention as silence, follow the skill. The prompt should be changed to the current subject `Address Confirmation for Your East Peak Order #{order_number}` and to a reply on every human @mention.

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

The message must @mention East Peak Operations. After that mention is removed, an exact label is a shipment action: `USPS Priority`, `guarded clone and submit`, `unsent Gmail draft`, `Draft an email to the customer`, `Draft address-check email`, or `resolve as undeliverable`. Any other text is a conversation. A conversation that asks to resolve at risk for one returned order, and does not ask to change the skill, is still that resolve-as-undeliverable call. A request to learn the call or to change the skill does not POST, even when it names the order and the resolution. The listener classifies it as `conversation` and does not post a stock acceptance line. Write the reply with `conversation_blocks` and post it with `slack_poster.post_thread_reply`. A `posted: false` result on a conversation means the stock line was not sent. It does not mean to stay silent.

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

The same other labels may replace `USPS Priority` in that text. Nothing else maps to a shipment action. Any other human @mention is a conversation, answered on that thread. A bot-authored copy of either payload does not map. When someone asks to see a draft, post the saved unsent draft with `draft_quote_blocks`. Keep the subject, from, to, and body in one quote, with the body as paragraphs. Do not run that text through `conversation_blocks`, and do not turn each line into a bullet. Say it is in the inbox, and do not send it. The standing order card still omits the street, email, and phone.

After a mapped action, post the verified result or the exact blocker as a further reply tied to that order message. Post that reply with `slack_poster.post_thread_reply` (`chat.postMessage`) as East Peak Operations, using `SLACK_BOT_TOKEN`. Do not use Cursor's Send to Slack tool. Do not set a different `username`. Do not edit the parent. Do not mark the shipment resolved because the reply was posted. Do not answer the bot's own follow-up. A message with no @mention produces no reply.

## Draft address-check email

On `draft_address_check` only:

1. Re-read the return. If the status is no longer exactly `returned`, stop and say so. Do not draft from a stale button.
2. Re-read the order. The recipient is `customer_email` when the ship-to email is empty. If both are present and differ, or neither is present, stop and ask which address to use. Never guess.
3. The From account must be `hello@runeastpeak.com`. If that mailbox is not the one available, stop. Do not draft from another account.
4. Search `hello@runeastpeak.com` for an existing unsent draft for this order. That includes the subject below, any earlier returned-order draft for the same order, and the older subjects `shipping issue with order: #{order_number}` and `Can you double-check the address for order {order_number}?`. Update the newest unsent draft in place, including the subject. Do not open another draft while one is still unsent, and do not save a second copy. If a matching message was already sent, stop and report it. Do not send another and do not start a second draft cycle. Use the subject and body below. Capitalize the subject. Keep the note warm, natural, and short. Say the order was returned and acknowledge the hassle. Do not write `We have not shipped it again.` Include the ship-to address and the closing line: if it looks right, they reply to confirm and we'll ship another out; once they send the correct address, we'll ship another out. Do not write `so we can work out the next steps.` Use only verified facts. Do not guess a return reason or promise a ship date. Include `{returned_date}` only when the return record has that date.
5. Save **DRAFT ONLY — NEVER SEND**. Read back the draft id, From, To, subject, body, and unsent state.
6. Reply on that order message: `The draft email is in your inbox.` Include the draft link when one exists. Do not include the address, email, or phone on that order card. Do not say the draft was sent. When a person asks to see the draft, post it with `draft_quote_blocks` and say it was not sent.

Guidelines for every returned-to-sender draft. Adapt the template to the order. Do not send it.

- Use a properly capitalized, descriptive subject.
- Keep the tone warm, natural, and concise.
- Briefly explain that the order was returned and acknowledge the inconvenience.
- Avoid abrupt wording such as "We have not shipped it again." and "We haven't reshipped it."
- Include the shipping address and the closing line: if it looks right, they reply to confirm and we'll ship another out; once they send the correct address, we'll ship another out. Do not write `so we can work out the next steps.`
- Use only verified facts. Do not speculate about the return reason or promise a shipping date.

Subject, only for a returned order:

```
Address Confirmation for Your East Peak Order #{order_number}
```

Body:

```
Hi {first_name},

Your East Peak order #{order_number} was returned to us on {returned_date}. Sorry for the hassle—we'd love to help get this sorted.

Could you confirm that the shipping address below is correct?

{street1}
{street2 line only when present}
{city}, {state} {zip}

If everything looks right, reply to confirm and we'll ship another out. Once you send the correct address, we'll ship another out.

Thanks for your help!

East Peak
```

Use the first name from the verified recipient. If it cannot be split safely, open with "Hi there,". `{returned_date}` is the return's `received_at` in `America/Los_Angeles`, written as Month D, YYYY, such as October 21, 2026. If that date is missing, omit " on {returned_date}" and write `was returned to us` with no `on` clause. The address lines are the order's current ship-to, copied exactly. Omit street2 when it is empty. Do not claim the address failed validation, and do not invent a carrier reason. Leave `reason_unknown` and any other unverified return reason out of the draft.

Say the order was returned. Do not write `We have not shipped it again.` or `We haven't reshipped it.` Do not use `If that's right, reply and let us know. If it isn't, reply with the corrected address.` Do not use `so we can work out the next steps.` The closing line promises another shipment in the email. Saving the draft does not create that shipment.

### Voice

No language guide named Thor is in this repo or in hello@runeastpeak.com. Write the returned-order draft in the short voice of sent mail from that mailbox, and in the usual support standard: fact first, specific, human, one next step.

- First name, contractions, and short sentences.
- Name the order and the return date when that date is known. Acknowledge the hassle. Do not say the package has not shipped again.
- Ask them to confirm, and say we'll ship another out. If they send a correction, say we'll ship another out once we have it. Do not write `so we can work out the next steps.`
- Sign `Thanks for your help!` then `East Peak`. Do not sign as a teammate.

A saved draft is waiting for a person to review it. It does not reship the order and it does not clear the alert.
