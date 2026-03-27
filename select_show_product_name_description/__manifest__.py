{
    'name': 'Select Show Product Name or Description',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Toggle Product Name and Description in Quotation PDF Reports',
    'description': """
Select Show Product Name or Description
=======================================
This module adds configuration options to the Sales Settings to control the 
display of product information in the Description column of the Sale Order Report.

Key Features:
-------------
* **Print Product Name**: Display the template name of the product.
* **Print Product Description**: Display the standard Odoo line description.
* **Combined Mode**: If both are selected, they appear as 'Product Name | Description'.
* **Company Specific**: Settings are saved per company for multi-company environments.
    """,
    'author': 'Business Solutions',
    'depends': ['sale', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/report_saleorder_templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}