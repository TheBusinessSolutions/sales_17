from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo import _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    discount_type = fields.Selection([
        ('percent', 'Percentage'),
        ('amount', 'Fixed Amount')
    ], string="Discount Type", default='percent', store=True,
       help="Choose whether the discount is a percentage or a fixed amount.")

    discount_rate = fields.Float(string="Discount Rate",store=True,
                                 help="Enter the discount value. Interpreted as percentage or fixed amount based on the selected type.")

    discount_amount = fields.Monetary(string="Discount Amount",
                                      compute='_compute_amount_all', store=True,
                                      help="Calculated discount value applied to this order.")

    terms_conditions = fields.Text(string="Terms and conditions",
                                   help="Add any terms or conditions related to this order.")

    state = fields.Selection(selection_add=[('waiting_approval', 'Waiting for Discount Approval')])

    can_approve_discount = fields.Boolean(compute='_compute_can_approve_discount',
                                          help="Indicates whether the current user can approve discounts.")

    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_compute_amount_all',
                                     help="Total amount without taxes.")

    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_compute_amount_all',
                                 help="Total tax amount for the order.")

    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_compute_amount_all',
                                   help="Total amount including discount and taxes.")

    def _compute_can_approve_discount(self):
        user = self.env.user
        is_manager = user.has_group('zehntech_sale_discount_on_total_amount.group_discount_approval_manager')
        for order in self:
            order.can_approve_discount = is_manager

    @api.depends('order_line.price_subtotal', 'order_line.price_tax', 'discount_type', 'discount_rate')
    def _compute_amount_all(self):
        for order in self:
            amount_untaxed = sum(line.price_subtotal for line in order.order_line)
            amount_tax = sum(line.price_tax for line in order.order_line)

            if amount_untaxed == 0 and order.discount_rate:
                order.discount_rate = 0
                raise UserError(_("Please select the product first before applying discount."))
            if not order.discount_type and order.discount_rate:
                order.discount_rate = 0
                raise UserError(_("Please first select the discount type."))
            if order.discount_rate < 0:
                raise UserError(_("Discount rate cannot be negative."))
            if order.discount_type == 'percent' and order.discount_rate > 100:
                raise UserError(_("The discount percentage cannot exceed the untaxed amount (100%)."))
            if order.discount_type == 'amount' and order.discount_rate > amount_untaxed:
                raise UserError(_("The discount amount must not exceed the untaxed total."))

            if order.discount_type == 'percent':
                discount = (amount_untaxed * order.discount_rate) / 100
            elif order.discount_type == 'amount':
                discount = order.discount_rate
            else:
                discount = 0.0

            currency = order.currency_id or order.company_id.currency_id
            order.update({
                'amount_untaxed': currency.round(amount_untaxed),
                'amount_tax': currency.round(amount_tax),
                'discount_amount': currency.round(discount),
                'amount_total': currency.round(amount_untaxed + amount_tax - discount),
            })

    def action_confirm(self):
        config = self.env['ir.config_parameter'].sudo()
        approval_enabled = config.get_param("zehntech_sale_discount_on_total_amount.sale_discount_approval") == "True"
        limit = float(config.get_param("zehntech_sale_discount_on_total_amount.discount_limit_percentage", default="0.0"))

        orders_to_confirm = self.browse()
        for order in self:
            if (
                approval_enabled
                and order.discount_type == 'percent'
                and order.discount_rate > limit
            ):
                order.state = 'waiting_approval'
            else:
                orders_to_confirm |= order

        return super(SaleOrder, orders_to_confirm).action_confirm() if orders_to_confirm else True

    def action_approve_discount(self):
        for order in self:
            if order.state == 'waiting_approval':
                order.state = 'sale'
                order.message_post(body=_("✅ Discount approved successfully."))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Discount approved successfully.'),
                'type': 'success',
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            }
        }



    def action_reject_discount(self):
        for order in self:
            order.write({
                'discount_rate': 0,
                'discount_amount': 0,
                'state': 'draft'
            })

    def action_open_bulk_discount_approval_wizard(self):
        return {
            'name': _('Bulk Discount Approval'),
            'type': 'ir.actions.act_window',
            'res_model': 'bulk.discount.approval.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': self._name,
                'active_ids': self.env.context.get('active_ids'),
            }
        }

    def action_open_bulk_discount_update_wizard(self):
        return {
            'name': _('Bulk Discount Update'),
            'type': 'ir.actions.act_window',
            'res_model': 'bulk.discount.update.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': self._name,
                'active_ids': self.env.context.get('active_ids'),
            }
        }

            
    def write(self, vals):
        for order in self:
            if order.state in ['sale', 'done']:
                if 'discount_rate' in vals or 'discount_type' in vals:
                    raise UserError(_("You cannot modify discount once the Sale Order is confirmed."))
        return super(SaleOrder, self).write(vals)

    def create(self, vals):
        return super(SaleOrder, self).create(vals)
