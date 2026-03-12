# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    area_cost_rate_id = fields.Many2one(
        'product.area.cost',
        string='Pricing Based Cost',
        readonly=True,
        copy=False,
        help='The active Pricing Based Cost rate at the time this quotation was created.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders:
            order._set_current_area_cost_rate()
        return orders

    def _set_current_area_cost_rate(self):
        rate = self.env['product.area.cost'].get_current_rate_record()
        if rate:
            self.area_cost_rate_id = rate.id

    def action_recalculate_area_prices(self):
        self.ensure_one()
        if self.state not in ('draft', 'sent'):
            raise UserError(_('You can only recalculate prices on draft quotations.'))

        recalculated = 0
        for line in self.order_line:
            if line.product_id and line.product_id.use_area_pricing:
                line._snapshot_area_cost_rate()
                line.product_id_change()
                recalculated += 1

        if recalculated == 0:
            raise UserError(_('No area-priced products found on this quotation.'))

        # Update the rate reference on the order too
        self._set_current_area_cost_rate()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Prices Recalculated'),
                'message': _('%d line(s) refreshed to current pricing.') % recalculated,
                'sticky': False,
                'type': 'success',
            },
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    area_width = fields.Float(string='Width (m)', digits=(16, 4), default=0.0)
    area_height = fields.Float(string='Height (m)', digits=(16, 4), default=0.0)
    area_sqm = fields.Float(
        string='Area (m²)', digits=(16, 4),
        compute='_compute_area_sqm', store=True, readonly=True,
    )
    applied_cost_rate = fields.Float(
        string='Rate Used (per m²)', digits=(16, 4),
        readonly=True, copy=False,
    )
    is_area_priced = fields.Boolean(
        string='Area Priced',
        compute='_compute_is_area_priced', store=True,
    )

    @api.depends('area_width', 'area_height')
    def _compute_area_sqm(self):
        for line in self:
            line.area_sqm = line.area_width * line.area_height

    @api.depends('product_id')
    def _compute_is_area_priced(self):
        for line in self:
            line.is_area_priced = bool(
                line.product_id and line.product_id.use_area_pricing
            )

    def _snapshot_area_cost_rate(self):
        CostRate = self.env['product.area.cost']
        for line in self:
            if not line.product_id or not line.product_id.use_area_pricing:
                continue
            rate = CostRate.get_rate_for_product(
                line.product_id.product_tmpl_id.id,
                ref_date=fields.Date.context_today(line),
            )
            line.applied_cost_rate = rate

    @api.onchange('product_id')
    def _onchange_product_id_area(self):
        if self.product_id and self.product_id.use_area_pricing:
            self.area_width = self.product_id.default_width
            self.area_height = self.product_id.default_height
            CostRate = self.env['product.area.cost']
            self.applied_cost_rate = CostRate.get_rate_for_product(
                self.product_id.product_tmpl_id.id,
                ref_date=fields.Date.context_today(self),
            )

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            if line.product_id and line.product_id.use_area_pricing:
                line._snapshot_area_cost_rate()
        return lines
