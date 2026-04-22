{
    'name': 'Sales Order Double Approval',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Double approval for sale orders',
    'description': """
        This module adds double validation for sale orders.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'base',
        'sale',
        'sales_team',
    ],
    'data': [
        'security/security.xml',
        'views/res_config_settings_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}