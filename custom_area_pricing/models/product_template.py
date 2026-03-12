# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    use_area_pricing = fields.Boolean(
        string='Use Area Pricing',
        default=False,
        help='When enabled, the sales price is computed as:\n'
             '  Width × Height × Pricing Based Cost Rate\n'
             'The standard product Cost (standard_price) is unaffected.',
    )
    default_width = fields.Float(
        string='Default Width (m)',
        digits=(16, 4),
        default=0.0,
        help='Default width in meters. Can be overridden on each quotation line.',
    )
    default_height = fields.Float(
        string='Default Height (m)',
        digits=(16, 4),
        default=0.0,
        help='Default height in meters. Can be overridden on each quotation line.',
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    use_area_pricing = fields.Boolean(
        related='product_tmpl_id.use_area_pricing',
        store=True,
        readonly=True,
    )
    default_width = fields.Float(
        related='product_tmpl_id.default_width',
        store=True,
        readonly=True,
    )
    default_height = fields.Float(
        related='product_tmpl_id.default_height',
        store=True,
        readonly=True,
    )
