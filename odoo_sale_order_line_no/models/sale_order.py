# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2021 Cloudroits (info.cloudroits@gmail.com)
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models

#Add serial no in Sales Order lines
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    serial_no = fields.Integer(string='Sl. No.', compute='_compute_serial_no')

    @api.depends('sequence', 'order_id')
    def _compute_serial_no(self):
        for so_line in self:
            #if not so_line.serial_no:
            serial_no = 1
            for line in so_line.mapped('order_id').order_line:
                if line.product_id:
                    line.serial_no = serial_no
                    serial_no += 1
                else:
                    line.serial_no = 0
                        
#Add serial no in Invoice lines
class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    serial_no = fields.Integer(string='Sl. No.', compute='_compute_serial_no')

    @api.depends('sequence', 'move_id')
    def _compute_serial_no(self):
        for invoice_line in self:
            #if not invoice_line.serial_no:
            serial_no = 1
            for line in invoice_line.mapped('move_id').line_ids.sorted(key=lambda r: r.sequence):
                if line.product_id:
                    line.serial_no = serial_no
                    serial_no += 1
                else:
                    line.serial_no = 0