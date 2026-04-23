==========================================
Total Discount for Invoices & Sales Orders
==========================================

Easily manage global discounts on invoices and sales orders in Odoo 17.

**Features**
------------
- Apply global discounts (percentage or fixed) on invoices and sales orders.
- Configure discount behavior: apply before or after tax.
- Automatically calculate and display total discount values.
- Show total discount fields in both form and tree views.
- No need for a discount product.

**Configuration**
-----------------
1. Go to Settings > General Settings > Discount Settings.
2. Choose whether to apply the discount before or after tax.

**Usage**
---------
- On Sales Orders and Invoices, use the "Add Discount" field to apply a global discount.
- The total discount and after-discount amounts are automatically calculated and displayed.

**API Usage**
-------------
This module fully supports creating and updating invoices with global discounts via Odoo’s JSON-RPC API.

On model `account.move`:

- `add_discount`: *(float)* The value of the global discount.
- `add_discount_type`: *(string)* `"fixed"` or `"percent"`.

**Example: Create an invoice with a global fixed discount**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "account.move",
    "method": "create",
    "args": [{
      "move_type": "out_invoice",
      "partner_id": 1,
      "add_discount": 150,
      "add_discount_type": "fixed",
      "invoice_line_ids": [[0, 0, {
        "product_id": 31,
        "quantity": 1,
        "price_unit": 1000,
        "tax_ids": [[6, 0, [1]]]
      }]]
    }],
    "kwargs": {}
  },
  "id": 1
}


**Author & Support**
--------------------

- Author: Mohamed Hussein
- LinkedIn: https://www.linkedin.com/in/muhmmdhussein/
- Email: muhmmdamer@gmail.com

**License**
-----------
AGPL-3
**Changelog**
-------------
- 17.0.1.0.0: Initial release.
