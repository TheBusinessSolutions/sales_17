# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductAreaCost(models.Model):
    _name = 'product.area.cost'
    _description = 'Pricing Based Cost Rate'
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', required=True)
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
        help='Leave empty to apply to ALL categories.',
    )
    notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('applied', 'Applied'),
    ], string='Status', default='draft', readonly=True, copy=False)

    affected_line_ids = fields.One2many(
        'product.area.cost.line',
        'cost_rate_id',
        string='Affected Products',
        readonly=True,
    )
    updated_product_count = fields.Integer(
        string='Products Updated',
        compute='_compute_updated_product_count',
    )

    # ── Validation: no duplicate date per category per company ────────────────
    _sql_constraints = [
        (
            'unique_date_categ_company',
            'UNIQUE(date, categ_id, company_id)',
            'A Pricing Based Cost rate already exists for this date and category. '
            'Please use a different date or archive the existing record first.',
        ),
    ]

    @api.constrains('rate')
    def _check_rate_positive(self):
        for rec in self:
            if rec.rate <= 0:
                raise ValidationError(_('Pricing Based Cost rate must be greater than zero.'))

    @api.constrains('state')
    def _check_one_applied_per_date_categ(self):
        for rec in self:
            if rec.state == 'applied':
                duplicate = self.search([
                    ('id', '!=', rec.id),
                    ('date', '=', rec.date),
                    ('categ_id', '=', rec.categ_id.id if rec.categ_id else False),
                    ('company_id', '=', rec.company_id.id),
                    ('state', '=', 'applied'),
                ])
                if duplicate:
                    raise ValidationError(_(
                        'An applied rate already exists for this date and category: %s. '
                        'Please archive it before applying a new one.'
                    ) % duplicate[0].name)

    @api.depends('affected_line_ids')
    def _compute_updated_product_count(self):
        for rec in self:
            rec.updated_product_count = len(rec.affected_line_ids)

    def action_apply_rate(self):
        """
        Manually apply this rate: update product list_price and mark as applied.
        Only Sale Administrators can execute this.
        """
        self.ensure_one()
        if self.state == 'applied':
            raise ValidationError(_('This rate has already been applied.'))
        self._update_product_prices()
        self.state = 'applied'

    def action_reset_to_draft(self):
        """Reset to draft so it can be edited. Does NOT revert product prices."""
        self.ensure_one()
        self.state = 'draft'

    def _update_product_prices(self):
        self.ensure_one()

        domain = [('use_area_pricing', '=', True)]
        if self.categ_id:
            domain.append(('categ_id', 'child_of', self.categ_id.id))

        products = self.env['product.template'].search(domain)

        # Clear previous snapshot
        self.affected_line_ids.unlink()

        lines_to_create = []
        for product in products:
            if product.default_width > 0 and product.default_height > 0:
                price_before = product.list_price
                new_price = product.default_width * product.default_height * self.rate
                product.standard_price = new_price
                lines_to_create.append({
                    'cost_rate_id': self.id,
                    'product_id': product.id,
                    'price_before': price_before,
                    'price_after': new_price,
                })

        if lines_to_create:
            self.env['product.area.cost.line'].create(lines_to_create)

    def action_view_affected_products(self):
        self.ensure_one()
        return {
            'name': _('Affected Products – %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.area.cost.line',
            'view_mode': 'tree',
            'domain': [('cost_rate_id', '=', self.id)],
            'context': {'default_cost_rate_id': self.id},
        }

    @api.model
    def get_rate_for_product(self, product_id, ref_date=None):
        if not product_id:
            return 0.0
        product = self.env['product.template'].browse(product_id)
        categ_id = product.categ_id.id if product.exists() else False
        ref_date = ref_date or fields.Date.context_today(self)
        domain_base = [
            ('date', '<=', ref_date),
            ('active', '=', True),
            ('state', '=', 'applied'),
            ('company_id', '=', self.env.company.id),
        ]
        if categ_id:
            specific = self.search(
                domain_base + [('categ_id', '=', categ_id)],
                order='date desc, id desc', limit=1,
            )
            if specific:
                return specific.rate
        global_rate = self.search(
            domain_base + [('categ_id', '=', False)],
            order='date desc, id desc', limit=1,
        )
        return global_rate.rate if global_rate else 0.0

    @api.model
    def get_current_rate_record(self, categ_id=False):
        """Return the most recently applied rate record (for SO display)."""
        domain = [
            ('active', '=', True),
            ('state', '=', 'applied'),
            ('company_id', '=', self.env.company.id),
        ]
        if categ_id:
            rec = self.search(
                domain + [('categ_id', '=', categ_id)],
                order='date desc, id desc', limit=1,
            )
            if rec:
                return rec
        return self.search(
            domain + [('categ_id', '=', False)],
            order='date desc, id desc', limit=1,
        )


class ProductAreaCostLine(models.Model):
    _name = 'product.area.cost.line'
    _description = 'Pricing Based Cost – Affected Product'
    _order = 'product_id asc'

    cost_rate_id = fields.Many2one(
        'product.area.cost', string='Cost Rate',
        required=True, ondelete='cascade',
    )
    product_id = fields.Many2one(
        'product.template', string='Product',
        required=True, readonly=True,
    )
    price_before = fields.Float(
        string='Price Before', digits=(16, 2), readonly=True,
    )
    price_after = fields.Float(
        string='New Price', digits=(16, 2), readonly=True,
    )
    price_diff = fields.Float(
        string='Difference', digits=(16, 2),
        compute='_compute_price_diff', store=True,
    )
    currency_id = fields.Many2one(
        related='cost_rate_id.currency_id', store=True, readonly=True,
    )

    @api.depends('price_before', 'price_after')
    def _compute_price_diff(self):
        for line in self:
            line.price_diff = line.price_after - line.price_before
