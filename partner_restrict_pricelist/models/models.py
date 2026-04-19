# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    allowed_pricelist_ids = fields.Many2many("product.pricelist")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    allowed_pricelist_ids = fields.Many2many(related="partner_id.allowed_pricelist_ids")
