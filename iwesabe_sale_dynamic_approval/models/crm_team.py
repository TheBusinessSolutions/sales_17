# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class CrmTeam(models.Model):
    _inherit = 'crm.team'

    sale_approver_line = fields.One2many('sale.approver', 'team_id',)

class SaleApprover(models.Model):
    _name = 'sale.approver'
    _description = 'Sale Approver'
    _order = 'sequence, id'

    team_id = fields.Many2one('crm.team')
    sale_id = fields.Many2one('sale.order')
    sequence = fields.Integer()
    user_id = fields.Many2one('res.users')
    approved_order = fields.Boolean('')

    @api.model
    def create(self,vals):
        result = super().create(vals)
        for res in result:
            if res.team_id:
                order_ids = self.env['sale.order'].search([('team_id','=',res.team_id.id),('state','in',['draft','sent'])])
                if order_ids:
                    order_ids._can_confirm_order()
        return result

    def write(self,vals):
        result = super().write(vals)
        for res in self:
            if res.team_id:
                order_ids = self.env['sale.order'].search([('team_id','=',res.team_id.id),('state','in',['draft','sent'])])
                if order_ids:
                    order_ids._can_confirm_order()
        return result