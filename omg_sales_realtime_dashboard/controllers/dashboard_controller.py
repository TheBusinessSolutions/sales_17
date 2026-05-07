# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class OMGSalesRealtimeDashboardController(http.Controller):

    @http.route('/omg_sales_realtime_dashboard/options', type='json', auth='user')
    def omg_sales_realtime_dashboard_options(self):
        return request.env['omg.sales.realtime.dashboard.service'].get_filter_options()

    @http.route('/omg_sales_realtime_dashboard/data', type='json', auth='user')
    def omg_sales_realtime_dashboard_data(self, filters=None):
        return request.env['omg.sales.realtime.dashboard.service'].get_dashboard_payload(filters or {})
