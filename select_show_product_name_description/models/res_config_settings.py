from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    print_product_name = fields.Boolean(
        related='company_id.print_product_name', 
        readonly=False,
        string="Print Product Name"
    )
    print_product_description = fields.Boolean(
        related='company_id.print_product_description', 
        readonly=False,
        string="Print Product Description"
    )