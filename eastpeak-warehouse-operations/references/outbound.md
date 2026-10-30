# ShipMonk outbound warehouse shipment

Confirm exact SKU inclusions/exclusions and available stock at the origin. Zero availability is not authorization to include backorders or redistribute quantities. Resolve exceptions while preparing unaffected lines.

Use a unique order reference and verified destination/contact. Select regular shipping, pickup/custom labels, or merchant-booked freight according to who books transport and current UI capabilities. Do not select paid shipping or modify global store settings just to save a draft.

Verify order-type definitions. ShipMonk documentation describes **Transfer** as movement between its own facilities; an external 3PL is not automatically that type. Check current options and intended handling before committing. This is not authorization to alter unrelated submitted orders.

Reconcile all selected SKUs and quantities. Remove temporary stock-check lines. Text left in a product search field is not proof that a product is in the order.

## Price and customs value

Item price and customs value per unit are independent. The example inventory transfer used item price $0 and nonzero customs values. Use the current user's specified currency/values, not historical defaults.

Historical values were $8.90/bandana, $2.20/regular sock, $2.04/tab sock. Verify every product group and sum(quantity × customs value) independently. Order-level edits do not authorize changing catalog defaults.

## Save without accidental release

Inspect current controls and store scheduling. A manual form may show only **Submit**, followed by a record with **Submit for Fulfillment**. The wording alone does not prove safe draft persistence.

“Ship as soon as possible,” automatic submission timers, and scheduled submission dates can release an order without another click. **Queued to Submit is not an indefinite hold.**

Establish a safe draft/hold mechanism before any step that could auto-fulfill. Use current UI/help evidence, not a plan to race a timer or cancel afterward. Verify final hold status if using an authorized hold.

If safe persistence cannot be established, preserve the prepared form and report it as unsaved/unsubmitted. Identify the exact decision needed. Never click **Submit for Fulfillment** when the user requests a draft or says they will submit.

Keep fulfillment/pick-pack fees visible when relevant to approval. Do not assume special packing is free.

## Packing and pickup

When requested, include the proper warehouse receiving documents, carton/inner-bag SKU labels, carton contents lists and palletization instructions. Confirm actual attachments rather than assuming uploads succeeded.

Product-derived weights are estimates, not final packed gross weight. Obtain final carton/pallet dimensions, weights, ready date, pickup location, contact and appointment requirements from the warehouse.
