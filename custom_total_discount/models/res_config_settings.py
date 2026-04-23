# -*- coding: utf-8 -*-
##############################################################################
#
#    Mohamed Hussein.
#    Copyright (C) 2024 Mohamed Hussein (<https://www.linkedin.com/in/muhmmdhussein/>).
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL-3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software without permission.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL-3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    discount_application = fields.Selection(
        [('before_tax', 'Before Tax'), ('after_tax', 'After Tax')],
        string='Discount Application',
        config_parameter='invoice_sales_custom_discount.discount_application',
        default='before_tax',
        help="Choose whether the additional discount is applied before or after tax."
    )




