# Slack listener actions

These are the built-in buttons a reply may include. Post a button only when its gate matches the live record. A button saves work only after a person clicks it. Do not click it on their behalf, and do not send customer email.

The Slack text of a reply still omits the store id, full address, email, and phone. The button payload may carry order number, order key, store id, and RMA so the listener can re-read the order. It must not carry the address, email, or phone.

Button `action_id` values and the card around them are in [the Slack blocks reference](slack-blocks.md). A URL button for the order link can always be posted. An `action_id` button is posted only when a click will reach an agent that runs this file. Otherwise omit the button and keep the same words on the context line.

## USPS Priority

`action_id`: `usps_priority`

Gate: verified US destination state HI or AK (or the unambiguous full name), and the shipment is still editable. Do not use it when the order is packed, en route, returned, or otherwise not editable. Do not use FlavorCloud. Do not describe an already-moving shipment as rerouted.

This file does not define a carrier service id. Do not invent one. Selecting the button is not permission to release a held shipment.

## Draft address-check email

`action_id`: `draft_address_check`

Label: **Draft address-check email**

Gate: the return stage is exactly `returned`. Read it from `GET /v1/integrations/returns-list?rma={rma}` for each RMA on the order. `processing_status` is not the stage. An order can stay `en_route` after the return is `returned`. Do not treat `arrived`, `grading_completed`, `en_route`, or any other return status as this gate. Do not match the substring "return" in a city, note, or tracking line.

On click, and only on click:

1. Re-read the return. If the status is no longer exactly `returned`, stop and say so. Do not draft from a stale button.
2. Re-read the order. The recipient is `customer_email` when the ship-to email is empty. If both are present and differ, or neither is present, stop and ask which address to use. Never guess.
3. The From account must be `hello@runeastpeak.com`. If that mailbox is not the one available, stop. Do not draft from another account.
4. Search for an existing unsent draft for this order whose subject is the subject below. Update that draft in place. If a matching message was already sent, stop and report it. Do not send another.
5. Save **DRAFT ONLY — NEVER SEND**. Read back the draft id, From, To, subject, body, and unsent state.
6. Reply in the same Slack thread that the draft exists, labeled **DRAFT ONLY / unsent**, with the draft link when one exists. Do not include the address, email, or phone in that reply.

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
