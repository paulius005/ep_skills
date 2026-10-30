---
name: shopify-mercury-cashflow
description: Processes East Peak monthly cash flow using Shopify net sales reports and QuickBooks/Mercury CSV exports. Use when the user provides monthly Shopify sales CSVs, Mercury or QuickBooks transaction CSVs, asks to calculate money in and money out, or asks to dedupe Shopify/Mercury transfers.
---

# Shopify Mercury Cash Flow

## Purpose

Create a monthly cash movement report for East Peak using:

- Shopify `Net sales` as the primary Shopify revenue source.
- QuickBooks/Mercury transaction CSV rows for bank deposits, withdrawals, expenses, and transfer cleanup.
- Monthly statement PDFs only as tie-out support when available.

Do not count Shopify payouts, Shopify Balance movement, or Shopify-to-Mercury deposits as new revenue when Shopify `Net sales` is already included.

## Required Inputs

Ask for these files if they are missing:

- Shopify sales CSV covering the reporting period, preferably `Total sales over time`, with columns including `Month` and `Net sales`.
- One QuickBooks/Mercury transaction CSV per month, with columns like `Date (UTC)`, `Description`, `Amount`, `Source Account`, `Bank Description`, `Mercury Category`, and `Category`.

Optional but useful:

- Mercury monthly statement PDF for tie-out to beginning balance, total deposits, total withdrawals, and ending balance.
- Shopify Balance statement PDF for checking Shopify Balance activity.

## Core Rule

Use this simplified model:

```text
Money In = Shopify Net Sales + included Mercury deposits
Money Out = included Mercury withdrawals
Net Cash Flow = Money In - Money Out
```

Where:

- Included Mercury deposits are deposits that are not Shopify payouts, Shopify Balance transfers, Mercury internal transfers, or other owner/account transfers.
- Included Mercury withdrawals are real cash outflows from Mercury checking. Count Mercury Credit autopay as money out unless individual Mercury credit card transactions are also included.

## Classification Rules

Classify each QuickBooks/Mercury row into one of these buckets:

```text
external_income
expense
shopify_transfer_excluded
internal_transfer_excluded
credit_card_payment
refund_or_reversal
needs_review
```

Use `Amount` sign:

- Positive amount = deposit/inflow candidate.
- Negative amount = withdrawal/outflow candidate.

Default handling:

- Shopify `Net sales`: include as Shopify revenue.
- Mercury positive deposits from Shopify, Shopify Payments, Shopify Balance, or payout-like descriptions: `shopify_transfer_excluded`.
- Mercury-to-Mercury movement: `internal_transfer_excluded`.
- Mercury Credit autopay/payment: `credit_card_payment`; include in Money Out if no card-level detail is provided.
- Normal vendor withdrawals: `expense`.
- Stripe deposits are confirmed non-Shopify revenue for East Peak. Classify as `external_income` and include in Money In unless the user explicitly says a specific Stripe row is a transfer.
- Other non-Shopify deposits such as cashback, wire returns, reimbursements, invoices, or other revenue: classify based on description/category. Include as Money In unless clearly a transfer.
- Wire returns and vendor refunds should usually be `refund_or_reversal`. Include them in Money In because cash came back into Mercury, but note that they are not new sales.
- Tiny account verification deposits and reversals can be netted to zero and excluded if immaterial and clearly paired.
- PayPal withdrawals with transfer-like descriptions should be included as Money Out by default, but keep them in `needs_review` until confirmed as a real expense or transfer.

## Reporting Categories

After assigning the cashflow bucket, group included rows into user-facing reporting categories. Keep the cashflow math separate from the category labels.

Recommended category labels:

```text
Shopify Net Sales
Stripe / Non-Shopify Revenue
Other Income
Refund / Reversal
Factory / Inventory Production Costs
Product Development / R&D
Athlete Payments
Mercury Credit Autopay
Shipping & Postage
Marketing & Advertising
Payroll
Other Uncategorized Expenses
Excluded Transfers
Needs Review
```

East Peak-specific category rules:

