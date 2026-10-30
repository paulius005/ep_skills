# Label LIVE mechanics learned from the East Peak workflow

## App and document access

The app was displayed as **Label LIVE**, bundle ID `com.semireg.LabelLIVE`, although the user called it “Core Label LIVE.” Discover the current app rather than assuming that nickname resolves. Recent Designs may expand a preview first; opening the design is a separate action. File → Duplicate followed by Save creates a safe working reference. Do not modify the only source template to start a new batch.

macOS file-picker actions can finish before the new document loads. Confirm the window title and product text before editing or exporting. After opening Go to Folder, fetch the dialog state before entering a path; typing too early once dropped the beginning of a path. Use fresh element indexes. If the Mac locks, preserve progress and ask for an unlock; never report pending exports as complete.

## Native .lsc format

The documents observed in Label LIVE 4.14 were JSON. Inspect the current document before applying these observations:

- `canvasRecord.objects` holds editable semantic elements. An `ELEMENT_BARCODE` has `config.text`, `bcid: upca`, scale, show-value, and height settings. Text elements have `config.text` and sometimes `lastText`.
- `canvasRecord.fabricRep.objects` holds rendering data: textboxes and an image with `imageKind: ELEMENT_BARCODE`, PNG `src`, dimensions, scale, position, and UUID linking it to the semantic element.
- `labelConfig` includes dimensions, DPI and `printerConfig.MOCK_IMAGE_QUALITY` in these documents. Settings in JSON do not replace observing the app's export settings.
- `path` can retain an old output path. Avoid saving into the wrong document; verify the app's active path and final destination. Preserve fonts, object IDs, positions, and unrelated settings.

Updating `config.text` without regenerating the image can leave an old barcode visible or exported. For new UPCs, use the app's barcode Data editor to regenerate the visual, save, and inspect. For programmatic batch preparation, update each applicable text representation and use the app to regenerate/export; do not treat an unchanged cached PNG as a new barcode. Avoid raw global string replacement that could corrupt encoded data.

For a wording-only change, update semantic and rendered text together while retaining the barcode object and cached image. Reopen in Label LIVE to confirm rendering. Do not shrink the digits to solve another layout issue.

The historical template's barcode image was typically 327 × 141 pixels at scale 1. One valid variant was 326 pixels wide because of digit glyph extents. These are observations, not universal constraints. Compare actual bar/module and digit sizing rather than failing a label solely for a one-pixel outer-image width difference.

## Export and save

The established route was Print → Print Preview, Single Label, 300 DPI, Full Color, Quality 100%. Print generated a PDF and opened it in Preview. Save the generated PDF under the exact SKU. Observe the actual generated file path or save dialog; do not guess a timestamped temporary filename. Match every export to the intended document, and do not accidentally choose an older PDF when multiple preview files share a SKU.

When direct Dropbox access failed, the app could open the template and Finder could copy validated files into the destination. Prepare only the intended deliverables in a staging folder, then copy them using supported UI controls. Existing matching files may be replaced when that edit is authorized; inspect any conflicts before applying a batch replacement. Verify all expected filenames after copying, and note if Dropbox is still uploading. Keep existing ZIP files distinct from the live label files.
