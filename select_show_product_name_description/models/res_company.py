from odoo import fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    print_product_name = fields.Boolean(string="Print Product Name")
    print_product_description = fields.Boolean(string="Print Product Description", default=True)