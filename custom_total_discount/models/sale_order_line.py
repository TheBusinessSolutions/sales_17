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

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    discount = fields.Float(
        string="Total Discount (%)",
        compute="_compute_discount",
        store=True,
        readonly=True,
    )
    discount1 = fields.Float(
        string="Discount (%)",
        digits="Discount",
    )
    discount2 = fields.Float(
        string="Discount 2",
        compute="_compute_discount_2",
        store=True,
    )

    @api.depends("order_id.add_discount", "order_id.add_discount_type", "price_unit", "product_uom_qty")
    def _compute_discount_2(self):
        for order in self.mapped('order_id'):
            if not order.add_discount or not order.order_line:
                for line in order.order_line:
                    line.discount2 = 0.0
                continue
            total_amount = sum(line.price_unit * line.product_uom_qty for line in order.order_line) or 1.0
            discount_application = self.env['ir.config_parameter'].sudo().get_param(
                'invoice_sales_custom_discount.discount_application', 'after_tax'
            )
            if discount_application == 'before_tax':
                if order.add_discount_type == 'fixed':
                    for line in order.order_line:
                        proportion = (line.price_unit * line.product_uom_qty) / total_amount
                        line.discount2 = order.add_discount * proportion
                else:
                    for line in order.order_line:
                        line.discount2 = order.add_discount
            else:
                if order.add_discount_type == 'fixed':
                    fixed_discount = order.add_discount / 1.15
                    for line in order.order_line:
                        proportion = (line.price_unit * line.product_uom_qty) / total_amount
                        line.discount2 = fixed_discount * proportion
                else:
                    for line in order.order_line:
                        line.discount2 = order.add_discount

    @api.depends("discount1", "discount2", "price_unit", "product_uom_qty", "order_id.add_discount_type")
    def _compute_discount(self):
        for line in self:
            base_amount = line.price_unit * line.product_uom_qty
            discount1_amount = base_amount * (line.discount1 or 0.0) / 100.0
            if line.order_id.add_discount_type == 'fixed':
                discount2_amount = line.discount2 or 0.0
            else:
                discount2_amount = base_amount * (line.discount2 or 0.0) / 100.0
            total_discount_amount = discount1_amount + discount2_amount
            line.discount = (total_discount_amount / base_amount * 100) if base_amount else 0.0
            line.price_subtotal = base_amount - total_discount_amount