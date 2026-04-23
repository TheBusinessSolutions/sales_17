================================================================
Sale Discount On Total Amount
================================================================

The **Sale Discount On Total Amount** module enhances Odoo’s discount management on Quotations, Sale Orders, and Invoices by introducing flexible discount types, approval workflows, configurable limits, bulk operations, and detailed reporting.

**Table of contents**

.. contents::
   :local:

**Key Features**
================================================================

**Sale Order / Quotation / Invoice Enhancements**  
- Supports **Percentage** or **Amount** discount types  
- Discount Rate input and computed **Discount Amount**  
- **Total After Discount** calculation  
- Auto state switch to `Waiting Discount Approval` if above limit  
- Discount displayed in reports (PDF)  
- Approve / Reject buttons for Discount Managers  
- Organized, clean user interface  

**Discount Approval Workflow**  
- New approval state: `waiting_discount_approval`  
- Enforces limits configured in settings  
- Prevents confirmation/posting if discount exceeds threshold  
- Only **Discount Approval Managers** can approve/reject  
- Transitions state on approval or rejection  
- Discount reset if rejected  

**Configuration Settings**  
- Assign **Discount Approval Manager** role  
- Set discount limit (%) for requiring approval  

**Bulk Operations**  
- **Bulk Discount Update Wizard**: Apply discount type/value to multiple records  
- **Bulk Discount Approval Wizard**: Batch approval or rejection  
- Wizard access restricted to Discount Managers  

**Reporting**  
- Discount Summary Report (user-wise):
  - Total Discount Amount  
  - Number of discounted Quotations / Orders / Invoices  
- Navigate to: **Invoicing > Reporting > Discount Reports > Discount Summary**

**Filters & Usability**  
- Easily filter records in list view that are:
  - **Waiting for Discount Approval**  
- Fields visibility managed by user group  
- Fully translatable UI  

**PDF Report Enhancements**  
- Displayed on:
  - Quotation / Sale Order reports  
  - Invoice reports  
- Shows:
  - Discount Type  
  - Discount Rate  
  - Discount Amount  
  - Final Total After Discount (bold + underlined)

**Multi-language Support**  
- Includes translations for:
  - 🇩🇪 German  
  - 🇫🇷 French  
  - 🇪🇸 Spanish  
  - 🇯🇵 Japanese  

**Summary**
================================================================

Sale Discount on Total Amount Odoo App manages total order discounts in Odoo with configurable limits and approval workflows. Offers bulk updates and integrates with quotations, sales orders, and invoices. Includes discount analytics.

**Installation**
================================================================

1. Copy the module to your custom addons directory.
2. Update the Apps List in Odoo.
3. Search for **Sale Discount On Total Amount** and install it.
4. Go to **Settings > Sales**, enable the **Discount Approval Manager** group.
5. Set the **Discount Limit (%)** for requiring approval.

**How to use this module:**
================================================================

1. Create or edit a Quotation / Sale Order / Invoice.
2. Set the Discount Type and Rate.
3. If the discount exceeds the configured limit:
   - The document is moved to `waiting_discount_approval`.
   - Approval buttons will be shown only to Discount Managers.
4. Discount Managers can **approve** or **reject** the discount.
5. Approved records will continue to confirmation/posting.
6. Use **Bulk Wizards** to apply or approve discounts in batch.
7. View discount insights in the **Discount Summary Report**.

**Change logs**
================================================================

[1.0.0]

* ``Added`` [21-05-2025] - Sale Discount On Total Amount module

**Support**
================================================================

`Zehntech Technologies <https://www.zehntech.com/erp-crm/odoo-services/>`_