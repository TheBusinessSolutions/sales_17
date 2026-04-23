{
    "name": "Total Discount",
    "version": "17.0.1.0.0",
    "description": """
    
    Easily manage global discounts on invoices and sales orders in Odoo.

    Features:
    - Apply global discounts (percentage or fixed) without needing a discount product.
    - Configure discount behavior: apply before or after tax.
    - Automatically calculate and display total discount values.
    - Show total discount fields in both form and tree views.
    """,
    "category": "Accounting & Finance",
    "author": "Mohamed Hussein",
    "support": "muhmmdamer@gmail.com",
    "website": "https://www.linkedin.com/in/muhmmdhussein/",
    "license": "AGPL-3",
    "depends": ["account", "sale_management"],
    "data": [
        "views/account_move.xml",
        "views/account_move_tree.xml",
        "views/sale_order.xml",
        "views/sale_order_tree.xml",
        "views/res_config_settings.xml",
    ],
    "installable": True,
     'images': ['static/description/banner.png'],
    "icon": "/custom_total_discount/static/description/icon.png"
}
