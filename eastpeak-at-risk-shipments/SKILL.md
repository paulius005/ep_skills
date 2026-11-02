---
name: eastpeak-at-risk-shipments
description: Resolve East Peak ShipMonk Action Required orders using destination-specific USPS Priority routing, guarded replacements for the exact halted reason, and customer-specific Gmail drafts surfaced in Slack. Replies on each order message are the action input. Use for that alert queue, not the at_risk flag alone; excludes blanket alert cleanup and scheduler setup.
---

# East Peak at-risk shipments

Apply this workflow when the user authorizes resolving at-risk shipments. Loading or editing this skill alone does not authorize live execution. Honor any narrower current request, including research-only or draft-only scope. Never send customer email, cancel orders, issue refunds, change products or addresses, or add unrelated customer messages.

## Establish the queue and evidence

Use available connected tools; otherwise use supported browser controls. ShipMonk HTTP calls follow the [ShipMonk API](#shipmonk-api) rules: curl, or a client whose User-Agent is not Python-urllib, and secret `SHIPMONK_API_KEY` never printed. The queue is the ShipMonk app alert **Action Required** (the sidebar count on the orders list), not the `actions_required.at_risk` flag. That flag only means the order may miss its required ship-by date and is one reason inside the alert. Select an order when any `actions_required` flag is true, then confirm the set matches the app badge before acting. If the count differs, report both sets and do not add or drop orders to force a match. Store id `19830` is not East Peak and returns no orders. Live East Peak orders use store `19002`; East Peak - Manual Store is `18969`. If access or the alert cannot be verified, report the exact blocker without acting on a substitute set of orders.

For each incident, read the live risk/status and exact reason, order and shipment IDs and persistent links, destination state/country, recipient and items/quantities, service, editability, handoff state, original tracking and latest carrier events. When the question is how long the order has been stuck, read the order logs in [How long an order has been stuck](#how-long-an-order-has-been-stuck). Do not answer that from `processing_status`, `shipped_at`, or `updated_at`. Inspect existing replacements, prior fulfillment/charges, action records, Gmail drafts and matching correspondence, and the day's existing Slack parent thread and per-order action replies. Use the original order as the recipient/product source of truth. Keep customer personal data within the authorized operational records.

Before any mutation, read [the incident record and rerun contract](references/incident-record.md), establish its stable incident key and exclusive claim, and record the original state and intended action. When the trigger is a Slack reply, also read [the Slack listener contract](references/slack-listener.md) and map that reply before applying the tree. Re-read live state immediately before a consequential mutation; risk can change while researching. An unresolved previous attempt blocks another consequential attempt until reconciled.

## Decision tree and precedence

1. **Evidence, authorization, duplication, and cost gates come first.** Missing identity, ambiguous incident, uncertain prior mutation, a conflicting active original/replacement, or an unapproved financial commitment blocks the affected action. Continue safe research and surface the blocker. Never bypass a gate because a status or destination matches.
2. **Exact live status/reason `halted awaiting carrier processing`: use the replacement branch.** Do not use fuzzy matching, paraphrases, or customer/Slack text to establish this status. The saved authoritative value must match; if only a composite display is available, inspect its underlying status/reason before deciding. HI/AK is a service constraint within this branch, so configure USPS Priority on the eligible replacement before submitting.
3. **All other reasons: use the draft-and-Slack branch.** For Hawaii or Alaska, first choose USPS Priority on an eligible editable shipment and verify it. This destination rule does not by itself authorize cloning. A shipment already handed off or otherwise uneditable must be flagged, never described as rerouted. If USPS Priority is unavailable or eligibility is unclear, flag that exception; do not silently substitute another service. Continue the draft-and-Slack branch using the verified result or blocker.

Hawaii/Alaska means verified US destination state HI/AK (or its unambiguous full name), not a substring of a city or free-text note. Preserve the intended recipient, address, products, and quantities throughout. Selecting USPS Priority alone is not permission to release an otherwise held shipment.

Do not treat `processing_status` as the shipment stage when the order lists any `returns[].rma`. For each RMA, read `GET /v1/integrations/returns-list?rma={rma}`. The return's `status` is the stage. Exact status `returned` means the shipment was returned, even when `processing_status` is still `en_route`. The built-in action is then the address-check draft button in [the Slack listener reference](references/slack-listener.md). Do not offer USPS Priority, and do not describe the shipment as rerouted. The button creates a Gmail draft from `hello@runeastpeak.com` and never sends it. Clearing the at-risk flag on that returned order is a separate person-requested call, [resolve as undeliverable](#resolve-at-risk-as-undeliverable). The daily report does not make that call.

Do not use FlavorCloud. It is not an East Peak option for this skill: do not select it, do not offer it as a button, and do not substitute it when USPS Priority is unavailable or eligibility is unclear.

### Exact halted reason: guarded clone and submit

1. Inspect original tracking directly and any existing replacement by order reference, shipment lineage, recipient/items, and incident record. If the original has moved, been delivered, or been handed off, do not create a duplicate; flag the conflict for owner review. If an existing matching replacement is submitted or fulfilled, verify and record it without creating another. Resume a matching editable replacement only after establishing that it belongs to this incident and is not a different order.
2. Establish how the original is prevented from fulfilling alongside the replacement. A halted label alone is insufficient evidence that later processing cannot release it. Use verified platform behavior/state and the existing controls; if that cannot be established without an unrequested cancellation or other action, stop submission and flag the conflict. Do not cancel the original as a workaround.
3. Verify inventory and exact recipient, items, quantities, warehouse/store, and intended service. Inspect actual clone/submit behavior, charge implications, customer payment capture, and whether saved/queued records auto-submit. Never charge the customer again. Avoid duplicate charges and commitments. For any new financial commitment, record amount/currency and applicable approved spend limit. If no approved limit covers it, surface the amount for owner approval before commitment. Unknown fees require a quote or owner decision; do not treat blank/zero/pending estimates as free.
4. Clone once, preserving intended fulfillment details and linking original and replacement to the incident using supported fields/records. If clone itself submits or commits funds, apply all submission gates before cloning. For HI/AK, select verified USPS Priority on the eligible replacement and verify it **before submission**. If the service cannot be set, stop; do not submit using an inherited/default service.
5. Submit only within the user's authorized scope and after the duplicate-fulfillment and cost gates pass. Treat any automatic submission timer as a consequential submission. Read back persisted replacement ID/link, recipient, SKU quantities, service, fees and actual status. Report queued, submitted, handed off and delivered distinctly. Never claim dispatch from submission alone.

Report every attempted or taken action in this branch, including successful replacements, blocked actions, failures and uncertain outcomes, in the daily Slack thread defined below. Do not automatically create a customer email for a successful halted replacement; state that no customer draft was created unless separately requested. Record unresolved risk and the next step.

### Replacement after 10 days on Awaiting Carrier Processing

The owner ordered this path on 2026-11-01 and set the wait to 10 days on 2026-11-02. It sits beside the halted-reason branch. It does not turn every in-transit order into a replacement. Use it when this job surfaces an order with `actions_required.at_risk` true and `assess_awaiting_carrier_processing` says it is stuck. That assessment covers `processing_status` `awaiting_carrier_processing` or `en_route`, with no return status `returned`, for more than 10 days after submission. If that duration cannot be verified, do not clone. If the app JWT is missing, still clone. Do not call resolve. The order card context line is `Order has been cloned. Please Resolve At Risk`. The daily readout uses the separate clone check below and says `Order has been cloned.`

1. Create one replacement with `POST /v1/integrations/order`. Use a new `order_number` `{order}-R1` and a new `order_key` `{order}-reship-YYYYMMDD`. Keep the same store, warehouse, ship-to, sku, quantity, price, and requested service. Create it as `onHold`. Do not reuse the original `order_key`.
2. Read it back. If the sku, quantity, destination state, or store does not match, stop and do not submit.
3. Submit that new key with `POST /v1/integrations/submit-order`. On 2026-11-01, sending `unfulfilled` on the upsert left the order `onHold`. The submit call moved it to `queued_to_submit`. `queued_to_submit` is not shipped.
4. Then resolve the original as undeliverable with the app call below. This path uses `undeliverable` even when the order has no return. If the app JWT is missing, leave the original alert on. Do not cancel the original. Set `cloned` on the original card. Its context line is `Order has been cloned. Please Resolve At Risk`.
5. One replacement. If `{order}-R1` already exists, do not create another. Do not send email. Do not use FlavorCloud. The daily thread still checks for that replacement and says `Order has been cloned.`

Order 8274 did not match the halted reason. On 2026-11-01 it was fulfilled and `en_route`, and OnTrac had reported that the package could not be located. The owner ordered the clone anyway. The replacement is `8274-R1`, order key `8274-reship-20261101`, store 19002, sku `006-IBW2-XL` quantity 1, California, requested service Standard. Readback was `unfulfilled` and `queued_to_submit`. On 2026-11-02 it was still `queued_to_submit`. Do not create `8274-R2`. Original 8274 stayed fulfilled, `en_route`, and `at_risk`, with `updated_at` `2026-10-21T06:35:22+00:00`. It was not resolved. The daily readout for 8274 says `Order has been cloned.`

### Other reasons: Gmail DRAFT ONLY, then Slack

1. Research the original order, carrier tracking/events, relevant ShipMonk history and customer-specific correspondence enough to explain this customer's actual issue. Distinguish verified facts from hypotheses and avoid unsupported delivery promises or claims that actions happened.
2. Resolve the buyer/recipient from the original order and matching correspondence, including Reply-To and the appropriate existing thread. If they conflict or cannot be verified, stop draft creation and surface the recipient decision needed; never guess an email address or use a no-reply sender. When available, use the recipient-resolution and writing-style guidance in the execution environment and relevant prior sent replies. Otherwise use concise, plain language without inventing a personal style. A returned order uses the address-check subject and body in [the listener contract](references/slack-listener.md). The subject is `Address Confirmation for Your East Peak Order #{order_number}`. Say the order was returned. Do not write `We have not shipped it again.`
3. Find an existing unsent draft for this order/shipment/incident, including one whose subject is still `Can you double-check the address for order {order_number}?` or `shipping issue with order: #{order_number}`. Update it in place after checking its account, recipient, subject and thread; preserve unrelated owner edits or flag conflicts. If one was already sent, treat it as correspondence and reassess whether further outreach is needed; never resend it or silently start another cycle. Create a new draft only when no matching unsent draft exists and outreach is still appropriate. Do not save a second unsent copy when the subject changes.
4. Save **DRAFT ONLY — NEVER SEND**. Verify by readback the saved draft ID, account, thread, recipients, subject, body, relevant links and unsent/DRAFT state. Use a real draft or thread link where available; otherwise supply the verified account, subject and draft reference without inventing a URL. An unsaved editor is not a saved draft. Record any blocked draft explicitly.
5. Report in the shared daily Slack thread using the procedure below; never create separate top-level posts or parent threads per order.
6. Surface: order link; order/shipment incident reference; exact risk reason and relevant verified tracking facts; action taken or proposed; draft reference/link and DRAFT-only status (or exact draft blocker); approval needed and next step. Include only the minimum customer data necessary: omit full address, email, phone, and unnecessary personal details. Clearly separate a proposed action from a completed action. A Slack summary is not a customer message.

A human @mention of East Peak Operations in `#at-risk-shipments` gets a reply in that thread. Exact labels and button clicks are the built-in shipment actions in [the listener contract](references/slack-listener.md). Plain language that clearly asks for the same action is that action. Any other mention is a conversation: answer the question or make the change they asked for. Do not stay silent because the wording is not one of the five labels. A conversation does not by itself change a shipment, send mail, or spend money. The East Peak Operations bot's own posts are not replies. A mapped shipment action still does not bypass the decision tree, the duplicate, original, or cost gates, or the ban on sending mail. Use direct trusted owner authorization for spend or other decisions outside this workflow. A draft or Slack post does not resolve the shipment risk and does not justify dismissing its alert. Sending the customer email does not clear it either. `actions_required.at_risk` on `api.shipmonk.com` is a read-only output. The app clears it with `POST https://app.shipmonk.com/api/v1/orders/{orderId}/resolve-at-risk` and body `{"resolveAs":"undeliverable"}`. `resolveAs` is `enRoute`, `shippedUntrackable`, `delivered`, or `undeliverable`. For a returned in-transit order, the owner uses `undeliverable`. `{orderId}` is the app's internal order id, not `order_key` and not the customer order number. That call needs the app session `Authorization: Bearer` token. `SHIPMONK_API_KEY` is rejected there with `The provided API key cannot be used for this operation.` Do not send the integrations key to that path, and do not guess the order id. On 2026-11-01, order 8257 stayed `at_risk` because this runtime only has the integrations key. There is no order 8527.

## One daily Slack thread for all actions

This reporting rule applies to **every branch and every attempted or taken operational action**, including routing edits, clone/save/submit, draft creation/update, blocked or denied attempts, failures and uncertain outcomes. Successful halted replacements must appear too. Use **one daily parent thread** for all orders in **#at-risk-shipments**, never separate top-level posts per order. **Each Action Required order is its own Slack message, posted as a reply in that thread.** Do not fold shipment text, buttons, or results into the parent.

1. Verify the **East Peak workspace** and channel **C0CCJJGG6HK** at [the configured channel](https://east-peak-workspace.slack.com/archives/C0CCJJGG6HK). Stop posting if workspace/channel identity differs. Use the explicitly configured reporting timezone **`America/Los_Angeles` (Pacific)** for this user unless the user changes it. Compute the actual Pacific calendar date at run time in that timezone, including daylight-saving changes, and persist the timezone and date; do not use a hardcoded example date or silently switch day boundaries between workers or runs.
2. Before creating a parent, consult the durable daily-thread record and search the channel for the day's existing parent. Verify its channel, date and parent message, then reuse it. One parent per Pacific day. On a rerun the same day, reuse that same parent. If multiple candidate parents exist, reconcile rather than adding another. If none exists, claim the daily key atomically, recheck, and create exactly one parent with the [Block Kit poster](#post-with-the-block-kit-poster). The header is **`At-risk shipments · [Date]`**, with a warning mark, replacing `[Date]` with that Pacific calendar date as a short month and day (`Oct 30`). The parent also has the summary lines, the quote count, and the thread link in [the Slack blocks reference](references/slack-blocks.md). It has no per-order card. An uncertain parent creation requires readback/search before retrying.
3. Persist and read back the verified workspace ID, channel ID, reporting date/timezone, parent message timestamp/`thread_ts` and real permalink. Post one reply per Action Required order under that parent. The parent header stays `At-risk shipments · [Date]`; the orders in the thread are the Action Required alert. The daily record is shared across incidents and workers. An existing incident from a prior day uses today's parent for new actions, with references to prior entries when useful. On rerun, reuse the shipment's existing order message for that day instead of posting a second one.
4. For every Action Required order, including every at-risk shipment, check whether it has already been cloned before writing the card. This check is part of every daily instruction set. Look up order number `{order_number}-R1` on that order's store with `GET /v1/integrations/orders-list` and `orderNumbers`. Use `existing_clone_number` in `slack_poster/blocks.py`. If that order exists, set `daily_cloned` and the daily readout is `Order has been cloned.` Do not create another clone from the check. Do not post the `-R1` order as its own card unless it has its own `actions_required` flag. A returned order still uses the draft context line. Then write each order message with [How to write each reply](#how-to-write-each-reply) and post it through the Block Kit poster, using [the Slack blocks reference](references/slack-blocks.md). Keep the order link, order number, status tag, route, service, context line, and footer. Also include the exact reason, attempted or taken action, verified result or the blocked, denied, failed, or uncertain outcome. For a verified editable HI/AK shipment, include the USPS Priority button. For return status exactly `returned`, include the draft-email button instead. When a draft was saved and read back, the context line is `The draft email is in your inbox.` Never represent a Gmail draft as sent, a timeout as failure or success without evidence, or a proposed action as completed. Include failed attempts and uncertain outcomes even when no mutation can be verified. Omit secrets and unnecessary customer data. Keep email and phone out of the message. Keep the street off the order card. An address-line fix is its own follow-up section with `Before:` and `After:`.
5. Deduplicate reporting by stable incident/action/attempt reference and its persisted reply ID. On rerun, read back the existing order message and update it only for a changed outcome instead of appending a duplicate shipment message; retain the earlier failure/uncertainty history when reconciling. A distinct authorized retry gets its own attempt reference and its own reply tied to that order message, still under the same daily parent. Read back each Slack create/update and persist its channel, parent and reply identifiers/permalink. If reporting times out, reconcile before retrying. If Slack reporting is blocked or uncertain, record the pending report and exact blocker in the ledger and completion handoff; never claim it was posted or recursively try to report a reporting failure. Reconcile pending reports into their recorded daily parent when access returns.

## Reply baseline

Two layers. The fixed layer is the only one that can change a shipment or save a draft. The flexible layer answers a person and does not invent a shipment action.

Every reply that is sent uses the same shape: one bold lead sentence, a short bullet list, and one context note of 75 characters or fewer, via `conversation_blocks` and `post_thread_reply` in channel `C0CCJJGG6HK`, in the same thread. Do not answer in a single paragraph. Do not set a username.

Stay silent only for these:

- No @mention of East Peak Operations.
- A post from East Peak Operations, subtype `bot_message`, or a bot profile with that name.
- The daily parent and the order cards, including the address before/after follow-up.
- A different workspace or channel.

`slack_listener --no-post` returns `posted: false` for every event. That only means the command did not send a stock line. A `conversation` result still gets a flexible reply from the agent. A `bot`, `report_post`, `no_mention`, or `wrong_channel` result gets nothing.

### Fixed shipment replies

These are the only shipment actions. Match the button or the exact label. Do not paraphrase a shipment change out of free text. One shipment change names one order. Zero orders or more than one: ask which order, and do not change a shipment.

| Reply | Fixed result |
| --- | --- |
| `USPS Priority` or `usps_priority` | Set USPS Priority only when the tree allows it. Otherwise leave the service and say why. |
| `guarded clone and submit` | Clone and submit only after the halted-reason, duplicate, original, and cost gates. Otherwise name the gate that stopped it. |
| `unsent Gmail draft` | Save or update one unsent draft. Never send it. |
| `Draft an email to the customer`, `Draft address-check email`, or `draft_address_check` | Returned status only. Save or update the address-check draft below. Context note: `The draft email is in your inbox.` |
| `resolve as undeliverable` | Returned status only. POST the app resolve-at-risk call below with `resolveAs` `undeliverable`. If the app JWT is missing, leave the alert and say so. |

Fixed context lines on the order card:

- In transit, service unchanged: `Service unchanged — shipment already en route.`
- The daily clone check finds `{order_number}-R1`: `Order has been cloned.` Set `daily_cloned`. This is the daily readout.
- Returned, before a draft: `Draft an email to the customer.`
- After that draft is saved and read back: `The draft email is in your inbox.`
- Address line 2 over 50 characters: `Address 2 exceeded limit of 50 characters.`
- A verified replacement exists and the original is still at risk: `Order has been cloned. Please Resolve At Risk`. Set `replacement_pending_resolve` on that order card. Do not add a button for it.

The returned-order customer draft has one subject and one body, in [the listener contract](references/slack-listener.md). Subject: `Address Confirmation for Your East Peak Order #{order_number}`. Say the order was returned. Do not write `We have not shipped it again.` Keep one unsent draft per order and update it in place, including when the subject changes. Do not save a second copy. If a matching message was already sent, stop. A request to "drop a new draft" means new wording in that one unsent draft, not a second draft and not a send.

If an older unsent draft with the previous subject is still in the mailbox, leave it unsent and do not create another. The review copy is the draft whose subject is the current subject. Do not send either.

### Flexible human replies

Any other @mention is a conversation. `classify` returns `action: null` and `reason: conversation`. Answer the question. Do not change a shipment unless the message also uses a fixed label above for one order, or it asks to resolve at risk for one returned order. That resolve request is [resolve as undeliverable](#resolve-at-risk-as-undeliverable). A request to learn that call, or to change this skill, does not POST it.

Fixed conversation patterns, still written as a flexible reply:

- They ask to see a draft: quote the saved unsent subject and body, say it was not sent, and use the context note `The draft email is in your inbox.` The order card still omits the street, email, and phone. The quote is only for that ask.
- They ask to change this skill or how replies work: update this skill and its references, commit, and say what changed. Do not merge unless they ask. If that same message also asks for one named order's fixed draft or shipment action, do that too. The skill edit alone does not change a shipment.
- A shipment change names zero orders or more than one: ask which order. Change nothing.

Anything else: answer in the same block shape. Do not send customer email, use FlavorCloud, skip the halted-reason gates, charge the customer again, or invent a shipment action. The owner-ordered [10-day awaiting-carrier path](#replacement-after-10-days-on-awaiting-carrier-processing) is the one added replacement path. It does not waive those limits for any other reason.

If an automation prompt still requires the old subject `Can you double-check the address for order {order_number}?`, or treats `posted: false` as silence on a human @mention, follow this section. The prompt should be edited to match it.

## Slack listener

Do not reply to East Peak Operations. Reply to every human @mention, including when the text is not an exact action label. A shipment action happens only when that reply uses a fixed label above. Every other @mention gets the flexible reply. If the incoming message does not @mention East Peak Operations, stop with no Slack message. Do not post "No changes made". Do not explain order-message timestamps. Do not answer the daily parent or an order card. The listener posts as East Peak Operations. The bot token is the secret `SLACK_BOT_TOKEN`. Do not create a second bot. Never print, log, or commit the token.

Do not use Cursor's Send to Slack tool for a reply. Post a reply only through `slack_poster.post_thread_reply`, which calls `chat.postMessage` with the secret `SLACK_BOT_TOKEN`. Slack then shows East Peak Operations. Do not set `username`. Do not create a second bot. Never print, log, or commit the token.

Ignore the bot. When `SLACK_BOT_TOKEN` is present, resolve the bot user id with `auth.test` and do not print the token. Also ignore a message whose user id is that bot, a message whose username or bot profile name is East Peak Operations, a message with subtype `bot_message`, and the daily parent and order-card posts themselves. The bot must not reply to its own messages.

A human message that @mentions East Peak Operations still follows this skill. A button click on the order card still maps, and that click does not need a second @mention. Map the reply with [the Slack listener contract](references/slack-listener.md), apply the decision tree in this document, and update that ShipMonk shipment only when the tree allows the update. Posting the daily parent or the order message does not itself change the shipment.

These replies are the built-in shipment actions. A button click uses the `action_id`. A text reply uses the exact label, or plain language that clearly asks for that same action. A question or other request is a conversation: answer it in the thread and do not run a shipment action unless they asked for one.

- Button `usps_priority`, or reply text **`USPS Priority`**: the existing Hawaii/Alaska option. Offer that button only when the verified destination is HI/AK and the shipment is still editable. This skill defines no other HI/AK service option, so the message has no other service button. FlavorCloud is not a button. If this reply arrives and the exact halted reason also applies, the button does not submit by itself: set USPS Priority on the eligible replacement, and clone and submit only after the duplicate, original, and cost gates. If the reason is anything else and the shipment is still editable, set USPS Priority, verify it, then continue the unsent-draft branch. If the shipment is not editable, or Priority cannot be verified, flag that exception and do not change service.
- Reply text **`guarded clone and submit`**: the replacement branch, and only when the exact live reason is `halted awaiting carrier processing`. Clone and submit only after the duplicate, original, and cost gates. For HI/AK, set USPS Priority on the eligible replacement before submission. Do not create a customer draft for a successful halted replacement unless separately requested.
- Reply text **`unsent Gmail draft`**: the draft branch for every reason other than that exact halted reason. If the destination is verified HI/AK and the shipment is still editable, select and verify USPS Priority first, then save the draft. **DRAFT ONLY — NEVER SEND.**
- Button `draft_address_check`, or reply text **`Draft an email to the customer`** or **`Draft address-check email`**: only when the return status is exactly `returned`. Save the unsent draft from `hello@runeastpeak.com` defined in the listener contract. Do not send it, and do not change the shipping service. Then set the context line to `The draft email is in your inbox.`
- Reply text **`resolve as undeliverable`**, or a request to resolve at risk / clear the at-risk flag for one returned order: the [resolve-at-risk call](#resolve-at-risk-as-undeliverable). One order. Do not change the shipping service and do not send email.

Returned-order drafts use that address-confirmation template for later cases too. The subject is `Address Confirmation for Your East Peak Order #{order_number}`. Say the order was returned, include the return date only when the return received date is known, apologize briefly, and ask them to confirm the current ship-to address or send a correction. Use only verified facts. Do not guess a return reason or promise a ship date. Do not write "We have not shipped it again." or "We haven't reshipped it." Adapt the first name, order number, date, and address to the order. Still draft only, still from `hello@runeastpeak.com`, and still no service change.

Any other @mention is the flexible reply in [Reply baseline](#reply-baseline). It maps to no shipment action by itself. Answer it, including when the message names no order. A channel message or thread reply with no @mention gets no Slack message. Every post from East Peak Operations is ignored. Do not invent a shipment action from free text. Do not auto-merge orders, shipments, incidents, or Slack messages. One shipment change applies to one order. If a shipment change names zero orders or more than one, ask which order and do not guess. A reply is not owner approval for a new charge; the cost gate still applies.

Format a conversation reply with `conversation_blocks` and post it with `slack_poster.post_thread_reply`, passing those blocks. The lead is one bold sentence. The next block is a short bullet list. The note is one context line of 75 characters or fewer. Do not answer in a single paragraph. The plain-text fallback carries the same lines. Do not set a username.

When someone asks to see a draft, that reply is the exception. Read the saved unsent draft and post it with `draft_quote_blocks`. The email stays in one quote: subject, from, to, then the body as paragraphs. Do not pass those lines to `conversation_blocks`. Do not turn each sentence or address line into a bullet. Say that it was not sent. Do not send it. The standing order card still omits the street, email, and phone. A draft quote is only for that ask.

A reply that asks to change this skill, or asks you to adjust yourself, updates this skill and its references, then is committed. Reply in the thread with what changed and which limit stayed. Do not merge unless they ask. Never commit or print `SHIPMONK_API_KEY` or `SLACK_BOT_TOKEN`. Do not apply feedback that would send customer email, use FlavorCloud, skip the halted-reason gates, or charge the customer again. Say which limit stayed and leave that part unchanged. If the same message also names one order and a fixed shipment reply, do that fixed reply as well. The skill edit does not itself change the shipment. A skill-feedback message that names no order still gets that reply.

## ShipMonk API

East Peak store id on live orders is `19002`. East Peak - Manual Store is `18969`. Store id `19830` returns an empty list and is not this account's East Peak store. The API key is the runtime secret `SHIPMONK_API_KEY`. Never print, log, or commit the key, and never put it in source, notes, chat, Slack, shell transcripts, or the incident record. Pass it only as the `Api-Key` header from the runtime secret. Do not use `curl -v` or any mode that records request headers.

Call ShipMonk with curl, or with another client whose User-Agent is not Python-urllib. `Python-urllib/3.12` is rejected by Cloudflare with HTTP 403 error 1010 (`browser_signature_banned`). curl 8.5.0 against `GET /v1/integrations/orders-list` with `Api-Key` and `Accept: application/json` returned HTTP 200 from the East Peak cloud environment. The same call filtered to `storeIds[]=19830` also returned HTTP 200 and an empty order list. Send `Accept: application/json`. Production host is `https://api.shipmonk.com`. Docs index: `https://apidocs.shipmonk.com/llms.txt`.

Read orders with the documented `GET /v1/integrations/orders-list`. The list has no Action Required query parameter. Page the account (or stores `19002` and `18969`) and keep orders where at least one `actions_required` flag is true. Do not keep an order only because `at_risk` is true, and do not drop an order because `at_risk` is false. On 2026-10-30 a full read returned 5629 orders, the same total as the app, with 4 orders having any flag true, while the app badge showed 5. Reconcile that difference before acting. The documented processing status `awaiting_carrier_processing` is not, by itself, the exact reason `halted awaiting carrier processing`. Confirm the exact live reason before the replacement branch. The order page can show status En Route while the active timeline step is Awaiting Carrier Processing. That title is not the halted-reason string. Whether that step has lasted more than 10 days after submission is [the carrier-wait assessment](#awaiting-carrier-processing-for-more-than-10-days). An at-risk order that meets it is cloned, and the original is resolved, in [that same section](#awaiting-carrier-processing-for-more-than-10-days).

The documented order write is the upsert `POST /v1/integrations/order`, not a partial PATCH. Retrieve and reconcile the complete required representation and preserve fields before writing, then read the order back. Never invent endpoints, payload fields, idempotency headers, or a USPS Priority service id. A shipping method on the order has an integer `id` and a `name`; use an id verified from the live account, not a guessed constant. If semantics or preservation cannot be established, stop the API mutation and flag it. That upsert does not clear `actions_required.at_risk` and does not set `processing_status`. The only verified clear for a returned at-risk order is the app call in [Resolve at risk as undeliverable](#resolve-at-risk-as-undeliverable). `SHIPMONK_API_KEY` cannot make that call.

### How long an order has been stuck

Do not measure a stuck interval from `processing_status` alone, from `updated_at`, or from the carrier tracking page. Pull the order logs when the app session can read them. `GET /v1/integrations/orders` has no log list. `GET /api/v1/orders/{id}/logs` is not a route (HTTP 404). The app bundle posts:

`POST https://app.shipmonk.com/api/v1/log-events`

JSON body: `{"entityName":"order","entityId":"{shipmonkOrderId}","paginator":{"page":1,"pageSize":100}}`. `{shipmonkOrderId}` is the numeric id in `/orders/order/{id}/logs`, sent as a string. It is not the order number and not `order_key`. `entityName` is `order`. `page` is at least 1. `pageSize` is at most 1000. Read every page until the paginator is finished or the stage-entry row is found. Each row has `datetime` (ISO-8601 with an offset), `user`, and `message`.

Auth is `Authorization: Bearer` with the logged-in app JWT. On 2026-11-02 `Api-Key` on that URL returned HTTP 401 `The provided API key cannot be used for this operation.` Do not substitute `SHIPMONK_API_KEY`. Do not invent a JWT. If the id is not verified, do not call. If the JWT is missing, the pickup log was not read. For the Awaiting Carrier Processing question, use `shipped_at` from the integrations order as described below. Do not use `ordered_at` or `updated_at` in its place.

The same app order payload includes `statusTimeline`. Each step has `status` (`passed`, `active`, `completed`, `warning`, `alert`, or `upcoming`), `title`, and a nullable `subtitle`. The active or warning step is the current milestone. Its subtitle is a date when the page shows one. That timeline is on `GET https://app.shipmonk.com/api/v1/orders/{shipmonkOrderId}`, which also rejects the integrations key. The timeline between Picked Up and Delivered is titled Awaiting Carrier Processing. It has no En Route step. The status badge can say En Route while that step is still current.

The stuck clock starts at the log row that entered the current step. For Awaiting Carrier Processing, that row is the pickup line, such as `Marked order {order_number} as picked up`. A later `moved to At-Risk` row is not the start. Order creation and the submission row are not the start. Report the start `datetime` with its offset, and the elapsed time to now in `America/Los_Angeles`.

### Awaiting carrier processing for more than 10 days

Use `assess_awaiting_carrier_processing` in `eastpeak-at-risk-shipments/carrier_wait.py`. The order is on that step when `processing_status` is `awaiting_carrier_processing` or `en_route`, and no return has status exactly `returned`. Delivered, cancelled, and undeliverable orders are not on that step. A packed or submitted order is not on it yet.

The clock is the pickup log when those rows were read. When they were not, the clock is `shipped_at`. Both are after submission: a shipment timestamp is not order creation. `ordered_at` and `updated_at` are not the clock. More than 10 days means the elapsed time is greater than 10 times 24 hours. Ten days exactly is not more than 10. If the order is on the step and both the pickup log and `shipped_at` are missing, the duration is not established. Do not fill it in.

On 2026-11-01, order 8274 (store `19002`, order key `18933995667587`) was fulfilled, `en_route`, with `actions_required.at_risk` true, `shipped_at` `2026-10-10T17:57:31+00:00`, and no return. Counted from `shipped_at` to 2026-11-02 02:47 UTC, that is 22.4 days, so it is past 10 days. The pickup log on the page was 2026-10-11 00:38 UTC. The at-risk log was `updated_at` `2026-10-21T06:35:22+00:00` and is not the clock.

When this job surfaces that order, and `at_risk` is true, and the assessment is stuck, `at_risk_job_action` returns `clone_and_resolve_original`. Clone one replacement. Keep the recipient, items, quantities, and store. Do not capture a new payment from the customer. Do not clone if a matching replacement already exists. After the replacement is read back, resolve the original order, not the clone, with `POST https://app.shipmonk.com/api/v1/orders/{shipmonkOrderId}/resolve-at-risk` and `{"resolveAs":"undeliverable"}`.

"At risk" is the flag on the original. It is not a `resolveAs` value. The dialog values are `enRoute`, `shippedUntrackable`, `delivered`, and `undeliverable`. This replacement uses `undeliverable` for the original. The app JWT is required for that call. The integrations key returns HTTP 401. If the JWT is missing, still clone, and do not call resolve. Set `cloned` on the original card. Its context line is `Order has been cloned. Please Resolve At Risk`. A saved assessment does not itself submit the clone. The daily readout still says `Order has been cloned.` after the clone check.

Log text can contain a ship-to change. Do not copy an address, email, or phone from a log into Slack, this skill, or the incident ledger. Keep the timestamp, the user label, and a short description of the event.

On 2026-11-01 the logs page for order 8274 showed app order id `2228133536` (store `19002`, order key `18933995667587`). The timeline's active step was Awaiting Carrier Processing. Picked Up was dated 10/10/2026. The pickup log was 10/10/2026 8:38 PM EDT: marked the order picked up. The at-risk log was 10/21/2026 2:35 AM EDT. The stuck clock is the pickup log. This runtime could not read those rows through the API. The page was the source. No shipment was changed from that read.

A duration does not pass the halted-reason, duplicate, original, or cost gates. Outside `clone_and_resolve_original`, it does not authorize a clone, a resolve-at-risk call, or a new charge. The daily clone check does not authorize another clone.

### Resolve at risk as undeliverable

The ShipMonk app button **Resolve At Risk** is an app-session call, not an integrations upsert. The dialog options and their `resolveAs` values are `enRoute`, `shippedUntrackable`, `delivered`, and `undeliverable`. The dialog opens on `enRoute`. For an order whose return `status` is exactly `returned`, this skill uses `undeliverable` only. Do not send `enRoute`, `delivered`, or `shippedUntrackable` for that order. Do not change the shipping service. Do not send customer email. A sent customer email still does not clear the alert by itself.

Call when a person asks to resolve that one returned order, or uses the exact label `resolve as undeliverable` for one order. A message that asks to learn this call or to update the skill does not POST, even when it names the order and the resolution. The next request to resolve that order is the call.

`POST https://app.shipmonk.com/api/v1/orders/{shipmonkOrderId}/resolve-at-risk`

JSON body: `{"resolveAs":"undeliverable"}`. Method and body are what the app bundle sends (`app.shipmonk.com/build/app.js`). `{shipmonkOrderId}` is the numeric id in `/orders/order/{id}/information`. The integrations order payload does not include that id. Do not guess it. If the id is not verified, stop before the POST.

Auth is `Authorization: Bearer` with the logged-in app JWT, plus `Content-Type: application/json`. The app also sends `X-Frontend-Version`. That JWT comes from `POST /api/v1/token/authenticate` with a username and password. It is not the integrations key. On 2026-11-02, `POST https://app.shipmonk.com/api/v1/orders/0/resolve-at-risk` with `Api-Key: SHIPMONK_API_KEY` and `{"resolveAs":"undeliverable"}` returned HTTP 401 `The provided API key cannot be used for this operation.` The same key as a Bearer token returned HTTP 401 `Invalid JWT Token`. `POST https://api.shipmonk.com/v1/orders/0/resolve-at-risk` returned HTTP 405, so the public host has no such write. The public order read still works and still has no numeric order id. Do not substitute `SHIPMONK_API_KEY`. Do not invent a JWT. Do not call `POST /api/v1/orders/batch/resolve-at-risk`.

If the return status is not exactly `returned`, do not pick a `resolveAs`, except the owner-ordered 10-day awaiting-carrier path, which uses `undeliverable` after its replacement is queued. Otherwise ask which of the four values they want, and do not call. Zero orders or more than one: ask which order and do not call. The daily report does not call this. Saving this skill does not call this.

Re-read the order and the return immediately before the POST. After it, read the order back with the integrations API. Success is `actions_required.at_risk` false and `processing_status` `undeliverable`. The app toast is not readback. If the JWT is missing, or the readback does not match, say the alert was not cleared. Do not clear the alert any other way.

### How to write each reply

Post the Block Kit card from the [poster](#post-with-the-block-kit-poster). The card follows the target hierarchy in [the Slack blocks reference](references/slack-blocks.md):

1. Bold order number and a status tag for each true `actions_required` flag, such as `At risk`.
2. Route line, such as `In transit → Hawaii`. Use the full state name. Add the country when it is not the US.
3. Service line, such as `USPS Priority Mail`. If no service is set, say `Not set (requested Standard)` with the requested service.
4. One context line.
5. A **View order in ShipMonk** link.
6. Action buttons only when a built-in action below applies.
7. Footer `Store {store id} · {Status}`, such as `Store 19002 · Fulfilled`.

Do not fold those into a paragraph. Do not print email or phone. Do not print the street on the card. The footer includes the store id. The ShipMonk link may also contain the store id. The incident ledger still keeps the store id.

Write status words like "Fulfilled" and "In transit", not raw keys. The context line is one short sentence. Do not add a boilerplate footer such as "no shipment change in this run."

Context lines:

- In transit, and the service was not changed: `Service unchanged — shipment already en route.`
- The daily clone check finds `{order_number}-R1` on the same store: `Order has been cloned.` Set `daily_cloned`. Do not create another replacement from that readout.
- A replacement was queued and the original could not be resolved: `Order has been cloned. Please Resolve At Risk`
- Return status exactly `returned`, before a draft exists: `Draft an email to the customer.`
- After that draft is saved and read back: `The draft email is in your inbox.` Omit the draft button. The draft is unsent.
- Address line 2 longer than 50 characters: `Address 2 exceeded limit of 50 characters.`
- A verified `{order}-R1` replacement exists and the original `at_risk` flag is still true: `Order has been cloned. Please Resolve At Risk`. This wins over the in-transit sentence. It is a suggestion for a person. It is not a completed resolve.

The plain-text `text` field is the notification fallback. It carries the same facts and does not invent a button.

**Built-in action.** If a built-in action applies, put that control in the reply and do not replace it with a different suggestion. The controls and their gates are in [the Slack listener reference](references/slack-listener.md).

- Return stage exactly `returned`: the **Draft an email to the customer** button (`action_id` `draft_address_check`). This wins over the USPS Priority button. The click saves an unsent draft from `hello@runeastpeak.com`. It does not send mail.
- Verified editable Hawaii or Alaska, and not returned: the USPS Priority button. Do not use FlavorCloud. Do not add that button, and do not describe the order as rerouted, when it is already en route, packed, returned, or otherwise not editable.

**View order in ShipMonk** is a link, not a block action. **Draft an email to the customer** and **USPS Priority** are `action_id` buttons. The poster can deliver those actions. Leave a button off when its gate fails. Do not post a button that does nothing.

**No built-in action.** When no action button applies, the context line is one suggested step. Phrase it as a suggestion, not as work already done. A suggestion in Slack is not authorization to perform it. Use the flag that blocks fulfillment:

- `address`: when address line 2 is longer than 50 characters, the context line is `Address 2 exceeded limit of 50 characters.` Put `Before:` and `After:` in the separate follow-up from [Address line limits](#address-line-limits). Otherwise, correct the address so ShipMonk can submit it. Do not edit the address from the report.
- `item_mapping`: map the unmapped items to products.
- `shipping_mapping`: choose a real carrier service for the requested method. An editable Hawaii or Alaska order uses the built-in USPS Priority action instead.
- `customs`: fill in the missing customs details.
- `hs_code`: add the missing HS codes.
- `routing` or `pending_b2b_routing`: add the missing routing instructions.
- `freight_quote`: choose a freight quote.
- `freight_info`: add the freight details needed for a quote.
- `ship_short`: decide whether to ship short or wait for the missing units.
- `global_e_label`: get the missing Global-e label.
- `automation_rule`: open the order and clear the automation-rule hold.
- `value_added_service_problem`: fix the value-added service, or change the order if it cannot be done.
- `at_risk`, and the order is still editable and is not Hawaii or Alaska: check whether it can still make the ship-by date. Treat a faster service as a suggestion until someone approves the change.
- `at_risk`, and the order is already packed, en route, or otherwise not editable: leave the service alone. The context line is `Service unchanged — shipment already en route.` The daily clone check still runs. When `{order_number}-R1` exists, the readout is `Order has been cloned.` If the return stage is `returned`, use `Draft an email to the customer.` and the draft button instead. The returned draft wins over the cloned-order sentence.

If several flags are true, show each as a status tag and use the blocking one for the context line or action button. If the order is not editable, do not suggest changing the address, the service, or the items. An unsubmitted order with the address flag can still get the address-line follow-up below.

## Address line limits

When `actions_required.address` is true and `ship_to.street2` is longer than 50 characters, keep the street off the order card. Post one follow-up in that day's thread, immediately after the order card. The follow-up is its own section. It names the order, states the current length and the 50-character limit, then shows the lines that would change as `Before:` and `After:`. Email and phone stay out. Do not write the address back to ShipMonk from the report. The follow-up ends with `Do not change the address until this is approved.`

When line 2 is `Guest:` plus the recipient name, a comma, and a stay sentence, `After:` keeps `Guest:` and the name and drops the stay sentence. Do not cut a word in the middle. Do not add a button that edits the address.

On 2026-10-30, order 8376 (store `19002`, unfulfilled, `unable_to_submit`, ship-to state FL) had `street2` of 61 characters: `Guest: Tyler Maher, staying from 5th November - 11th November`. The shortened line is `Guest: Tyler Maher`.

## Post with the Block Kit poster

Cursor's built-in Send to Slack tool posts plain text only. It cannot send Block Kit `blocks` or action buttons, and it posts as the Cursor app rather than East Peak Operations. Do not use it for this report or for a reply. Post the daily parent, each order card, and any address follow-up with `eastpeak-at-risk-shipments/slack_poster`. That poster calls Slack `chat.postMessage` with `blocks` and a plain-text `text` fallback. Post a listener reply with `slack_poster.post_thread_reply` and the same `chat.postMessage` call. The Slack app display name is East Peak Operations. The bot token is the runtime secret `SLACK_BOT_TOKEN`. The poster and the reply listener both use that same app and that same token. The listener reads it only to resolve its user id and to post a reply. Never print, log, or commit it. Do not create a second bot. If the incoming message does not @mention East Peak Operations, stop with no message.

From the repo root, run the local tests:

```
python3 -m unittest discover -s eastpeak-at-risk-shipments/tests -v
```

Preview the JSON that would be posted. This does not read the token and does not call Slack:

```
PYTHONPATH=eastpeak-at-risk-shipments python3 -m slack_poster --dry-run --report eastpeak-at-risk-shipments/tests/fixtures/in_transit.json
```

The in-transit fixture is the target layout. `address_and_returned.json` covers the 61-character address line and a returned Hawaii order.

The cards below are the shape. Full JSON is in the blocks reference. The first is in transit, so it has no action button. A returned order uses the draft button and the context line `Draft an email to the customer.` instead of the in-transit sentence.

```
Order #8257  At risk
In transit → Hawaii
USPS Priority Mail
Service unchanged — shipment already en route.
View order in ShipMonk
Store 19002 · Fulfilled
```

```
Order #8274  At risk
In transit → California
ShipMonk Standard
Service unchanged — shipment already en route.
View order in ShipMonk
Store 19002 · Fulfilled
```

## Verification, completion and restrictions

Read back **every** mutation, including service edits, clone/save/submit, draft creation/update, Slack posts/updates, and incident record writes. Record original state, requested action, observed result and next step. If a call times out, inspect persistent state before retrying; if the outcome remains uncertain, mark it uncertain and stop that action. Preserve completed independent work.

Do not automatically dismiss alerts. The separately approved cleanup of 26 alerts older than September 27 was a one-time action, not a standing policy. Age, a saved draft, a Slack post, a sent customer email, or submission alone is not grounds to clear risk. The one standing clear is a person-requested [resolve as undeliverable](#resolve-at-risk-as-undeliverable) for a single returned order, and only after the app call is read back. Any other requested dismissal still needs its own authorized scope and verified resolution.

Finish with the order/replacement links, precise status, routing result, unsent draft location, Slack reference, unresolved risks and approval/next step. Do not claim a blocked, queued, or uncertain action succeeded.

## Runtime prerequisites; no scheduler

This skill defines decisions and verification; it is not a scheduler and creates no schedule. Do not create a 9:00 a.m. Pacific job from this skill. A verified runtime for mutations, unsent Gmail drafts, and the Slack listener is still required before unattended runs. Runs must not depend on a laptop being awake.

Before future automation, verify cloud ShipMonk/Gmail/Slack access, the correct risk queue, supported mutation semantics and carrier-service mapping, a durable incident ledger with concurrency control, cost approval handling, and readback/recovery behavior in that runtime. Do not configure credentials merely to author or load this skill. Store the ShipMonk key only as the secret `SHIPMONK_API_KEY`, and the Slack bot token only as the secret `SLACK_BOT_TOKEN`, in an approved runtime secret facility. Never print either one and never put them in source, logs, notes, chat, or incident records. Follow the ShipMonk API section for the client, store, and documented upsert.
