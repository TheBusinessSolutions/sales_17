# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    can_confirm_order = fields.Boolean(compute="_compute_can_confirm_order")
    sale_approver_line = fields.One2many('sale.approver', 'sale_id', copy=False)
    
    # New fields for UI status & next approver tracking
    approval_status = fields.Char(compute="_compute_approval_status", string="Approval Status")
    next_approver_id = fields.Many2one('res.users', compute="_compute_approval_status", string="Next Approver")

    @api.depends('team_id', 'team_id.sale_approver_line', 'team_id.sale_approver_line.sequence',
                 'state', 'sale_approver_line', 'sale_approver_line.approved_order')
    @api.depends_context('uid')
    def _compute_can_confirm_order(self):
        for record in self:
            record.can_confirm_order = record._check_can_confirm()

    def _check_can_confirm(self):
        self.ensure_one()
        if self.state not in ('draft', 'sent'):
            return False
        if not self.team_id.sale_approver_line:
            return True

        self._sync_approver_lines()
        pending = self.sale_approver_line.filtered(lambda x: not x.approved_order)
        if not pending:
            return True
        return self.env.user == pending[0].user_id

    @api.depends('state', 'sale_approver_line', 'sale_approver_line.approved_order')
    def _compute_approval_status(self):
        for record in self:
            if record.state not in ('draft', 'sent'):
                record.approval_status = False
                record.next_approver_id = False
                continue

            record._sync_approver_lines()
            pending = record.sale_approver_line.filtered(lambda x: not x.approved_order)
            if not pending:
                record.approval_status = 'Fully Approved'
                record.next_approver_id = False
            else:
                record.approval_status = 'Pending Approval'
                record.next_approver_id = pending[0].user_id

    def _sync_approver_lines(self):
        """Sync approvers from Sales Team to Sale Order if missing"""
        for record in self:
            if not record.team_id.sale_approver_line:
                continue
            existing_user_ids = record.sale_approver_line.mapped('user_id')
            to_create = []
            for line in record.team_id.sale_approver_line.sorted('sequence'):
                if line.user_id not in existing_user_ids:
                    to_create.append({
                        'sale_id': record.id,
                        'team_id': record.team_id.id,
                        'user_id': line.user_id.id,
                        'sequence': line.sequence,
                        'approved_order': False,
                    })
            if to_create:
                self.env['sale.approver'].create(to_create)

    def _notify_next_approver(self):
        """Send internal notification & email to the next approver in line"""
        self.ensure_one()
        pending = self.sale_approver_line.filtered(lambda x: not x.approved_order)
        if not pending:
            return
        
        next_user = pending[0].user_id
        if not next_user.partner_id:
            return

        subject = _('Approval Required for Sale Order %s') % self.name
        body = _('Hello %s,<br/><br/>The sale order <b>%s</b> is currently pending your approval.<br/>Please review and confirm when ready.') % (next_user.name, self.name)
        
        self.message_post(
            body=body,
            subject=subject,
            message_type='notification',
            partner_ids=[next_user.partner_id.id],
            subtype_xmlid='mail.mt_comment'
        )

    def action_confirm(self):
        for order in self:
            if not order.team_id.sale_approver_line:
                return super(SaleOrder, self).action_confirm()

            order._sync_approver_lines()
            pending = order.sale_approver_line.filtered(lambda x: not x.approved_order)

            if not pending:
                return super(SaleOrder, self).action_confirm()

            if self.env.user != pending[0].user_id:
                raise UserError(_("You are not the designated approver for this step."))

            # Mark current step as approved
            pending[0].approved_order = True
            
            # Notify the next person in line
            order._notify_next_approver()

            # If all approved, confirm the SO
            if all(order.sale_approver_line.mapped('approved_order')):
                return super(SaleOrder, self).action_confirm()

            # Return success notification for partial approval
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Approval Step Completed'),
                    'message': _('Your approval has been recorded. The order is now pending the next approver.'),
                    'type': 'success',
                    'sticky': True,
                }
            }
        return super(SaleOrder, self).action_confirm()