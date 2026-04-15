# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CrmTeam(models.Model):
    _inherit = 'crm.team'
    sale_approver_line = fields.One2many('sale.approver', 'team_id', string="Sale Order Approver(s)")

class SaleApprover(models.Model):
    _name = 'sale.approver'
    _description = 'Sale Approver'
    _order = 'sequence, id'

    team_id = fields.Many2one('crm.team')
    sale_id = fields.Many2one('sale.order')
    sequence = fields.Integer(default=10)
    user_id = fields.Many2one('res.users', required=True)
    approved_order = fields.Boolean(default=False)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res._trigger_sale_order_update()
        return res

    def write(self, vals):
        res = super().write(vals)
        self._trigger_sale_order_update()
        return res

    def _trigger_sale_order_update(self):
        """Recompute approval fields on related Sale Orders"""
        sale_ids = self.filtered('sale_id').mapped('sale_id')
        team_ids = self.filtered('team_id').mapped('team_id')
        
        # Directly linked SOs
        if sale_ids:
            sale_ids._compute_can_confirm_order()
            sale_ids._compute_approval_status()
            
        # SOs linked via changed teams
        if team_ids:
            orders = self.env['sale.order'].search([
                ('team_id', 'in', team_ids.ids),
                ('state', 'in', ['draft', 'sent'])
            ])
            if orders:
                orders._compute_can_confirm_order()
                orders._compute_approval_status()