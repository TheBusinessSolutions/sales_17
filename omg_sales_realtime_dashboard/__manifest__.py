# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo Man
#
##############################################################################
{
    'name': 'Sales Real-Time Dashboard',
    'summary': 'Executive-grade live sales dashboard with advanced analytics, list mode, targets, and drill-downs.',
    'description': """
        Odoo Man Sales Real-Time Dashboard for Odoo 17

        Features:
            * executive KPIs with period comparison
            * advanced filters with presets and favorites
            * dashboard mode and grouped list mode
            * drill-down charts and Odoo list opening actions
            * target planning and achievement tracking
            * profitability insight and alert widgets
            * pivot-style summary and static enterprise-style UI
    """,
    'version': '17.0.2.0.8',
    'category': 'Sales',
    'license': 'AGPL-3',
    'author': 'Odoo Man',
    'company': 'Odoo Man',
    'maintainer': 'Odoo Man',
    'website': 'https://odooman.odoo.com/',
    'depends': ['sale_management', 'web', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/dashboard_views.xml',
        'views/dashboard_target_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'omg_sales_realtime_dashboard/static/src/scss/dashboard.scss',
            'omg_sales_realtime_dashboard/static/src/js/dashboard_action.js',
            'omg_sales_realtime_dashboard/static/src/xml/dashboard_templates.xml',
        ],
    },
    'images': [
        'static/description/banner.gif',
    ],
    'currency': 'USD',
    'price': 0.0,
    'application': True,
    'installable': True,
}
