# -*- coding: utf-8 -*-
##############################################################################
#
#    iWesabe.
#    Copyright (C) 2018-TODAY iWesabe (<https://www.iwesabe.com>).
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Sales Dynamic Approval",
    'summary': """Sales Dynamic Approval Based on Sales Team""",
    'description': """
        Sale order can confirm based on configured approver in sales team.
    """,
    'author': "iWesabe",
    'website': "https://www.iwesabe.com/",
    'license': 'AGPL-3',
    'category': 'Sales/Approvers',
    'version': '17.0.1.0',

    'depends': ['sale','sales_team'],

    'data': [
        'security/ir.model.access.csv',
        'views/crm_team_view.xml',
        'views/sale_view.xml',
    ],
    'images': ['static/description/banner.png'],

    'demo': [],

    'installable': True,
    'application': True,
    'auto_install': False,
    
}
