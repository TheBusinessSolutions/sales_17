from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_discount_approval = fields.Boolean(
        string="Sale Discount Approval",
        config_parameter="zehntech_sale_discount_on_total_amount.sale_discount_approval",
        help="Enable this option to activate the approval process for discounts given on sale orders and invoices.")

    discount_limit_percentage = fields.Float(
        string="Discount limit requires approval in %",
        config_parameter="zehntech_sale_discount_on_total_amount.discount_limit_percentage",
        help="Specify the maximum discount percentage allowed without approval. Discounts exceeding this percentage will require manager approval.")

