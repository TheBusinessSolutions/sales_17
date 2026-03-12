# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductAreaCost(models.Model):
    """
    Pricing Based Cost Rate Table.

    When a new rate is saved, all products with use_area_pricing=True
    get their lst_price updated as: default_width x default_height x rate.

    Odoo's standard pricelist engine then runs on lst_price normally —
    discounts, fixed prices, qty breaks all work out of the box.
    """
    _name = 'product.area.cost'
    _description = 'Pricing Based Cost Rate'
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        help='e.g. "March 2025 Rate Increase"',
    )
    date = fields.Date(
        string='Effective Date',
        required=True,
        default=fields.Date.context_today,
    )
    rate = fields.Float(
        string='Pricing Based Cost (per m²)',
        required=True,
        digits=(16, 4),
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
        help='Leave empty to apply to ALL categories. '
             'A category-specific record takes priority over a global one.',
    )
    notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )
    updated_product_count = fields.Integer(
        string='Products Updated',
        readonly=True,
        default=0,
        help='Number of products whose Sales Price was updated when this rate was saved.',
    )

    @api.constrains('rate')
    def _check_rate_positive(self):
        for rec in self:
            if rec.rate <= 0:
                raise ValidationError(_('Pricing Based Cost rate must be greater than zero.'))

    def write(self, vals):
        res = super().write(vals)
        if 'rate' in vals or 'categ_id' in vals:
            for rec in self:
                rec._update_product_prices()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._update_product_prices()
        return records

    def _update_product_prices(self):
        """
        Update lst_price for all products with use_area_pricing = True
        that match this rate's category scope.

        Price = default_width x default_height x self.rate

        Products with no default dimensions set are skipped (price would be 0).
        """
        self.ensure_one()

        domain = [('use_area_pricing', '=', True)]

        # Category scope: if this rate has a category, only update that category
        # If global (no category), update ALL area-priced products
        if self.categ_id:
            domain.append(('categ_id', 'child_of', self.categ_id.id))

        products = self.env['product.template'].search(domain)

        count = 0
        for product in products:
            if product.default_width > 0 and product.default_height > 0:
                new_price = product.default_width * product.default_height * self.rate
                product.list_price = new_price
                count += 1

        self.updated_product_count = count

    def action_preview_update(self):
        """
        Show a preview of which products will be updated and their new prices,
        without actually saving. Useful before committing a rate change.
        """
        self.ensure_one()
        domain = [('use_area_pricing', '=', True)]
        if self.categ_id:
            domain.append(('categ_id', 'child_of', self.categ_id.id))

        products = self.env['product.template'].search(domain)
        lines = []
        for p in products:
            if p.default_width > 0 and p.default_height > 0:
                new_price = p.default_width * p.default_height * self.rate
                lines.append(
                    f"  • {p.name}: {p.default_width} x {p.default_height} x "
                    f"{self.rate} = {new_price:.2f}"
                )

        msg = _('%d product(s) will be updated:\n\n%s') % (
            len(lines), '\n'.join(lines) if lines else _('None')
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Preview: Products to be Updated'),
                'message': msg,
                'sticky': True,
                'type': 'info',
            },
        }

    @api.model
    def get_rate_for_product(self, product_id, ref_date=None):
        """
        Return the applicable rate (float) for a given product on ref_date.
        Used for snapshotting the rate on SO lines at the time of order creation.

        Priority:
          1. Most recent record with date <= ref_date AND categ matches product
          2. Most recent record with date <= ref_date AND categ = False (global)
        """
        if not product_id:
            return 0.0

        product = self.env['product.template'].browse(product_id)
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
                return specific.rate

        global_rate = self.search(
            domain_base + [('categ_id', '=', False)],
            order='date desc, id desc',
            limit=1,
        )
        return global_rate.rate if global_rate else 0.0