from odoo import models, fields

class DiscountAnalytics(models.Model):
    _name = 'discount.analytics'
    _description = 'Discount Analytics'
    _auto = False

    user_id = fields.Many2one(
        'res.users',
        string='User',
        help="The user who has been assigned or associated with the discount approvals.")

    total_discount = fields.Monetary(
        string='Total Discount',
        help="The total discount amount given by the user on all sale orders or invoices.")

    invoice_count = fields.Integer(
        string='Invoices',
        help="The total number of invoices where the user has applied discounts.")

    order_count = fields.Integer(
        string='Sale Orders',
        help="The total number of sale orders where the user has applied discounts.")

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        help="The currency in which the total discount amount is calculated.")


    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW discount_analytics AS (
                SELECT
                    MIN(so.id) AS id,
                    so.user_id,
                    SUM(so.discount_amount) AS total_discount,
                    COUNT(so.id) FILTER (WHERE so.state IN ('sale', 'done')) AS order_count,
                    0 AS invoice_count,
                    c.id AS currency_id
                FROM sale_order so
                LEFT JOIN res_currency c ON so.currency_id = c.id
                GROUP BY so.user_id, c.id

                UNION ALL

                SELECT
                    -MIN(am.id) AS id,
                    am.invoice_user_id AS user_id,
                    SUM(am.discount_amount),
                    0,
                    COUNT(am.id) FILTER (WHERE am.state = 'posted'),
                    c.id
                FROM account_move am
                LEFT JOIN res_currency c ON am.currency_id = c.id
                WHERE am.move_type IN ('out_invoice', 'out_refund')
                GROUP BY am.invoice_user_id, c.id
            );
        """)
