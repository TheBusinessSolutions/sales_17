from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError
from odoo import _

class BulkDiscountApprovalWizard(models.TransientModel):
    _name = 'bulk.discount.approval.wizard'
    _description = 'Bulk Discount Approval Wizard'

    action = fields.Selection([
        ('approve', 'Approve'),
        ('reject', 'Reject')
    ], required=True, string="Action", help="Select whether you want to approve or reject the selected records.")

    is_approval_manager = fields.Boolean(
        compute='_compute_is_approval_manager', 
        store=False, 
        help="Indicates whether the current user belongs to the Discount Approval Manager group."
    )

    @api.depends()
    def _compute_is_approval_manager(self):
        group = self.env.ref('zehntech_sale_discount_on_total_amount.group_discount_approval_manager')
        for wizard in self:
            wizard.is_approval_manager = group in self.env.user.groups_id
            


    def apply_bulk_action(self):
        active_ids = self.env.context.get('active_ids', [])
        active_model = self.env.context.get('active_model')

        group = self.env.ref('zehntech_sale_discount_on_total_amount.group_discount_approval_manager')
        if group not in self.env.user.groups_id:
            raise AccessError(_("You are not authorized to approve or reject discounts."))

        records = self.env[active_model].browse(active_ids)

        invalid_records = records.filtered(lambda r: r.state != 'waiting_approval')
        if invalid_records:
            raise UserError(_(
                "Some selected records are not in 'Waiting for Discount Approval' state. "
                "Please make sure all selected records are in the correct state."
            ))

        for record in records:
            if record.amount_untaxed == 0.0:
                raise UserError(_(
                    "Cannot proceed because some records have no products added. Please add at least one product before continuing."))

            discount_value = record.discount_rate if hasattr(record, 'discount_rate') else 0.0
            if discount_value == 0.0 and self.action == 'approve':
                raise UserError(_("Cannot approve discount because the discount value is zero for some records. Please set a valid discount."))

            if active_model == 'sale.order':
                if self.action == 'approve':
                    record.action_approve_discount()
                elif self.action == 'reject':
                    record.action_reject_discount()

            elif active_model == 'account.move':
                if self.action == 'approve':
                    record.action_approve_discount()
                elif self.action == 'reject':
                    record.action_reject_discount()


        action_message = 'approval' if self.action == 'approve' else 'rejection'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Bulk discount %s completed successfully.') % action_message,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }


