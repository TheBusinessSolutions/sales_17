# -- coding: utf-8 --
#############################################################################
# Cybrosys Technologies Pvt. Ltd.
# Copyright (C) 2024-TODAY Cybrosys Technologies(https://www.cybrosys.com)
# Author: Cybrosys Techno Solutions(https://www.cybrosys.com)
# You can modify it under the terms of the GNU LESSER
# GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
# You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
# (LGPL v3) along with this program.
# If not, see http://www.gnu.org/licenses/.
#############################################################################
from odoo import fields, models, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(selection_add=[
        ('to_approve', 'To Approve')
    ], ondelete={'to_approve': 'set default'})

    def button_approve(self):
        """
        Method to approve the sale order. 
        This changes the state to 'sale', which triggers the creation of 
        deliveries, manufacturing orders, etc.
        """
        # Security check: Ensure user is Manager or Approver
        # REPLACE 'sales_order_double_approval' with your actual module folder name
        if not (self.user_has_groups('sales_team.group_sale_manager') or 
                self.user_has_groups('sales_order_double_approval.group_sale_order_approver')):
            raise UserError(_("You do not have permission to approve this sale order."))
        
        # Change state to 'sale'. 
        # In Odoo, changing state to 'sale' via write usually triggers the necessary actions.
        self.write({'state': 'sale'})
        return True

    def action_confirm(self):
        """
        Override to intercept confirmation.
        If approval is required and user is not authorized, set to 'to_approve'.
        If user IS authorized, proceed with normal confirmation.
        """
        # Get configuration parameters
        ir_config = self.env['ir.config_parameter'].sudo()
        so_approval_enabled = ir_config.get_param('sales_order_double_approval.so_approval', default=False)
        
        try:
            min_amount = float(ir_config.get_param('sales_order_double_approval.so_min_amount', default=0.0))
        except ValueError:
            min_amount = 0.0

        # Check if double validation is enabled AND amount exceeds limit
        if so_approval_enabled and self.amount_total > min_amount:
            # Check if current user is Sales Manager OR Sale Order Approver
            is_manager = self.user_has_groups('sales_team.group_sale_manager')
            # REPLACE 'sales_order_double_approval' with your actual module folder name
            is_approver = self.user_has_groups('sales_order_double_approval.group_sale_order_approver')
            
            if is_manager or is_approver:
                # User has rights, proceed with standard confirmation (creates deliveries, etc.)
                return super(SaleOrder, self).action_confirm()
            else:
                # User does NOT have rights. 
                # Set state to 'to_approve' and STOP. 
                # Do NOT call super(), so no deliveries/manufacturing are created yet.
                self.write({'state': 'to_approve'})
                return True
        else:
            # Approval not needed or amount below limit. Proceed normally.
            return super(SaleOrder, self).action_confirm()

    def action_cancel(self):
        """
        Method to cancel the sale order.
        """
        self.write({'state': 'cancel'})
        return True