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


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

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

    @api.depends("move_id.add_discount", "move_id.add_discount_type", "price_unit", "quantity")
    def _compute_discount_2(self):
        for move in self.mapped('move_id'):
            discount_application = self.env['ir.config_parameter'].sudo().get_param(
                'invoice_sales_custom_discount.discount_application', 'after_tax'
            )
            if not move.add_discount or not move.invoice_line_ids:
                for line in move.invoice_line_ids:
                    line.discount2 = 0.0
                continue
            total_amount = sum(line.price_unit * line.quantity for line in move.invoice_line_ids) or 1.0
            tax_rates = []
            for line in move.invoice_line_ids:
                if line.tax_ids:
                    line_tax_rate = sum(tax.amount for tax in line.tax_ids) / 100.0
                    tax_rates.append(1.0 + line_tax_rate)
                else:
                    tax_rates.append(1.0)
            average_tax_rate = sum(tax_rates) / len(tax_rates) if tax_rates else 1.0
            if discount_application == 'before_tax':
                if move.add_discount_type == 'fixed':
                    for line in move.invoice_line_ids:
                        proportion = (line.price_unit * line.quantity) / total_amount
                        line.discount2 = move.add_discount * proportion
                else:
                    for line in move.invoice_line_ids:
                        line.discount2 = move.add_discount
            else:
                if move.add_discount_type == 'fixed':
                    fixed_discount = move.add_discount / average_tax_rate
                    for line in move.invoice_line_ids:
                        proportion = (line.price_unit * line.quantity) / total_amount
                        line.discount2 = fixed_discount * proportion
                else:
                    for line in move.invoice_line_ids:
                        line.discount2 = move.add_discount

    @api.depends("discount1", "discount2", "price_unit", "quantity", "move_id.add_discount_type")
    def _compute_discount(self):
        for line in self:
            base_amount = line.price_unit * line.quantity
            discount1_amount = base_amount * (line.discount1 or 0.0) / 100.0
            if line.move_id.add_discount_type == 'fixed':
                discount2_amount = line.discount2 or 0.0
            else:
                discount2_amount = base_amount * (line.discount2 or 0.0) / 100.0
            total_discount_amount = discount1_amount + discount2_amount
            line.discount = (total_discount_amount / base_amount * 100) if base_amount else 0.0
            line.price_subtotal = base_amount - total_discount_amount

    def _fix_discount_values(self, values):
        if "discount" in values and "discount1" not in values:
            values["discount1"] = values.pop("discount")
        return values

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([self._fix_discount_values(vals) for vals in vals_list])

    def write(self, vals):
        return super().write(self._fix_discount_values(vals))




