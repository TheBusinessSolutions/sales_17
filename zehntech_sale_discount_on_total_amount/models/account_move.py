from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo import _

class AccountMove(models.Model):
    _inherit = 'account.move'

    discount_type = fields.Selection([
        ('percent', 'Percentage'),
        ('amount', 'Fixed Amount')
    ], string="Discount Type", default='percent',
       help="Choose whether the discount is a percentage or a fixed amount.")

    discount_rate = fields.Float(string="Discount Rate",
                                 help="Set the discount value as percentage or amount depending on the discount type.")

    discount_amount = fields.Monetary(string="Discount Amount",
                                      compute='_compute_discount_amount', store=True,
                                      help="Total discount amount calculated based on the discount rate.")

    state = fields.Selection(
        selection_add=[('waiting_approval', 'Waiting for Discount Approval')],
        ondelete={'waiting_approval': 'set default'}
    )

    @api.depends('invoice_line_ids.price_subtotal', 'discount_type', 'discount_rate')
    def _compute_discount_amount(self):
        for move in self:
            if move.move_type not in ['out_invoice', 'out_refund']:
                move.discount_amount = 0
                continue

            untaxed = sum(line.price_subtotal for line in move.invoice_line_ids)

            if untaxed == 0 and move.discount_rate:
                move.discount_rate = 0
                raise UserError(_("Please select the product first before applying discount."))

            if not move.discount_type and move.discount_rate:
                move.discount_rate = 0
                raise UserError(_("Please first select the discount type."))

            if move.discount_rate < 0:
                raise UserError(_("Discount rate cannot be negative."))
            if move.discount_type == 'percent' and move.discount_rate > 100:
                raise UserError(_("The discount percentage cannot exceed the untaxed amount (100%)."))
            if move.discount_type == 'amount' and move.discount_rate > untaxed:
                raise UserError(_("The discount amount must not exceed the untaxed total."))

            if move.discount_type == 'percent':
                discount = (untaxed * move.discount_rate) / 100
            elif move.discount_type == 'amount':
                discount = move.discount_rate
            else:
                discount = 0.0

            move.discount_amount = discount

    
    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.balance',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.full_reconcile_id',
        'discount_amount'
    )
    def _compute_amount(self):
        """Compute all invoice amounts including proper discount and residuals"""
        for move in self:
            total_untaxed, total_tax, total, total_residual = 0.0, 0.0, 0.0, 0.0
            total_untaxed_currency, total_tax_currency, total_currency, total_residual_currency = 0.0, 0.0, 0.0, 0.0
            currencies = set()

            for line in move.line_ids:
                currencies.add(line.currency_id)
                if move.is_invoice(include_receipts=True):
                    if line.display_type == 'tax' or (line.display_type == 'rounding' and line.tax_repartition_line_id):
                        total_tax += line.balance
                        total_tax_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.display_type in ('product', 'rounding'):
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.display_type == 'payment_term':
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency

            sign = move.direction_sign

            move.amount_untaxed = sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed)
            move.amount_tax = sign * (total_tax_currency if len(currencies) == 1 else total_tax)

            if len(currencies) == 1:
                discounted_total_currency = total_currency + move.discount_amount 
                move.amount_total = sign * discounted_total_currency
            else:
                discounted_total = total + move.discount_amount
                move.amount_total = sign * discounted_total

            move.amount_residual = -sign * (total_residual_currency - move.discount_amount)
            move.amount_untaxed_signed = -total_untaxed
            move.amount_tax_signed = -total_tax

            move.amount_total_signed = abs(move.amount_total) if move.move_type == 'entry' else -move.amount_total
            move.amount_residual_signed = total_residual - move.discount_amount
            move.amount_total_in_currency_signed = abs(move.amount_total) if move.move_type == 'entry' else -(sign * move.amount_total)

            currency = (currencies.pop() if len(currencies) == 1 else move.company_id.currency_id)
            new_pmt_state = 'not_paid' if move.move_type != 'entry' else False

            if move.is_invoice(include_receipts=True) and move.state == 'posted':
                if currency.is_zero(move.amount_residual):
                    if all(p.is_matched for p in move._get_reconciled_payments()):
                        new_pmt_state = 'paid'
                    else:
                        new_pmt_state = move._get_invoice_in_payment_state()
                elif currency.compare_amounts(move.amount_total, abs(move.amount_residual)) != 0:
                    new_pmt_state = 'partial'

            if new_pmt_state == 'paid' and move.move_type in ('in_invoice', 'out_invoice', 'entry'):
                reverse_type = (
                    'in_refund' if move.move_type == 'in_invoice'
                    else 'out_refund' if move.move_type == 'out_invoice'
                    else 'entry'
                )
                reverse_moves = self.env['account.move'].search([
                    ('reversed_entry_id', '=', move.id),
                    ('state', '=', 'posted'),
                    ('move_type', '=', reverse_type)
                ])
                reverse_moves_full_recs = reverse_moves.mapped('line_ids.full_reconcile_id')
                if reverse_moves_full_recs.mapped('reconciled_line_ids.move_id').filtered(
                    lambda x: x not in (reverse_moves + reverse_moves_full_recs.mapped('exchange_move_id'))
                ) == move:
                    new_pmt_state = 'reversed'

            move.payment_state = new_pmt_state

    def action_post(self):
        config = self.env['ir.config_parameter'].sudo()
        approval_enabled = config.get_param("zehntech_sale_discount_on_total_amount.sale_discount_approval") == "True"
        limit = float(config.get_param("zehntech_sale_discount_on_total_amount.discount_limit_percentage", default="0.0"))

        for move in self:
            if self.env.context.get('bypass_discount_approval'):
                return super(AccountMove, move.with_context(bypass_discount_approval=False)).action_post()

            if (
                approval_enabled
                and move.discount_type == 'percent'
                and move.discount_rate > limit
                and move.state == 'draft'
            ):
                move.write({'state': 'waiting_approval'})
                return

        return super().action_post()

 
    def action_approve_discount(self):
        for move in self:
            if move.state == 'waiting_approval':
                move.write({'state': 'draft'})
                move.with_context(bypass_discount_approval=True).action_post()
                move.message_post(body=_("✅ Invoice discount approved successfully."))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Invoice discount approved successfully.'),
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            }
        }

    def action_reject_discount(self):
        for move in self:
            move.write({
                'discount_rate': 0,
                'discount_amount': 0,
                'state': 'draft'
            })

    def write(self, vals):
        for move in self:
            if move.state == 'posted':
                if 'discount_rate' in vals or 'discount_type' in vals:
                    raise UserError(_("You cannot modify discount after the Invoice is posted."))
        return super(AccountMove, self).write(vals)

    def create(self, vals):
        return super(AccountMove, self).create(vals)

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
