# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CrmTeam(models.Model):
    _inherit = 'crm.team'
    
    sale_approver_line = fields.One2many('sale.approver', 'team_id', string="Sale Order Approver(s)")


class SaleApprover(models.Model):
    _name = 'sale.approver'
    _description = 'Sale Approver'
    _order = 'sequence, id'

    team_id = fields.Many2one('crm.team', string="Sales Team")
    sale_id = fields.Many2one('sale.order', string="Sale Order")
    sequence = fields.Integer(default=10)
    user_id = fields.Many2one('res.users', string="Approver", required=True)
    approved_order = fields.Boolean(string="Approved", default=False)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res._trigger_sale_order_recompute()
        return res

    def write(self, vals):
        res = super().write(vals)
        self._trigger_sale_order_recompute()
        return res

    def _trigger_sale_order_recompute(self):
        """Recompute approval fields on related Sale Orders"""
        # Directly linked SOs
        sale_orders = self.filtered('sale_id').mapped('sale_id')
        if sale_orders:
            sale_orders._compute_can_confirm_order()
            sale_orders._compute_approval_display()
        
        # SOs linked via changed teams
        teams = self.filtered('team_id').mapped('team_id')
        if teams:
            orders = self.env['sale.order'].search([
                ('team_id', 'in', teams.ids),
                ('state', 'in', ['draft', 'sent'])
            ])
            if orders:
                orders._compute_can_confirm_order()
                orders._compute_approval_display()