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
                # Force today's date for the rate lookup
                line._compute_area_price(ref_date=today)
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
    # Core pricing logic
    # ─────────────────────────────────────────────────────────────────────────

    def _compute_area_price(self, ref_date=None):
        """
        Compute and set price_unit for area-priced lines.

        Flow:
          1. base_price = area_sqm × Pricing Based Cost rate
          2. Apply pricelist rule:
             a. Fixed Price rule  → use fixed price directly (pricelist wins)
             b. Discount % rule   → base_price × (1 - discount%)
             c. No rule           → use base_price as-is
          3. Snapshot applied_cost_rate and applied_cost_rate_id

        ref_date: date to use for cost lookup.
                  Defaults to order date (for initial calc) or today (for recalc).
        """
        CostRate = self.env['product.area.cost']

        for line in self:
            if not line.product_id or not line.product_id.use_area_pricing:
                continue

            # ── Determine reference date ──────────────────────────────────
            lookup_date = ref_date or (
                line.order_id.date_order.date()
                if line.order_id.date_order
                else fields.Date.context_today(line)
            )

            # ── Fetch rate ────────────────────────────────────────────────
            rate_record = CostRate.get_rate_record_for_product(
                line.product_id.id, ref_date=lookup_date
            )
            rate = rate_record.rate if rate_record else 0.0

            # ── Compute area (use stored value) ───────────────────────────
            area = line.area_sqm or (line.area_width * line.area_height)

            # ── Base price ────────────────────────────────────────────────
            base_price = area * rate

            # ── Apply pricelist ───────────────────────────────────────────
            final_price = line._apply_pricelist_to_area_price(base_price)

            # ── Write values ──────────────────────────────────────────────
            line.price_unit = final_price
            line.applied_cost_rate = rate
            line.applied_cost_rate_id = rate_record.id if rate_record else False

    def _apply_pricelist_to_area_price(self, base_price):
        """
        Apply pricelist rules to the area-computed base_price.

        Pricelist priority (pricelist WINS over formula):
          1. Fixed Price rule for this product/category → return fixed price
          2. Percentage Discount rule                  → base_price × (1 - disc%)
          3. No matching rule                          → return base_price

        Returns the final unit price (float).
        """
        self.ensure_one()
        pricelist = self.order_id.pricelist_id
        if not pricelist or base_price == 0.0:
            return base_price

        partner = self.order_id.partner_id
        product = self.product_id
        qty = self.product_uom_qty or 1.0
        date = self.order_id.date_order or fields.Datetime.now()

        # Use Odoo's pricelist to get the price
        # get_product_price returns the final price after all pricelist rules
        pricelist_price = pricelist.get_product_price(
            product, qty, partner, date=date, uom_id=self.product_uom.id
        )

        # Detect if pricelist returned a Fixed Price (not derived from base_price)
        # We do this by checking if any rule for this product is type 'fixed'
        rule_id = pricelist._get_product_rule(
            product, qty, uom=self.product_uom, date=date
        )
        if rule_id:
            rule = self.env['product.pricelist.item'].browse(rule_id)
            if rule.compute_price == 'fixed':
                # Fixed price rule — pricelist wins completely
                self.discount = 0.0
                return rule.fixed_price

            elif rule.compute_price == 'percentage':
                # Discount % rule applied on top of our base_price
                discount_pct = rule.percent_price or 0.0
                discounted = base_price * (1.0 - discount_pct / 100.0)
                # Store the discount visibly on the line
                self.discount = discount_pct
                return base_price  # price_unit stays as base; discount shown separately

            elif rule.compute_price == 'formula':
                # Formula-based rule: apply the price ratio against our base
                # (edge case — treat like no rule, return base_price)
                return base_price

        # No matching pricelist rule — return base price
        return base_price

    # ─────────────────────────────────────────────────────────────────────────
    # Onchange / override hooks
    # ─────────────────────────────────────────────────────────────────────────

    @api.onchange('product_id')
    def _onchange_product_id_area(self):
        """Populate default dimensions when product is selected."""
        if self.product_id and self.product_id.use_area_pricing:
            self.area_width = self.product_id.default_width
            self.area_height = self.product_id.default_height
            # Trigger price computation after dimensions are set
            self._compute_area_price()

    @api.onchange('area_width', 'area_height')
    def _onchange_dimensions(self):
        """Recompute price when dimensions change."""
        if self.product_id and self.product_id.use_area_pricing:
            self._compute_area_price()

    @api.onchange('product_uom_qty')
    def _onchange_qty_area(self):
        """Recompute price when qty changes (pricelist qty breaks may apply)."""
        if self.product_id and self.product_id.use_area_pricing:
            self._compute_area_price()

    def _get_display_price(self):
        """
        Override Odoo's standard price getter for area-priced products.
        Returns the area-computed price instead of the standard pricelist price.
        """
        self.ensure_one()
        if self.product_id and self.product_id.use_area_pricing:
            # Trigger area price computation and return current price_unit
            self._compute_area_price()
            return self.price_unit
        return super()._get_display_price()

    # ─────────────────────────────────────────────────────────────────────────
    # Override create/write to ensure area pricing is applied on save
    # ─────────────────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            if line.product_id and line.product_id.use_area_pricing:
                line._compute_area_price()
        return lines
