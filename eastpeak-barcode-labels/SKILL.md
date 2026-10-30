---
name: eastpeak-barcode-labels
description: Create, edit, export, and validate East Peak apparel UPC-A labels in Label LIVE, delivering matching editable .lsc files and SKU-named PDFs. Use for retail product barcode labels and visual barcode scan checks, not shipping labels or assigning new UPC numbers.
---

# East Peak barcode labels

Deliver matching editable Label LIVE documents and print-ready PDFs for the requested SKUs, with evidence that the actual exported barcode bars decode correctly.

## Establish the job

- Use the current user's exact SKU → UPC mapping, product attributes, destination, and template. Treat UPCs as strings, preserving leading zeros. Validate 12 digits and the UPC-A checksum before authoring. Flag invalid, duplicate, or conflicting assignments; do not silently correct or invent numbers. A valid checksum does not prove GS1 ownership or registration.
- Default to the existing East Peak layout and Label LIVE when continuing this workflow. Confirm missing product facts or a missing template only when they affect the result. Do not reuse old products, destination paths, or country-of-origin claims as facts for a new job.
- For a folder-wide edit, inventory actual PDFs and .lsc files, including examples. For a SKU-specific edit, restrict changes to those SKUs. Archives are separate deliverables: update only if requested, and mention an existing archive that still contains old labels when relevant.

## Label conventions

The established design is a 2 × 1-inch label: size and color at upper left; SKU, style, and apparel category right-aligned at upper right; centered UPC-A barcode with large readable digits; country of origin at lower left. Preserve the actual supplied template's dimensions and typography if they differ.

Use **Unisex**, **Women's**, or **Men's** on its own, without `Gender:`. Retain `Size:`, `Color:`, and `Style:` where the template uses them. Include origin wording such as `Made in China` only when supported by current product data or the applicable template. Do not extend a label wording fix into unrelated product changes.

## Build and export

Read [Label LIVE workflow](references/label-live.md) before editing .lsc files or driving the app. Use the available PDF skill for PDF rendering and visual QA.

- Preserve source files while preparing working copies. Produce one `<SKU>.lsc` and one `<SKU>.pdf` per SKU, directly in the requested destination unless the user asks for subfolders.
- Export from Label LIVE at **300 DPI / 100% quality**, one 2 × 1-inch page per label for the established template. Verify actual settings; never assume inherited export quality.
- Retain barcode digit size, bar dimensions, and quiet zones. Changing the data string alone does not guarantee the cached image updated. Reopen and verify the native document and the PDF.
- Use supported computer-use tools for UI work; re-read accessibility state after actions. Do not embed brittle UI indexes, guessed app internals, or historical temporary paths in automation.
- If filesystem access to Dropbox is denied, use an available authorized app file picker or Finder workflow. Do not change system permissions silently. Report a concrete access blocker if no authorized route works.

## Validate the actual deliverables

Read [Validation and handoff](references/validation.md). Run the included scanner on **the latest exported PDFs**, not a separately generated barcode or printed digits:

```sh
python scripts/validate_labels.py --expected /absolute/path/expected.json \
  --pdf-dir /absolute/path/labels --lsc-dir /absolute/path/labels \
  --report /absolute/path/qa/barcode-validation.json
```

`expected.json` is a nonempty JSON object mapping exact SKU strings to 12-digit UPC strings. The script requires `Pillow`, `zxing-cpp`, `pypdf`, and Poppler's `pdftoppm`. Resolve the current runtime instead of hardcoding an old bundled version. Install missing dependencies in an isolated environment if needed and permitted.

Require every label to decode to the expected UPC at 300 DPI in all four cardinal orientations, with a valid checksum. Inspect rendered full labels for correct text, unclipped digits, alignment, sharp bars, and adequate whitespace around the barcode. A decoder success alone is not a formal barcode-quality or quiet-zone certification. For text-only edits, compare the old/new barcode region pixels and native barcode image to confirm they stayed unchanged.

Save QA reports outside the deliverable folder unless requested. Verify all intended files reached the destination; distinguish saved local files from completed cloud sync. Report exact file counts, changes, scan results, and any unresolved limitation. Say “software-decoded successfully,” not “physically tested.” Recommend printing at Actual Size / 100%, 300 DPI or better, with a physical sample scan before a production run. Do not claim the skill is installed merely because it was saved in a skills repository.
