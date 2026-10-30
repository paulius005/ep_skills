# Country allocation and factory packing

Read the supplied workbook/tab and headers. Distinguish total stock, country allocations, existing warehouse stock, and new factory stock. Filter the requested SKU subset before calculating. Do not replace exact allocations with a percentage split.

Verify US + Australia = total per SKU when those are the complete destinations. Investigate discrepancies without redistributing stock unasked. An exception colorway can have an inbound receiving while remaining excluded from an outbound shipment.

## Factory spreadsheet

Use the available spreadsheet skill. A practical layout is:

- Quantity split: exact SKU, product/colorway, size, US units, Australia units, total units; formula totals and packing assumptions nearby.
- Shipping instructions, when substantial: both addresses, receiving references, exact label filenames, label fields, arrival targets, and pre-dispatch requirements.

One sheet suffices for a small allocation without substantial instructions. Avoid redundant country tabs. Preserve order IDs such as 0026 as text. Cite source filename/tab and user-provided packing assumptions in one ordinary notes area.

## Cartons and labels

100 units per box does not imply one SKU per box. For allowed mixed-SKU cartons, planned count is country units / capacity when exactly divisible. For single-SKU cartons, calculate cartons per SKU using its quantity and capacity, then sum. Ask only when the distinction changes the commitment.

Never alter SKU quantities to fill boxes. Mixed cartons need separate labelled inner bags and a carton packing list with each SKU and actual quantity. Keep the countries' shipments separate.

Receiving labels, SKU labels, and carrier/destination labels serve different purposes. Inspect supplied PDFs; render image-only documents when text extraction is empty. A blank SKU label is not a complete destination shipping label.

For ShipMonk forms, preserve ASN/barcode, and fill actual carton number, SKU(s), and quantities. Number cartons against the actual shipment count. For Pacificomm blank SKU labels, fill exact codes and include receiving reference and quantities on outer documentation as requested.

Before dispatch, request separate country packing lists, carton counts, gross weights, dimensions and label photos when part of the authorized handoff.

## Verification

Compare every exported SKU/quantity with source, detect duplicates/missing sizes, and independently verify country totals and carton arithmetic. Recalculate formulas and render deliverable sheets. Keep addresses, dates, filenames and labels readable. Mark unconfirmed arrival dates as targets.
