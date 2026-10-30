# Product setup

## CartonCloud mapping and access

Check the account for existing exact Product Codes and available export/import controls. Customer access may expose Add Product without bulk controls. Do not assume an administrator feature is available. If manual entry is needed, explain the limitation and proceed when authorized. A mapping workbook does not prove an import occurred.

SKU maps to **Product Code**. Preserve SKU and barcode leading zeros as text. Internal product ID is assigned by the service and should be recorded after creation. Product names may differ from the factory description.

For a requested spreadsheet copy, preserve source tabs and add a clearly named mapping/results tab. Use an actual exported template when available; do not call a guessed schema official.

Observed mapping fields: Customer, Id, Active, Name, Code, Type, Storage Charge Method, Volume (cubic meters), Weight (kilograms), Country of Origin, Harmonised System Code, Measurement Category, Base Measurement, Stock Selection Method, Stock Sub-Selection Method, Barcode. Recheck the current template/UI before generating an import.

Convert lb to kg using 0.45359237. Distinguish unknown volume from zero: a very small volume may be below the UI's decimal precision. Leave it blank when allowed and explain the limitation rather than silently entering zero.

Reuse existing measurement/storage/FIFO conventions only when applicable to the new product. Verify each saved code, name, barcode, and assigned ID. Search by code before retrying an uncertain save.

## Customs fields

HS code, MID, barcode, SKU, and internal product ID are different identifiers. MID is manufacturer identification; supplier name alone may be insufficient to derive it. Leave optional MID blank without supported manufacturer details.

Identify HS codes as recorded in the source/product records. These fields are not verified legal tariff classifications. Historical examples were 6115.96 for socks (including tab socks) and 6307.90 for ice bandanas; do not generalize them to all future products.

When classification advice is requested, check current official customs sources and actual composition. Distinguish international six-digit headings from country-specific extensions. Ask the broker to confirm destination tariff digits where needed.
