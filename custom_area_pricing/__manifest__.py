# -*- coding: utf-8 -*-
{
    'name': 'Area-Based Pricing',
    'version': '17.0.2.0.0',
    'category': 'Sales',
    'summary': 'Calculate sales price based on product area (W × H) × Pricing Based Cost rate',
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
