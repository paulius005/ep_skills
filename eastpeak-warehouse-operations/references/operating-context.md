# Starting context — verify before use

Observed in October 2026. These are discovery aids, not current service state or authorization.

## Services and official evidence

- Pacificomm CartonCloud: https://app.cartoncloud.com/Pacificomm_Aus/Dashboards
- ShipMonk: https://app.shipmonk.com/
- CartonCloud inbound terms: https://help.cartoncloud.com/knowledge/purchase-orders-stock-in-as-a-customer
- Inbound API terminology (evidence, not permission to bypass UI): https://api-docs.cartoncloud.com/latest/api-reference/inbound-orders-purchase-orders
- ShipMonk manual orders: https://support.shipmonk.com/s/article/Creating-Manual-Orders
- NV1 official address: https://www.shipmonk.com/resources/fulfillment-locations/las-vegas-nevada

Observed customer/account names were RUN EAST PEAK in CartonCloud and EAST PEAK in ShipMonk. Verify account identity. The user chose Chrome computer use for this example; follow the current request's tool preference.

## Address starting points

Australia:
RUN EAST PEAK
Pacificomm / Virago Logistics
1/19 Centre Road
Scoresby, VIC 3179
Australia

This came from the supplied warehouse move notice. Verify current receiving address/contact against current instructions.

USA:
ShipMonk NV1 / EAST PEAK
6710 E. North Belt Rd.
Las Vegas, NV 89165
USA

NV1 differs from other Nevada sites. Verify selected warehouse and current official address. Public receiving hours are not necessarily outbound pickup appointment hours.

## Historical example, not a new-shipment default

Order 0026 split Black Poppy/Fish into 1,600 US and 400 Australia units. A different older-stock outbound shipment contained 2,711 units excluding those products. Do not conflate new factory receiving with the existing-stock outbound movement.

Supplier, customs values, 100-unit box packing, arrival dates and approvals were task-specific user facts. Require current task evidence before reuse. Do not persist UI indices, credentials, session URLs or transient compose/form state in this skill.
