# -*- coding: utf-8 -*-
{
    'name': 'Area-Based Pricing',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Calculate sales price based on product area (W × H) × Pricing Based Cost rate',
    'description': """
        Area-Based Pricing Module for Odoo 17 CE
        =========================================
        - Maintains a dated Pricing Based Cost rate table per product category
        - Computes sale order line price as: Width × Height × Rate
        - Pricelist rules (discount % or fixed price) applied on top
        - Full cost rate history preserved — never overwritten
        - Recalculate button refreshes to today's latest rate on draft quotations
    """,
    'author': 'Custom Development',
    'depends': ['sale_management', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_area_cost_views.xml',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
