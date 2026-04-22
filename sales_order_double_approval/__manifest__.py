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
    'live_test_url': 'https://youtu.be/dQw4w9WgXcQ',
    'depends': [
        'base',
        'sale',  # <--- THIS IS CRITICAL. Add this line.
        'sales_team',
    ],
    'data': [
        'security/security.xml',
        'res_config_settings_views.xml',
        'sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}