- Factory, supplier, manufacturer, and inventory production payments are `Factory / Inventory Production Costs`. Do not rename these to R&D.
- Developer, product design, app, software, and product development vendors are `Product Development / R&D`. Known examples include `RubyLab Europe S.L.` and `Marco Design Studio`.
- Athlete, ambassador, sponsorship, royalty, and commission payments tied to athlete relationships are `Athlete Payments`. Known examples include `Aaron Kubala`, including notes like `5% of Dec - Feb Ice Bandana Sales`.
- `STRIPE` deposits are `Stripe / Non-Shopify Revenue`.
- `Mercury IO Cashback` is `Other Income`.
- Positive deposits from `ALPHA INTERNATIONAL CO., LTD.` and `NEVERSECOND NUTRITION, INC.` are income, even when categorized as `Transfer`; classify them as `Stripe / Non-Shopify Revenue` and include them in Money In.
- `TRAILDAZE INVEST` or other category `Revenue` deposits are `Stripe / Non-Shopify Revenue` or `Other Income` based on the description; include them in Money In.
- DHL, ShipBob, ShipMonk, and similar fulfillment or postage withdrawals are `Shipping & Postage` when they are real charges.
- Meta, Facebook, and Instagram charges are `Marketing & Advertising` by default because they are usually advertising spend. Use `needs_review` only when the description or available transaction detail indicates a non-advertising purpose.
- International wire foreign exchange fees are `Other Uncategorized Expenses` unless a more specific category is supplied.
- Mercury Credit autopay is `Mercury Credit Autopay` when included as Money Out.

For Money In, always show the split:

```text
Total Money In = Shopify Net Sales + Mercury Deposits
```

Where `Mercury Deposits` means included non-Shopify inflows from the Mercury/QuickBooks export.

## Shopify Data Handling

Use the Shopify sales CSV `Net sales` column for each month.

Do not use Shopify Balance statement `Shopify Payments payout` rows as revenue. Those represent funds moving within Shopify/processor balances and can overlap with sales reporting.

Know the Shopify definitions:

```text
Net sales = Gross sales - Discounts - Sales reversals
Total sales = Gross sales - Discounts - Sales reversals + Taxes + Duties + Shipping charges + Fees
```

For this workflow, prefer `Net sales` unless the user explicitly wants taxes/shipping included in money in.

## Mercury Credit Rule

If only Mercury checking or QuickBooks bank CSV activity is provided:

```text
Mercury Credit payment = included Money Out
```

If individual Mercury credit card transactions are also provided:

```text
Individual card charges = included Money Out
Mercury Credit payment = internal debt payment / excluded
```

Never count both the card charges and the card payment as expenses.

## Monthly Output

Produce one summary row per month:

```text
Month
Shopify Net Sales
Included Mercury Deposits
Total Money In
Included Mercury Withdrawals
Total Money Out
Net Cash Flow
Excluded Shopify/Mercury Transfers
Excluded Internal Transfers
Needs Review
Notes
```

When presenting a month, also include a small Money In breakdown:

```text
Source
Amount

Shopify Net Sales
Mercury Deposits
Total Money In
```

For Money Out, include category totals using the reporting categories above, plus detail sections for high-signal categories such as:

```text
Factory / Inventory Production Costs
Product Development / R&D
Payroll when payroll is high, such as over $5,000 or over 10% of Money Out
Other Uncategorized Expenses
Needs Review
```

Also produce or describe a transaction detail table when useful:

```text
date
description
amount
source_account
category
cashflow_bucket
included_in_money_in
included_in_money_out
reason
```

## Validation

When a Mercury monthly statement PDF is provided, tie the QuickBooks/Mercury CSV totals to the statement:

```text
Beginning balance + total deposits - total withdrawals = ending balance
```

Allow minor differences only when the statement and CSV cover different accounts, time zones, pending transactions, or card-level activity.

Flag:

- Shopify-looking deposits that were included as revenue.
- Missing categories on large withdrawals.
- Positive deposits that are not Shopify transfers and need explanation.
- Duplicate months or mismatched date ranges.
- Any month where QuickBooks/Mercury totals do not tie to the statement.

## Response Style

Keep the first response practical:

- Say whether the provided files are enough.
- List missing files only if needed.
- Show the computed monthly summary if possible.
- Call out classification assumptions, especially Mercury Credit handling.
- Default to copyable Notion-friendly Markdown for the report output.
- Put the full report in one fenced `markdown` code block so the user can copy it directly into Notion.
- Do not create or rely on a canvas for this workflow unless the user explicitly asks for one.

For uncertainty, use `needs_review` rather than guessing.

When producing the report, use Notion-friendly Markdown instead of relying on canvas styling. Use:

- A short title and bold headline metrics.
- A top `Money In Formula` table before the monthly summary that explicitly shows:

```text
Shopify Net Sales
Included Mercury Deposits
Total Money In
```

- Markdown tables in this order: Money In Formula, Monthly Summary, Money Out by Category, Included Mercury Deposits, then detail sections such as Factory / Inventory Production Costs, Product Development / R&D, Payroll when high, Athlete Payments, Other Uncategorized Expenses, Excluded Shopify/Mercury Transfers, and Needs Review.
- Category names that are readable in Notion, not internal bucket names.
- No canvas-only formatting assumptions, because Notion strips most canvas styling when pasted.
