# Incident record and rerun contract

Use a durable, access-controlled operational ledger available to the authorized runtime. This document is its contract, not a live ledger. Do not create customer records in the skill source tree. If a reliable ledger or exclusive claim is unavailable, continue read-only triage and report that consequential actions are blocked.

## Identity and minimum record

Key an incident by verified account/store + original order ID + original shipment ID + stable source incident ID. If the source has no incident ID, persist a generated incident token once against that original shipment and observed risk episode. Reuse it while unresolved. Do not derive a new key on every run from a timestamp or changing status text. A later incident requires evidence that the prior episode closed and a distinct new risk began; ambiguity requires review.

Keep these fields in the operational record:

| Field | Contents |
| --- | --- |
| Identity | Stable incident key, account/store, order ID/link, original shipment ID/link, source queue and incident/episode evidence |
| Original state | Observation time, exact live status/reason, destination state/country, original service, editability/handoff and tracking evidence references; item/quantity comparison references |
| Prior work | Replacement lineage/IDs/links and statuses; charges/commitments; existing customer draft account/ID/thread; Slack reporting date/timezone, verified workspace/channel/daily parent, the one order-message reply per shipment, and listener action-reply identifiers/permalinks |
| Authorization | Current scope, direct owner approval reference, approved amount/currency/limit where applicable; never credentials |
| Action | Stable action key (incident + operation + target), intended mutation, safe before/after comparison, claim owner/version and attempt state |
| Result | Readback time/reference and observed persisted state, replacement or draft/message ID, amount/currency, discrepancy or exact blocker |
| Next step | Outstanding risk, owner decision needed, pending/denied/uncertain outcome, and evidence required to resume |

Keep personal data out of general logs and Slack. Refer to protected order records for recipient/items instead of copying addresses, email addresses or payment data into the ledger unnecessarily. Never store secrets.

## Claim, apply, verify, resume

1. Atomically claim the incident/action in the ledger before mutation; use a supported lock or compare-and-set/version mechanism. A second worker must defer while a claim is active. An expired claim does not prove that its external action failed.
2. Inspect the ledger **and** current service records, including replacements, drafts, Slack history and original tracking. Check for work done outside the ledger. Reconcile disagreements before proceeding; absence of a ledger entry is not evidence that no action occurred.
3. Persist the planned action and original state before executing. Confirm the ledger write by readback. States should distinguish planned, in progress, verified, blocked, denied, failed, and uncertain; maintain history rather than overwriting failed/uncertain evidence.
4. Perform the one authorized mutation. Read back its actual target and result, persist the verified result and IDs/references, then read back the ledger update. Only mark verified after external readback; a successful request return alone is insufficient.
5. After timeout, crash or uncertain return, inspect external state using stable IDs, lineage and search. Resume the same action only if evidence establishes it did not execute and retry is authorized. Never blindly repeat clone/submit or create another draft/post. If ambiguous, keep the claim/action uncertain and surface the precise blocker.
6. On rerun, skip already verified work **after checking current live state**. Reuse the matching replacement and unsent draft; report in the day's shared Slack parent, reusing that parent and the shipment's order message. Deduplicate existing action replies. Update them only when evidence requires it. A sent/deleted draft, changed risk or conflicting owner edits needs reconciliation, not automatic recreation. A Slack reply is not a merge: do not merge orders, shipments, or incidents because a reply arrived.

## Daily thread and action reporting records

Maintain a shared daily key of verified workspace ID + channel ID + reporting date + explicitly configured reporting timezone. Default to `America/Los_Angeles` (Pacific) for this user unless changed by the user. Compute the actual Pacific calendar date at run time. The parent text must be exactly `At Risk Shipments [Date] 🧵`, replacing `[Date]` with that date in `YYYY-MM-DD` format. One parent per Pacific day in `#at-risk-shipments`; reuse it on reruns. Each at-risk shipment is its own reply under that parent. The parent contains no shipment detail. Persist the parent message timestamp/`thread_ts`, permalink, claim/version and creation/readback state, plus each shipment's order-message timestamp. Search for an existing daily parent before creation, claim atomically across workers and reconcile uncertain creation before retrying. Do not use one parent per incident.

Link each incident/action/attempt to its daily key, order-message id, verified reply ID/permalink and last reported outcome. Listener replies are action input only after [the Slack listener contract](slack-listener.md) maps them; record the action label or button `action_id`, the order message it named, and the tree result. Preserve before/after or verified result, blocked/denied/failed/uncertain status, unsent draft reference or absence reason, decisions needed, and pending reporting errors. Failed or uncertain operational attempts still require a reply on that order message. Deduplicate unchanged reruns; update a reconciled result while retaining prior uncertainty/failure history. A distinct authorized retry has a distinct attempt reference. Verify every report mutation and ledger update by readback. If Slack is inaccessible, preserve the pending entry and report the blocker in the completion handoff rather than claiming delivery. Do not auto-merge orders, shipments, incidents, or Slack messages to work around a missing reply or a missing parent.

The ledger prevents repeated actions; it never proves that delivery risk is resolved. Record a saved draft as awaiting owner review and keep the shipment alert open. Do not mark an incident resolved solely because a replacement was submitted, an email drafted or a Slack message posted.
