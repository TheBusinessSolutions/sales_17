# -*- coding: utf-8 -*-
##############################################################################
#
#    Mohamed Hussein.
#    Copyright (C) 2024 Mohamed Hussein (<https://www.linkedin.com/in/muhmmdhussein/>).
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL-3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software without permission.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL-3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    DISCOUNT_TYPE_SELECTION = [
        ('fixed', 'Fixed Amount'),
        ('percent', 'Percentage'),
    ]

    add_discount = fields.Float(
        string="Add Discount",
        default=0.0,
    )
    add_discount_type = fields.Selection(
        selection=DISCOUNT_TYPE_SELECTION,
        string="Discount Type",
        default='fixed',
    )
    total_discount = fields.Monetary(
        string='Total Discount',
        compute='_compute_total_discount',
        store=True,
        currency_field='currency_id',
    )
    amount_after_discount = fields.Monetary(
        string='Total After Discount',
        compute='_compute_amount_after_discount',
        store=True,
        default=0.0,
        currency_field='currency_id',
    )
    amount_due = fields.Monetary(
        string='Amount Due',
        compute='_compute_amount_due',
        store=True,
        currency_field='currency_id',
    )
    amount_untaxed = fields.Monetary(
        string='Untaxed Amount',
        compute='_compute_amount_untaxed',
        store=True,
        currency_field='currency_id',
    )
    partner_vat = fields.Char(
        string='Partner VAT',
        related='partner_id.vat',
        store=True,
    )
    tax_value = fields.Monetary(
        string="Taxes",
        compute="_compute_tax_value",
        currency_field="currency_id",
    )
    amount_total_before_discount = fields.Monetary(
        string='Total Before Discount',
        compute='_compute_amount_total_before_discount',
        currency_field='currency_id',
    )

    @api.depends('amount_tax')
    def _compute_tax_value(self):
        for record in self:
            record.tax_value = record.amount_tax
            
    @api.depends('order_line.discount1', 'order_line.discount2', 'order_line.price_unit',
             'order_line.product_uom_qty', 'add_discount_type')
    def _compute_total_discount(self):
        for order in self:
            total = 0.0
            for line in order.order_line:
                base_amount = line.price_unit * line.product_uom_qty
                discount1_amount = base_amount * (line.discount1 or 0.0) / 100.0
                if order.add_discount_type == 'fixed':
                    discount2_amount = line.discount2 or 0.0
                else:  # 'percent'
                    discount2_amount = base_amount * (line.discount2 or 0.0) / 100.0
                total += discount1_amount + discount2_amount
            order.total_discount = total

    @api.depends('amount_total', 'add_discount', 'add_discount_type')
    def _compute_amount_after_discount(self):
        for order in self:
            discount_application = self.env['ir.config_parameter'].sudo().get_param(
                'invoice_sales_custom_discount.discount_application', 'after_tax'
            )
            if discount_application == 'before_tax':
                order.amount_after_discount = order.amount_total
            else:
                if order.add_discount_type == 'fixed':
                    order.amount_after_discount = order.amount_total - order.add_discount
                else:
                    order.amount_after_discount = order.amount_total * (1 - order.add_discount / 100)

    @api.depends('amount_after_discount')
    def _compute_amount_due(self):
        for order in self:
            order.amount_due = order.amount_after_discount

    @api.depends('order_line.price_subtotal')
    def _compute_amount_untaxed(self):
        for order in self:
            order.amount_untaxed = sum(line.price_subtotal for line in order.order_line)

    @api.depends('amount_untaxed', 'amount_tax')
    def _compute_amount_total_before_discount(self):
        for order in self:
            order.amount_total_before_discount = order.amount_untaxed + order.amount_tax

    @api.onchange("add_discount", "add_discount_type")
    def _onchange_add_discount(self):
        if self.order_line:
            self.order_line._compute_discount_2()

    def write(self, vals):
        res = super().write(vals)
        if "add_discount" in vals or "add_discount_type" in vals:
            for order in self:
                order.order_line._compute_discount_2()
        return res