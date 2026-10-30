# Inbound receiving

Create expected inbound stock, not physically received inventory. Search existing references before creating another order.

## CartonCloud / Pacificomm

CartonCloud's customer inbound workflow is called **Purchase Orders / Stock In**. Verify the current page/status. If terminology is challenged, show official documentation from operating-context.md.

Confirm customer, reference, arrival and exact SKU subset. Separate main stock from requested exception colorways. Add expected quantities by Product Code in the proper base unit. Dynamic editors can create duplicate rows: reconcile the full saved code/quantity set, not just the total.

Submit/approve within current authorization. **Not yet received** is distinct from physical receipt or allocation. Do not use receive/complete merely to finish an inbound notification.

If requested, export vendor verification/receiving printouts and compare the PDF quantities to source. Templates may say “Purchase Order Confirmation” or “Completed”; report physical receipt using application status, not boilerplate.

## ShipMonk

Open Receiving → Create Receiving. Confirm warehouse, category, ASN/reference, supplier, expected delivery, handling type and count. Select category for the actual purpose: a manufacturing/purchase ASN differs from a warehouse inventory transfer.

In the observed version, supplier, delivery date, handling type and valid count were required even to continue/save. Ask for actual facts instead of placeholders. If the current UI permits blanks in drafts, use it rather than imposing historical requirements.

Continue can create a persistent **Draft Detail** and advance to Product Details. Capture its link. Add/import exact SKU quantities and verify each selected result before saving. Search/save responses can load asynchronously. Inspect whether a line exists before retrying a slow save.

Reconcile the final eight or other requested lines by exact SKU and quantity. Use **Save as Draft** for a draft endpoint and verify the list shows warehouse, supplier, date, handling count, SKU count and units.

**Submit Receiving** is separate from saving a draft. Honor submission checkpoints. After authorized submission, verify final status and retrieve labels/printouts if requested. Do not mark stock physically received.

Handoff: record link/reference, Draft/Awaiting status, SKU/unit total, handling count, ETA, and any material remaining prerequisite.
