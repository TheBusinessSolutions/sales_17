from odoo import models, fields, api
from odoo.exceptions import AccessError, ValidationError
from odoo import _

class BulkDiscountUpdateWizard(models.TransientModel):
    _name = 'bulk.discount.update.wizard'
    _description = 'Bulk Discount Update Wizard'

    discount_type = fields.Selection([
        ('percent', 'Percentage'),
        ('amount', 'Fixed Amount')
    ], string="Discount Type", required=True, default='percent',
       help="Choose whether the discount is a percentage or a fixed amount.")

    discount_rate = fields.Float(string="Discount Rate", required=True,
        help="Set the discount value as percentage or amount depending on the discount type.")

    is_approval_manager = fields.Boolean(
        compute='_compute_is_approval_manager', store=False,
        help="Indicates whether the current user belongs to the Discount Approval Manager group."
    )

    @api.depends()
    def _compute_is_approval_manager(self):
        group = self.env.ref('zehntech_sale_discount_on_total_amount.group_discount_approval_manager')
        for wizard in self:
            wizard.is_approval_manager = group in self.env.user.groups_id

    @api.constrains('discount_rate')
    def _check_discount_rate_limits(self):
        for wizard in self:
            if wizard.discount_rate < 0.0:
                raise ValidationError(_("Discount Rate cannot be negative."))

            if wizard.discount_type == 'percent' and wizard.discount_rate > 100.0:
                raise ValidationError(_("Percentage discount cannot exceed 100%."))

            active_model = self.env.context.get('active_model')
            active_ids = self.env.context.get('active_ids', [])
            records = self.env[active_model].browse(active_ids)

            for rec in records:
                untaxed_amt = 0.0
                if active_model == 'sale.order':
                    untaxed_amt = rec.amount_untaxed
                elif active_model == 'account.move' and rec.move_type in ('out_invoice', 'out_refund'):
                    untaxed_amt = rec.amount_untaxed

                if wizard.discount_type == 'amount' and wizard.discount_rate > untaxed_amt:
                    raise ValidationError(_("For some records discount amount exceeding the untaxed amount, Please check"))

    @api.onchange('discount_rate')
    def _onchange_discount_rate_non_negative(self):
        for wizard in self:
            if wizard.discount_rate < 0.0:
                wizard.discount_rate = 0.0
                return {
                    'warning': {
                        'title': "Invalid Discount",
                        'message': _("Discount Rate cannot be negative. It has been reset to 0."),
                        'type': 'warning',
                    }
                }

    def apply_bulk_discount(self):
        group = self.env.ref('zehntech_sale_discount_on_total_amount.group_discount_approval_manager')
        if group not in self.env.user.groups_id:
            raise AccessError(_("Only Discount Approval Managers can apply bulk discounts."))

        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids', [])
        records = self.env[active_model].browse(active_ids)

        param = self.env['ir.config_parameter'].sudo()
        limit = float(param.get_param('zehntech_sale_discount_on_total_amount.discount_limit', default=0.0))

        for rec in records:
            rec.write({
                'discount_type': self.discount_type,
                'discount_rate': self.discount_rate
            })

            is_over_limit = self.discount_type == 'percent' and self.discount_rate > limit

            if active_model == 'sale.order':
                if is_over_limit:
                    rec.state = 'waiting_approval'
                elif rec.state == 'waiting_approval' and not is_over_limit:
                    rec.state = 'draft'

            elif active_model == 'account.move':
                if rec.move_type not in ('out_invoice', 'out_refund'):
                    continue
                if is_over_limit:
                    rec.state = 'waiting_approval'
                elif rec.state == 'waiting_approval' and not is_over_limit:
                    rec.state = 'draft'

        return {'type': 'ir.actions.act_window_close'}
