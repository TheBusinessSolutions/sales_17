from odoo import models

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _compute_amount(self):
        for wizard in self:
            invoices = wizard.line_ids.mapped('move_id')
            if invoices:
                wizard.amount = abs(sum(invoices.mapped('amount_residual')))
            else:
                wizard.amount = 0.0
