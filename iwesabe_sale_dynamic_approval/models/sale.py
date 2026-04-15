# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # =========================
    # FIELDS
    # =========================
    sale_approver_line = fields.One2many(
        'sale.approver', 'sale_id', copy=False
    )

    can_confirm_order = fields.Boolean(
        compute="_compute_can_confirm_order",
        store=False
    )

    # ✅ IMPORTANT: store=True for tree view
    approval_status = fields.Char(
        compute="_compute_approval_status",
        store=True
    )

    next_approver_name = fields.Char(
        compute="_compute_approval_status",
        store=True
    )

    # =========================
    # CREATE / WRITE
    # =========================
    @api.model
    def create(self, vals):
        order = super().create(vals)
        order._sync_approver_lines()
        return order

    def write(self, vals):
        res = super().write(vals)
        if 'team_id' in vals:
            self._sync_approver_lines()
        return res

    # =========================
    # COMPUTE METHODS
    # =========================
    @api.depends('state', 'sale_approver_line.approved_order')
    def _compute_can_confirm_order(self):
        for order in self:
            order.can_confirm_order = order._check_can_confirm()

    def _check_can_confirm(self):
        self.ensure_one()

        if self.state not in ('draft', 'sent'):
            return False

        if not self.sale_approver_line:
            return True

        pending = self.sale_approver_line.filtered(
            lambda x: not x.approved_order
        ).sorted('sequence')

        if not pending:
            return True

        return self.env.user == pending[0].user_id

    @api.depends(
        'state',
        'sale_approver_line.approved_order',
        'sale_approver_line.sequence',
        'sale_approver_line.user_id'
    )
    def _compute_approval_status(self):
        for record in self:

            if record.state not in ('draft', 'sent'):
                record.approval_status = 'N/A'
                record.next_approver_name = False
                continue

            if not record.sale_approver_line:
                record.approval_status = 'No Approval'
                record.next_approver_name = False
                continue

            pending = record.sale_approver_line.filtered(
                lambda x: not x.approved_order
            ).sorted('sequence')

            if not pending:
                record.approval_status = 'Fully Approved'
                record.next_approver_name = False
            else:
                record.approval_status = 'Pending Approval'
                record.next_approver_name = pending[0].user_id.name

    # =========================
    # CORE LOGIC
    # =========================
    def _sync_approver_lines(self):
        for order in self:

            if not order.id:
                continue

            if not order.team_id or not order.team_id.sale_approver_line:
                continue

            existing_users = order.sale_approver_line.mapped('user_id')
            lines_to_create = []

            for line in order.team_id.sale_approver_line.sorted('sequence'):
                if line.user_id not in existing_users:
                    lines_to_create.append({
                        'sale_id': order.id,
                        'user_id': line.user_id.id,
                        'sequence': line.sequence,
                        'approved_order': False,
                    })

            if lines_to_create:
                self.env['sale.approver'].create(lines_to_create)

    # =========================
    # APPROVAL FLOW
    # =========================
    def action_confirm(self):
        for order in self:

            if not order.sale_approver_line:
                return super().action_confirm()

            order._sync_approver_lines()

            pending = order.sale_approver_line.filtered(
                lambda x: not x.approved_order
            ).sorted('sequence')

            if not pending:
                return super().action_confirm()

            current = pending[0]

            if self.env.user != current.user_id:
                raise UserError(_(
                    "You are not the current approver.\n"
                    "Current approver: %s"
                ) % current.user_id.name)

            current.approved_order = True

            remaining = order.sale_approver_line.filtered(
                lambda x: not x.approved_order
            )

            if not remaining:
                return super().action_confirm()

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Approval Recorded'),
                    'message': _('Waiting for: %s') %
                               remaining.sorted('sequence')[0].user_id.name,
                    'type': 'success',
                }
            }