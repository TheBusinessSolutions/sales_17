# -*- coding: utf-8 -*-
{
    'name': "Partner Restrict Pricelist",

    'summary': """Restrict pricelist for customers""",

    'description': """This module will help you in restricting the pricelist for customers. Means only allowed 
    pricelists can be used for a  customer sale order. Restrict PriceList Access for User and Customer/Partner Odoo
    """,

    'author': 'Azkob',
    'category': 'Sales',
    'version': '1.0',
    "website": "https://www.azkob.com",
    # any module necessary for this one to work correctly
    'depends': ['sale_management'],

    # always loaded
    'data': [
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],

    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': True,
    'price': 0,
    'currency': 'EUR',
}
