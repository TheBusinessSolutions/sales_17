# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo Man
#
##############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OMGSalesDashboardTarget(models.Model):
    _name = 'omg.sales.dashboard.target'
    _description = 'Odoo Man Sales Dashboard Target'
    _order = 'month_start desc, scope, team_id, user_id'

    name = fields.Char(compute='_compute_name', store=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', store=True, readonly=True)
    scope = fields.Selection([('team', 'Sales Team'), ('user', 'Salesperson')], required=True, default='team')
    team_id = fields.Many2one('crm.team', string='Sales Team')
    user_id = fields.Many2one('res.users', string='Salesperson')
    month_start = fields.Date(required=True, help='Use the first day of the month for target planning.')
    target_amount = fields.Monetary(required=True)
    notes = fields.Text()

    _sql_constraints = [(
        'omg_sales_dashboard_target_unique',
        'unique(company_id, scope, team_id, user_id, month_start)',
        'A target already exists for the same company, month, and owner.',
    )]

    @api.depends('scope', 'team_id', 'user_id', 'month_start')
    def _compute_name(self):
        for record in self:
            owner = record.team_id.display_name if record.scope == 'team' else record.user_id.display_name
            record.name = '%s - %s' % (owner or 'Target', fields.Date.to_string(record.month_start) or '')

    @api.constrains('scope', 'team_id', 'user_id')
    def _check_scope_owner(self):
        for record in self:
            if record.scope == 'team' and not record.team_id:
                raise ValidationError(_('Sales Team is required for team targets.'))
            if record.scope == 'user' and not record.user_id:
                raise ValidationError(_('Salesperson is required for user targets.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('month_start'):
                vals['month_start'] = fields.Date.start_of(fields.Date.to_date(vals['month_start']), 'month')
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('month_start'):
            vals['month_start'] = fields.Date.start_of(fields.Date.to_date(vals['month_start']), 'month')
        return super().write(vals)
