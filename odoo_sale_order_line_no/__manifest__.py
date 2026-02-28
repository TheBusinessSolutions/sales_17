# -*- coding: utf-8 -*-
{
    'name': 'Serial no for product lines in Sale orders and Invoices',
    'version': '17.1',
    'author': 'Cloudroits',
    'summary': 'Add serial/line nos to product lines in Sale orders and invoices',
    'description': """This module displays serial/line nos to product lines in Sale orders and invoices both in the form as well in reports.""",
    'category': 'Sales',
    'website': 'https://www.cloudroits.com/',
    'license': 'AGPL-3',
    'depends': ['sale_management'],
    'data': [
        'views/sale_order_views.xml',
        'report/sale_order_report.xml',
    ],
    'qweb': [],
    'images': ['static/description/odoo_so_line_nos_banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
