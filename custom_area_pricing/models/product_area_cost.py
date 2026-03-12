# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductAreaCost(models.Model):
    """
    Pricing Based Cost Rate Table.

    Stores a dated cost-per-square-meter rate, optionally scoped
    to a product category.  Lookup always picks the most recent
    record whose date <= the reference date AND whose category
    matches the product (or has no category = applies to all).

    Category-specific records take priority over "all categories" records
    on the same date.
    """
    _name = 'product.area.cost'
    _description = 'Pricing Based Cost Rate'
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        help='e.g. "March 2025 Rate Increase" — for internal tracking only.',
    )
    date = fields.Date(
        string='Effective Date',
        required=True,
        default=fields.Date.context_today,
        help='This rate applies to quotations dated on or after this date '
             '(until a newer record exists).',
    )
    rate = fields.Float(
        string='Pricing Based Cost (per m²)',
        required=True,
        digits=(16, 4),
        help='Cost per square meter used to compute the sale price.\n'
             'Formula: Sales Price = Width × Height × Rate',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    categ_id = fields.Many2one(
        'product.category',
        string='Product Category',
        help='Leave empty to apply this rate to ALL product categories.\n'
             'A category-specific record always takes priority over a '
             'global (no-category) record on the same date.',
    )
    notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )

    @api.constrains('rate')
    def _check_rate_positive(self):
        for rec in self:
            if rec.rate <= 0:
                raise ValidationError(_('Pricing Based Cost rate must be greater than zero.'))

    @api.model
    def get_rate_for_product(self, product_id, ref_date=None):
        """
        Return the applicable rate (float) for a given product on ref_date.

        Priority:
          1. Most recent record with date <= ref_date AND categ_id = product.categ_id
          2. Most recent record with date <= ref_date AND categ_id = False (global)

        Returns 0.0 if no rate is found.
        """
        if not product_id:
            return 0.0

        product = self.env['product.product'].browse(product_id)
        if not product.exists():
            product = self.env['product.template'].browse(product_id)

        categ_id = product.categ_id.id if hasattr(product, 'categ_id') else False
        ref_date = ref_date or fields.Date.context_today(self)

        domain_base = [
            ('date', '<=', ref_date),
            ('active', '=', True),
            ('company_id', '=', self.env.company.id),
        ]

        # 1. Category-specific rate
        if categ_id:
            specific = self.search(
                domain_base + [('categ_id', '=', categ_id)],
                order='date desc, id desc',
                limit=1,
            )
            if specific:
                return specific.rate

        # 2. Global rate (no category)
        global_rate = self.search(
            domain_base + [('categ_id', '=', False)],
            order='date desc, id desc',
            limit=1,
        )
        return global_rate.rate if global_rate else 0.0

    @api.model
    def get_rate_record_for_product(self, product_id, ref_date=None):
        """
        Same as get_rate_for_product but returns the full record (or empty).
        Used to store the applied_cost_rate_id snapshot on SO lines.
        """
        if not product_id:
            return self.browse()

        product = self.env['product.product'].browse(product_id)
        categ_id = product.categ_id.id if product.exists() else False
        ref_date = ref_date or fields.Date.context_today(self)

        domain_base = [
            ('date', '<=', ref_date),
            ('active', '=', True),
            ('company_id', '=', self.env.company.id),
        ]

        if categ_id:
            specific = self.search(
                domain_base + [('categ_id', '=', categ_id)],
                order='date desc, id desc',
                limit=1,
            )
            if specific:
                return specific

        global_rate = self.search(
            domain_base + [('categ_id', '=', False)],
            order='date desc, id desc',
            limit=1,
        )
        return global_rate or self.browse()
