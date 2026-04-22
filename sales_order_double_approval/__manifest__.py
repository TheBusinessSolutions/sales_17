# __manifest__.py
{
    'name': 'Sales Order Double Approval',
    # ... other fields ...
    'data': [
        'security/security.xml',  # Add this line
        'res_config_settings_views.xml',
        'sale_order_views.xml',
        # Remove res_company_views.xml from here if it was present
    ],
}