# Barcode evidence and validation

## What each check establishes

1. **Input checksum:** confirms the 12-digit string is structurally valid UPC-A. It does not validate product assignment, registration, or ownership.
2. **Editable document consistency:** confirms the .lsc semantic barcode data matches the requested UPC. It does not prove the cached image or PDF changed.
3. **Independent image decode:** render the exported PDF with Poppler and decode its pixels with ZXing-C++. Require the expected UPC, not merely any readable barcode. UPC-A may be reported as the equivalent EAN-13 with exactly one leading zero; normalize only that specific representation. Do not strip arbitrary leading zeros.
4. **Visual inspection:** review the rendered label for actual wording, cropped digits, blurry bars, text overlap, and clear quiet zones. Verify start/center/end guards if using a supplemental custom scanline decoder. A custom decoder is supplementary, not an independent third-party reader.
5. **Text-only regression check:** unchanged native barcode PNG bytes and unchanged PDF barcode-region pixels establish that a wording edit did not alter the known-good barcode. Use a crop derived from the current layout and include bars and digits; do not assume historic coordinates for another template.
6. **Physical scan:** only a real printed sample read by a scanner establishes performance for that printer, material, and print settings. Software success cannot guarantee it.

The included validator renders into a temporary directory, checks a single page per SKU, optionally checks native .lsc data, decodes each full label at 0°, 90°, 180°, and 270°, and writes a JSON report. It exits nonzero for input errors, missing files, native mismatch, or failed/wrong scan. It does not measure physical print grade, certify quiet-zone widths, or verify product registration. Inspect dimensions reported against the requested template; default 2 × 1 inches is a layout convention, not enforced by the script.

For a scan-only request, do not re-export or change labels. On any failure, preserve the evidence and identify the affected SKU. Fix an authorized label, then re-export and repeat relevant checks; do not hide a no-read by validating a separate generated barcode.

## Resolution lessons from the eight-sock batch

All eight labels decoded at 203, 300, and 600 DPI, including all four orientations at 300 DPI. Deliberately reducing to 150 DPI produced three no-reads. This is historical evidence, not an expected result for future batches. Test the actual current exports; report lower-resolution failures separately. Default to Actual Size / 100% and 300 DPI or better. Avoid Fit to Page, image downsampling, lossy recompression, or exporting thumbnails as deliverables.

## Minimal handoff

“Saved N PDFs and N editable .lsc files in [destination], exported at 300 DPI / 100% quality. All N exported barcode images decoded to their assigned UPCs in four orientations. [Any limitations or sync status.]”

Use that claim only when the current report supports it. For a wording-only change, add that barcode pixels are unchanged only if compared. Mention example-file edits separately. Avoid repeating claims about physical scanning or universal scanner compatibility that the evidence does not support.
