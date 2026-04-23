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
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

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



    @api.constrains('add_discount')
    def _check_discount_non_negative(self):
        for record in self:
            if record.add_discount < 0:
                raise ValidationError("Discount cannot be negative.")

    @api.depends('amount_tax')
    def _compute_tax_value(self):
        for record in self:
            record.tax_value = record.amount_tax

    @api.depends('invoice_line_ids.discount1', 'invoice_line_ids.discount2', 'invoice_line_ids.price_unit',
                 'invoice_line_ids.quantity', 'add_discount_type')
    def _compute_total_discount(self):
        for move in self:
            total = 0.0
            for line in move.invoice_line_ids:
                base_amount = line.price_unit * line.quantity
                discount1_amount = base_amount * (line.discount1 or 0.0) / 100.0
                if move.add_discount_type == 'fixed':
                    discount2_amount = line.discount2 or 0.0
                else:
                    discount2_amount = base_amount * (line.discount2 or 0.0) / 100.0
                total += discount1_amount + discount2_amount
            move.total_discount = total

    @api.depends('amount_total', 'add_discount', 'add_discount_type')
    def _compute_amount_after_discount(self):
        for move in self:
            discount_application = self.env['ir.config_parameter'].sudo().get_param(
                'invoice_sales_custom_discount.discount_application', 'after_tax'
            )
            if discount_application == 'before_tax':
                move.amount_after_discount = move.amount_total
            else:
                if move.add_discount_type == 'fixed':
                    move.amount_after_discount = move.amount_total - move.add_discount
                else:
                    move.amount_after_discount = move.amount_total * (1 - move.add_discount / 100)

    @api.depends('amount_after_discount')
    def _compute_amount_due(self):
        for move in self:
            move.amount_due = move.amount_after_discount

    @api.depends('invoice_line_ids.price_subtotal')
    def _compute_amount_untaxed(self):
        for move in self:
            move.amount_untaxed = sum(line.price_subtotal for line in move.invoice_line_ids)

    @api.depends('amount_untaxed', 'amount_tax')
    def _compute_amount_total_before_discount(self):
        for move in self:
            move.amount_total_before_discount = move.amount_untaxed + move.amount_tax

    @api.onchange("add_discount", "add_discount_type")
    def _onchange_add_discount(self):
        if self.invoice_line_ids:
            self.invoice_line_ids._compute_discount_2()

    def write(self, vals):
        res = super().write(vals)
        if "add_discount" in vals or "add_discount_type" in vals:
            for move in self:
                move.invoice_line_ids._compute_discount_2()
        return res


    















