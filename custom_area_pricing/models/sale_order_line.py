# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_recalculate_area_prices(self):
        """
        Refresh all area-priced lines to the latest lst_price
        (which reflects the current Pricing Based Cost rate).
        Only allowed on draft quotations.
        """
        self.ensure_one()
        if self.state not in ('draft', 'sent'):
            raise UserError(_('You can only recalculate prices on draft quotations.'))

        recalculated = 0
        for line in self.order_line:
            if line.product_id and line.product_id.use_area_pricing:
                # Snapshot the current rate
                line._snapshot_area_cost_rate()
                # Re-trigger standard product onchange to refresh price+discount
                line.product_id_change()
                recalculated += 1

        if recalculated == 0:
            raise UserError(_('No area-priced products found on this quotation.'))

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

    # ── Dimension fields (informational — shown on line) ──────────────────────
    area_width = fields.Float(
        string='Width (m)',
        digits=(16, 4),
        default=0.0,
    )
    area_height = fields.Float(
        string='Height (m)',
        digits=(16, 4),
        default=0.0,
    )
    area_sqm = fields.Float(
        string='Area (m²)',
        digits=(16, 4),
        compute='_compute_area_sqm',
        store=True,
        readonly=True,
    )

    # ── Rate snapshot (audit trail) ───────────────────────────────────────────
    applied_cost_rate = fields.Float(
        string='Rate Used (per m²)',
        digits=(16, 4),
        readonly=True,
        copy=False,
        help='Pricing Based Cost rate active when this line was created.',
    )

    # ── Visibility helper ─────────────────────────────────────────────────────
    is_area_priced = fields.Boolean(
        string='Area Priced',
        compute='_compute_is_area_priced',
        store=True,
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Computed fields
    # ─────────────────────────────────────────────────────────────────────────

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

    # ─────────────────────────────────────────────────────────────────────────
    # Rate snapshot helper
    # ─────────────────────────────────────────────────────────────────────────

    def _snapshot_area_cost_rate(self):
        """
        Record the currently active Pricing Based Cost rate on this SO line.
        This is for audit purposes only — pricing itself comes from lst_price.
        """
        CostRate = self.env['product.area.cost']
        for line in self:
            if not line.product_id or not line.product_id.use_area_pricing:
                continue
            rate = CostRate.get_rate_for_product(
                line.product_id.product_tmpl_id.id,
                ref_date=fields.Date.context_today(line),
            )
            line.applied_cost_rate = rate

    # ─────────────────────────────────────────────────────────────────────────
    # Onchange: populate dimensions from product defaults
    # ─────────────────────────────────────────────────────────────────────────

    @api.onchange('product_id')
    def _onchange_product_id_area(self):
        """Populate default W/H and snapshot rate when product is selected."""
        if self.product_id and self.product_id.use_area_pricing:
            self.area_width = self.product_id.default_width
            self.area_height = self.product_id.default_height
            # Snapshot the rate for audit — price comes from lst_price via standard flow
            CostRate = self.env['product.area.cost']
            self.applied_cost_rate = CostRate.get_rate_for_product(
                self.product_id.product_tmpl_id.id,
                ref_date=fields.Date.context_today(self),
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Override create to snapshot rate on programmatic line creation
    # ─────────────────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            if line.product_id and line.product_id.use_area_pricing:
                line._snapshot_area_cost_rate()
        return lines
