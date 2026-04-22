# -- coding: utf-8 --
from odoo import fields, models, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(selection_add=[
        ('to_approve', 'To Approve')
    ], ondelete={'to_approve': 'set default'})

    def button_approve(self):
        """Approve the order and move to 'sale' state."""
        # REPLACE 'sales_order_double_approval' with your actual module folder name
        if not (self.user_has_groups('sales_team.group_sale_manager') or 
                self.user_has_groups('sales_order_double_approval.group_sale_order_approver')):
            raise UserError(_("You do not have permission to approve this sale order."))
        
        # Change state to 'sale'. This triggers deliveries/manufacturing.
        self.write({'state': 'sale'})
        return True

    def action_confirm(self):
        """Intercept confirmation to check for approval."""
        ir_config = self.env['ir.config_parameter'].sudo()
        so_approval_enabled = ir_config.get_param('sales_order_double_approval.so_approval', default=False)
        
        try:
            min_amount = float(ir_config.get_param('sales_order_double_approval.so_min_amount', default=0.0))
        except ValueError:
            min_amount = 0.0

        # Check if approval is needed
        if so_approval_enabled and self.amount_total > min_amount:
            # REPLACE 'sales_order_double_approval' with your actual module folder name
            is_manager = self.user_has_groups('sales_team.group_sale_manager')
            is_approver = self.user_has_groups('sales_order_double_approval.group_sale_order_approver')
            
            if is_manager or is_approver:
                # User has rights, proceed normally
                return super(SaleOrder, self).action_confirm()
            else:
                # User needs approval, set state to 'to_approve' and STOP
                self.write({'state': 'to_approve'})
                return True
        else:
            # No approval needed, proceed normally
            return super(SaleOrder, self).action_confirm()

    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True