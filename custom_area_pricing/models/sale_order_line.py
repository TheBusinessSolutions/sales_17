# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_recalculate_area_prices(self):
        """
        Recalculate all area-priced lines using TODAY's latest Pricing Based Cost.
        Only allowed on draft (quotation) orders.
        """
        self.ensure_one()
        if self.state not in ('draft', 'sent'):
            raise UserError(_('You can only recalculate prices on draft quotations.'))

        today = fields.Date.context_today(self)
        recalculated = 0

        for line in self.order_line:
            if line.product_id and line.product_id.use_area_pricing:
                line._set_area_base_price(ref_date=today)
                recalculated += 1

        if recalculated == 0:
            raise UserError(_('No area-priced products found on this quotation.'))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Prices Recalculated'),
                'message': _(
                    '%d line(s) updated using the latest Pricing Based Cost as of today (%s).'
                ) % (recalculated, today),
                'sticky': False,
                'type': 'success',
            },
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # ── Dimension fields ──────────────────────────────────────────────────────
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

    # ── Cost rate snapshot ────────────────────────────────────────────────────
    applied_cost_rate_id = fields.Many2one(
        'product.area.cost',
        string='Applied Cost Rate',
        readonly=True,
        copy=False,
        help='Snapshot of the Pricing Based Cost record used when this line was priced.',
    )
    applied_cost_rate = fields.Float(
        string='Rate Used (per m²)',
        digits=(16, 4),
        readonly=True,
        copy=False,
        help='The actual rate value at the time of pricing — preserved even if the '
             'rate record is later modified.',
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
    # Core: compute and store area base price + rate snapshot
    # ─────────────────────────────────────────────────────────────────────────

    def _set_area_base_price(self, ref_date=None):
        """
        Step 1 of pricing:
        Compute base_price = Width x Height x Pricing Based Cost Rate
        and store it as price_unit + snapshot the rate used.

        Pricelist is NOT applied here — Odoo's standard engine handles
        that automatically via _get_display_price override below.
        """
        CostRate = self.env['product.area.cost']

        for line in self:
            if not line.product_id or not line.product_id.use_area_pricing:
                continue

            lookup_date = ref_date or (
                line.order_id.date_order.date()
                if line.order_id.date_order
                else fields.Date.context_today(line)
            )

            rate_record = CostRate.get_rate_record_for_product(
                line.product_id.id, ref_date=lookup_date
            )
            rate = rate_record.rate if rate_record else 0.0
            area = (line.area_width or 0.0) * (line.area_height or 0.0)
            base_price = area * rate

            line.price_unit = base_price
            line.applied_cost_rate = rate
            line.applied_cost_rate_id = rate_record.id if rate_record else False

    # ─────────────────────────────────────────────────────────────────────────
    # Override _get_display_price so Odoo's pricelist engine uses our base price
    # ─────────────────────────────────────────────────────────────────────────

    def _get_display_price(self):
        """
        For area-priced products: return the area-computed base price as the
        'list price' that the pricelist engine applies its rules against.

          - Percentage discount rule  -> base_price shown, discount% applied
          - Fixed price rule          -> fixed price wins (standard behaviour)
          - No rule                   -> base_price used as-is

        All standard Odoo pricelist behaviour is preserved unchanged.
        """
        self.ensure_one()
        if self.product_id and self.product_id.use_area_pricing:
            return self.price_unit
        return super()._get_display_price()

    # ─────────────────────────────────────────────────────────────────────────
    # Onchange hooks
    # ─────────────────────────────────────────────────────────────────────────

    @api.onchange('product_id')
    def _onchange_product_id_area(self):
        """Populate default dimensions when area-priced product is selected."""
        if self.product_id and self.product_id.use_area_pricing:
            self.area_width = self.product_id.default_width
            self.area_height = self.product_id.default_height
            self._set_area_base_price()

    @api.onchange('area_width', 'area_height')
    def _onchange_dimensions(self):
        """Recompute price when dimensions change."""
        if self.product_id and self.product_id.use_area_pricing:
            self._set_area_base_price()

    @api.onchange('product_uom_qty')
    def _onchange_qty_area(self):
        """Recompute when qty changes (pricelist qty-break rules may apply)."""
        if self.product_id and self.product_id.use_area_pricing:
            self._set_area_base_price()

    # ─────────────────────────────────────────────────────────────────────────
    # Override create to ensure area pricing on programmatic line creation
    # ─────────────────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            if line.product_id and line.product_id.use_area_pricing:
                line._set_area_base_price()
        return lines