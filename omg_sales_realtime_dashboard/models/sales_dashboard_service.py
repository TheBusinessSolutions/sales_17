# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo Man
#
##############################################################################

from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class OMGSalesRealtimeDashboardService(models.AbstractModel):
    _name = 'omg.sales.realtime.dashboard.service'
    _description = 'Odoo Man Sales Realtime Dashboard Service'

    _TOP_LIMIT = 10

    @api.model
    def get_filter_options(self):
        user = self.env.user
        is_manager = user.has_group('sales_team.group_sale_manager')
        team_domain = []
        user_domain = [('share', '=', False), ('active', '=', True)]
        if not is_manager:
            team_domain = ['|', ('user_id', '=', user.id), ('member_ids', 'in', [user.id])]
            user_domain.append(('id', '=', user.id))

        currency = self.env.company.currency_id
        return {
            'teams': [{'id': rec.id, 'name': rec.name} for rec in self.env['crm.team'].search(team_domain, limit=80, order='name asc')],
            'products': [{'id': rec.id, 'name': rec.display_name} for rec in self.env['product.product'].search([('sale_ok', '=', True), ('active', '=', True)], limit=250, order='name asc')],
            'partners': [{'id': rec.id, 'name': rec.display_name} for rec in self.env['res.partner'].search([('customer_rank', '>', 0), ('active', '=', True)], limit=250, order='name asc')],
            'salespeople': [{'id': rec.id, 'name': rec.name} for rec in self.env['res.users'].search(user_domain, limit=80, order='name asc')],
            'currency': {'symbol': currency.symbol, 'position': currency.position, 'name': currency.name},
            'refresh_intervals': [0, 15000, 30000, 60000, 300000],
            'date_presets': [
                {'key': 'today', 'label': 'Today'},
                {'key': 'this_week', 'label': 'This Week'},
                {'key': 'this_month', 'label': 'This Month'},
                {'key': 'this_quarter', 'label': 'This Quarter'},
                {'key': 'this_year', 'label': 'This Year'},
            ],
            'is_manager': is_manager,
            'can_manage_targets': is_manager,
        }

    @api.model
    def get_dashboard_payload(self, filters=None):
        filters = self._normalize_filters(filters)
        current_range = self._get_period_range(filters['date_from'], filters['date_to'])
        previous_range = self._get_previous_period(current_range)
        current = self._compute_period_bundle(filters, current_range)
        previous = self._compute_period_bundle(filters, previous_range)
        currency = self.env.company.currency_id
        return {
            'filters': filters,
            'currency': {'symbol': currency.symbol, 'position': currency.position, 'name': currency.name},
            'access': {'is_manager': self._is_manager()},
            'kpis': current['kpis'],
            'comparison_cards': self._build_comparison_cards(current, previous),
            'charts': current['charts'],
            'targets': current['targets'],
            'profitability': current['profitability'],
            'alerts': current['alerts'],
            'pivot_summary': current['pivot_summary'],
            'orders': current['orders'],
            'meta': {
                'generated_at': fields.Datetime.now(),
                'current_label': '%s → %s' % (filters['date_from'], filters['date_to']),
                'previous_label': '%s → %s' % (previous_range['date_from'], previous_range['date_to']),
                'days': current_range['days'],
                'refresh_interval_ms': filters['refresh_interval_ms'],
            },
        }

    @api.model
    def _normalize_filters(self, filters=None):
        filters = dict(filters or {})
        today = fields.Date.context_today(self)
        start = today - relativedelta(days=29)

        def _clean_ids(values):
            cleaned = []
            for value in values or []:
                try:
                    cleaned.append(int(value))
                except (TypeError, ValueError):
                    continue
            return cleaned

        date_from = filters.get('date_from') or fields.Date.to_string(start)
        date_to = filters.get('date_to') or fields.Date.to_string(today)
        if date_from > date_to:
            date_from, date_to = date_to, date_from

        try:
            refresh_interval_ms = int(filters.get('refresh_interval_ms') or 0)
        except (TypeError, ValueError):
            refresh_interval_ms = 0
        if refresh_interval_ms not in [0, 15000, 30000, 60000, 300000]:
            refresh_interval_ms = 0

        return {
            'date_from': date_from,
            'date_to': date_to,
            'team_ids': _clean_ids(filters.get('team_ids')),
            'product_ids': _clean_ids(filters.get('product_ids')),
            'partner_ids': _clean_ids(filters.get('partner_ids')),
            'user_ids': _clean_ids(filters.get('user_ids')),
            'company_ids': self.env.companies.ids or [self.env.company.id],
            'refresh_interval_ms': refresh_interval_ms,
            'group_by': filters.get('group_by') or 'none',
        }

    @api.model
    def _get_period_range(self, date_from, date_to):
        start = fields.Date.to_date(date_from)
        end = fields.Date.to_date(date_to)
        return {'date_from': fields.Date.to_string(start), 'date_to': fields.Date.to_string(end), 'days': (end - start).days + 1}

    @api.model
    def _get_previous_period(self, current_range):
        start = fields.Date.to_date(current_range['date_from'])
        days = current_range['days']
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days - 1)
        return {'date_from': fields.Date.to_string(prev_start), 'date_to': fields.Date.to_string(prev_end), 'days': days}

    @api.model
    def _compute_period_bundle(self, filters, period_range):
        period_filters = dict(filters)
        period_filters['date_from'] = period_range['date_from']
        period_filters['date_to'] = period_range['date_to']
        metrics = self._compute_core_metrics(period_filters)
        charts = {
            'daily_revenue': self._get_daily_revenue(period_filters),
            'daily_orders': self._get_daily_orders(period_filters),
            'monthly_revenue': self._get_monthly_revenue(period_filters),
            'average_order_trend': self._get_average_order_trend(period_filters),
            'quotation_funnel': self._get_quotation_funnel(metrics),
            'state_distribution': self._get_state_distribution(period_filters),
            'team_performance': self._get_team_performance(period_filters),
            'salesperson_performance': self._get_salesperson_performance(period_filters),
            'top_customers': self._get_top_customers(period_filters),
            'top_products': self._get_top_products(period_filters),
            'top_categories': self._get_top_categories(period_filters),
            'weekday_heatmap': self._get_weekday_heatmap(period_filters),
        }
        targets = self._get_target_progress(period_filters, metrics)
        profitability = self._get_profitability(period_filters)
        return {
            'kpis': self._build_kpis(metrics, targets, profitability),
            'charts': charts,
            'targets': targets,
            'profitability': profitability,
            'alerts': self._get_alerts(metrics, profitability, targets),
            'pivot_summary': self._get_pivot_summary(period_filters),
            'orders': self._get_orders(period_filters),
        }

    @api.model
    def _is_manager(self):
        return self.env.user.has_group('sales_team.group_sale_manager')

    @api.model
    def _is_product_filtered(self, filters):
        return bool(filters.get('product_ids'))

    @api.model
    def _build_order_where(self, filters, states=None):
        clauses = ['so.company_id = ANY(%s)', 'so.date_order >= %s', 'so.date_order <= %s']
        params = [filters['company_ids'], '%s 00:00:00' % filters['date_from'], '%s 23:59:59' % filters['date_to']]
        if not self._is_manager():
            clauses.append('(so.user_id = %s OR so.create_uid = %s)')
            params.extend([self.env.user.id, self.env.user.id])
        if filters.get('team_ids'):
            clauses.append('so.team_id = ANY(%s)')
            params.append(filters['team_ids'])
        if filters.get('partner_ids'):
            clauses.append('so.partner_id = ANY(%s)')
            params.append(filters['partner_ids'])
        if filters.get('user_ids'):
            clauses.append('so.user_id = ANY(%s)')
            params.append(filters['user_ids'])
        if states:
            clauses.append('so.state = ANY(%s)')
            params.append(states)
        return clauses, params

    @api.model
    def _build_line_where(self, filters, states=None):
        clauses, params = self._build_order_where(filters, states=states)
        clauses.extend(['sol.display_type IS NULL', 'sol.order_id = so.id'])
        if filters.get('product_ids'):
            clauses.append('sol.product_id = ANY(%s)')
            params.append(filters['product_ids'])
        return clauses, params

    @api.model
    def _fetchall_dict(self, query, params):
        self.env.cr.execute(query, params)
        columns = [col[0] for col in self.env.cr.description]
        return [dict(zip(columns, row)) for row in self.env.cr.fetchall()]

    @api.model
    def _scalar(self, query, params):
        self.env.cr.execute(query, params)
        row = self.env.cr.fetchone()
        return row[0] if row and row[0] is not None else 0.0

    @api.model
    def _column_is_json(self, table_name, column_name):
        self.env.cr.execute(
            """
                SELECT udt_name
                  FROM information_schema.columns
                 WHERE table_name = %s
                   AND column_name = %s
                 LIMIT 1
            """,
            [table_name, column_name],
        )
        row = self.env.cr.fetchone()
        return bool(row and row[0] in ('json', 'jsonb'))

    @api.model
    def _translated_label_expr(self, table_name, column_name, column_sql, fallback):
        fallback = (fallback or '').replace("'", "''")
        if self._column_is_json(table_name, column_name):
            lang = (self.env.lang or 'en_US').replace("'", "''")
            return "COALESCE(NULLIF(%s->>'%s', ''), NULLIF(%s->>'en_US', ''), '%s')" % (column_sql, lang, column_sql, fallback)
        return "COALESCE(NULLIF(%s, ''), '%s')" % (column_sql, fallback)

    @api.model
    def _json_name_expr(self, column_sql, fallback, table_name=None, column_name='name'):
        if table_name:
            return self._translated_label_expr(table_name, column_name, column_sql, fallback)
        lang = (self.env.lang or 'en_US').replace("'", "''")
        fallback = (fallback or '').replace("'", "''")
        return "COALESCE(NULLIF(%s->>'%s', ''), NULLIF(%s->>'en_US', ''), '%s')" % (column_sql, lang, column_sql, fallback)

    @api.model
    def _partner_name_expr(self, column_sql='partner.name', fallback='No Customer'):
        fallback = (fallback or '').replace("'", "''")
        return "COALESCE(NULLIF(%s, ''), '%s')" % (column_sql, fallback)

    @api.model
    def _compute_core_metrics(self, filters):
        confirmed_states = ['sale', 'done']
        quotation_states = ['draft', 'sent']
        all_states = ['draft', 'sent', 'sale', 'done', 'cancel']
        if self._is_product_filtered(filters):
            confirmed_where, confirmed_params = self._build_line_where(filters, confirmed_states)
            quotation_where, quotation_params = self._build_line_where(filters, quotation_states)
            confirmed_from = 'sale_order so JOIN sale_order_line sol ON sol.order_id = so.id'
            quotation_from = confirmed_from
            amount_confirmed = 'COALESCE(SUM(sol.price_total), 0.0)'
            amount_quotation = 'COALESCE(SUM(sol.price_total), 0.0)'
            count_expr = 'COUNT(DISTINCT so.id)'
        else:
            confirmed_where, confirmed_params = self._build_order_where(filters, confirmed_states)
            quotation_where, quotation_params = self._build_order_where(filters, quotation_states)
            confirmed_from = 'sale_order so'
            quotation_from = 'sale_order so'
            amount_confirmed = 'COALESCE(SUM(so.amount_total), 0.0)'
            amount_quotation = 'COALESCE(SUM(so.amount_total), 0.0)'
            count_expr = 'COUNT(so.id)'

        confirmed_revenue = self._scalar('SELECT %s FROM %s WHERE %s' % (amount_confirmed, confirmed_from, ' AND '.join(confirmed_where)), confirmed_params)
        quotation_revenue = self._scalar('SELECT %s FROM %s WHERE %s' % (amount_quotation, quotation_from, ' AND '.join(quotation_where)), quotation_params)
        confirmed_orders = self._scalar('SELECT %s FROM %s WHERE %s' % (count_expr, confirmed_from, ' AND '.join(confirmed_where)), confirmed_params)
        quotation_orders = self._scalar('SELECT %s FROM %s WHERE %s' % (count_expr, quotation_from, ' AND '.join(quotation_where)), quotation_params)
        all_where, all_params = self._build_order_where(filters, all_states)
        all_orders = self._scalar('SELECT COUNT(so.id) FROM sale_order so WHERE %s' % ' AND '.join(all_where), all_params)
        average_order_value = confirmed_revenue / confirmed_orders if confirmed_orders else 0.0
        win_rate = (confirmed_orders / (confirmed_orders + quotation_orders) * 100.0) if (confirmed_orders + quotation_orders) else 0.0
        return {
            'confirmed_revenue': float(confirmed_revenue or 0.0),
            'quotation_revenue': float(quotation_revenue or 0.0),
            'confirmed_orders': int(confirmed_orders or 0),
            'quotation_orders': int(quotation_orders or 0),
            'all_orders': int(all_orders or 0),
            'average_order_value': float(average_order_value or 0.0),
            'win_rate': float(win_rate or 0.0),
        }

    @api.model
    def _build_kpis(self, metrics, targets, profitability):
        return [
            {'key': 'confirmed_revenue', 'label': 'Confirmed Revenue', 'value': metrics['confirmed_revenue'], 'type': 'currency'},
            {'key': 'quotation_revenue', 'label': 'Quotation Pipeline', 'value': metrics['quotation_revenue'], 'type': 'currency'},
            {'key': 'confirmed_orders', 'label': 'Confirmed Orders', 'value': metrics['confirmed_orders'], 'type': 'number'},
            {'key': 'average_order_value', 'label': 'Average Order Value', 'value': metrics['average_order_value'], 'type': 'currency'},
            {'key': 'win_rate', 'label': 'Win Rate', 'value': metrics['win_rate'], 'type': 'percentage'},
            {'key': 'target_achievement', 'label': 'Target Achievement', 'value': targets.get('overall_achievement', 0.0), 'secondary_value': targets.get('overall_target_amount', 0.0), 'type': 'percentage'},
            {'key': 'approx_margin', 'label': 'Approx. Margin', 'value': profitability.get('margin_amount', 0.0), 'type': 'currency'},
            {'key': 'approx_margin_rate', 'label': 'Approx. Margin Rate', 'value': profitability.get('margin_rate', 0.0), 'type': 'percentage'},
        ]

    @api.model
    def _build_comparison_cards(self, current, previous):
        current_map = {item['key']: item for item in current['kpis']}
        previous_map = {item['key']: item for item in previous['kpis']}
        result = []
        for key in ['confirmed_revenue', 'confirmed_orders', 'average_order_value', 'win_rate', 'approx_margin_rate', 'target_achievement']:
            cur = current_map.get(key, {})
            prev = previous_map.get(key, {})
            cur_val = cur.get('value', 0.0)
            prev_val = prev.get('value', 0.0)
            diff = cur_val - prev_val
            pct = (diff / prev_val * 100.0) if prev_val else (100.0 if cur_val else 0.0)
            result.append({'key': key, 'label': cur.get('label', key), 'current_value': cur_val, 'previous_value': prev_val, 'difference': diff, 'difference_pct': pct, 'type': cur.get('type', 'number')})
        return result

    @api.model
    def _complete_daily_series(self, filters, row_map, int_values=False):
        result = []
        current = fields.Date.to_date(filters['date_from'])
        end = fields.Date.to_date(filters['date_to'])
        while current <= end:
            key = fields.Date.to_string(current)
            row = row_map.get(key, {})
            value = int(row.get('value') or 0) if int_values else float(row.get('value') or 0.0)
            result.append({'date': key, 'label': current.strftime('%d %b'), 'value': value})
            current += timedelta(days=1)
        return result

    @api.model
    def _get_daily_revenue(self, filters):
        if self._is_product_filtered(filters):
            where, params = self._build_line_where(filters, ['sale', 'done'])
            query = "SELECT TO_CHAR(DATE(so.date_order), 'YYYY-MM-DD') AS date, COALESCE(SUM(sol.price_total), 0.0) AS value FROM sale_order so JOIN sale_order_line sol ON sol.order_id = so.id WHERE %s GROUP BY DATE(so.date_order) ORDER BY DATE(so.date_order)" % ' AND '.join(where)
        else:
            where, params = self._build_order_where(filters, ['sale', 'done'])
            query = "SELECT TO_CHAR(DATE(so.date_order), 'YYYY-MM-DD') AS date, COALESCE(SUM(so.amount_total), 0.0) AS value FROM sale_order so WHERE %s GROUP BY DATE(so.date_order) ORDER BY DATE(so.date_order)" % ' AND '.join(where)
        rows = {row['date']: row for row in self._fetchall_dict(query, params)}
        return self._complete_daily_series(filters, rows)

    @api.model
    def _get_daily_orders(self, filters):
        if self._is_product_filtered(filters):
            where, params = self._build_line_where(filters, ['sale', 'done'])
            query = "SELECT TO_CHAR(DATE(so.date_order), 'YYYY-MM-DD') AS date, COUNT(DISTINCT so.id) AS value FROM sale_order so JOIN sale_order_line sol ON sol.order_id = so.id WHERE %s GROUP BY DATE(so.date_order) ORDER BY DATE(so.date_order)" % ' AND '.join(where)
        else:
            where, params = self._build_order_where(filters, ['sale', 'done'])
            query = "SELECT TO_CHAR(DATE(so.date_order), 'YYYY-MM-DD') AS date, COUNT(so.id) AS value FROM sale_order so WHERE %s GROUP BY DATE(so.date_order) ORDER BY DATE(so.date_order)" % ' AND '.join(where)
        rows = {row['date']: row for row in self._fetchall_dict(query, params)}
        return self._complete_daily_series(filters, rows, int_values=True)

    @api.model
    def _get_monthly_revenue(self, filters):
        if self._is_product_filtered(filters):
            where, params = self._build_line_where(filters, ['sale', 'done'])
            query = "SELECT TO_CHAR(DATE_TRUNC('month', so.date_order), 'YYYY-MM-DD') AS date, TO_CHAR(DATE_TRUNC('month', so.date_order), 'Mon YYYY') AS label, COALESCE(SUM(sol.price_total), 0.0) AS value FROM sale_order so JOIN sale_order_line sol ON sol.order_id = so.id WHERE %s GROUP BY DATE_TRUNC('month', so.date_order) ORDER BY DATE_TRUNC('month', so.date_order)" % ' AND '.join(where)
        else:
            where, params = self._build_order_where(filters, ['sale', 'done'])
            query = "SELECT TO_CHAR(DATE_TRUNC('month', so.date_order), 'YYYY-MM-DD') AS date, TO_CHAR(DATE_TRUNC('month', so.date_order), 'Mon YYYY') AS label, COALESCE(SUM(so.amount_total), 0.0) AS value FROM sale_order so WHERE %s GROUP BY DATE_TRUNC('month', so.date_order) ORDER BY DATE_TRUNC('month', so.date_order)" % ' AND '.join(where)
        return self._fetchall_dict(query, params)

    @api.model
    def _get_average_order_trend(self, filters):
        where, params = self._build_order_where(filters, ['sale', 'done'])
        query = "SELECT TO_CHAR(DATE(so.date_order), 'YYYY-MM-DD') AS date, COALESCE(AVG(so.amount_total), 0.0) AS value FROM sale_order so WHERE %s GROUP BY DATE(so.date_order) ORDER BY DATE(so.date_order)" % ' AND '.join(where)
        rows = {row['date']: row for row in self._fetchall_dict(query, params)}
        return self._complete_daily_series(filters, rows)

    @api.model
    def _get_quotation_funnel(self, metrics):
        total = (metrics['quotation_orders'] + metrics['confirmed_orders']) or 1
        return [
            {'key': 'quotations', 'label': 'Open Quotations', 'value': metrics['quotation_orders'], 'pct': metrics['quotation_orders'] / total * 100.0},
            {'key': 'confirmed', 'label': 'Confirmed Orders', 'value': metrics['confirmed_orders'], 'pct': metrics['confirmed_orders'] / total * 100.0},
        ]

    @api.model
    def _get_state_distribution(self, filters):
        where, params = self._build_order_where(filters)
        query = """
            SELECT so.state AS key,
                   CASE so.state WHEN 'draft' THEN 'Draft Quotation' WHEN 'sent' THEN 'Sent Quotation' WHEN 'sale' THEN 'Sales Order' WHEN 'done' THEN 'Locked Order' WHEN 'cancel' THEN 'Cancelled' ELSE so.state END AS label,
                   COUNT(so.id) AS value
              FROM sale_order so
             WHERE %s
          GROUP BY so.state
          ORDER BY value DESC
        """ % ' AND '.join(where)
        return self._fetchall_dict(query, params)

    @api.model
    def _limit_with_others(self, rows, value_key='value', label='Others'):
        if len(rows) <= self._TOP_LIMIT:
            return rows
        top = rows[: self._TOP_LIMIT - 1]
        remaining = rows[self._TOP_LIMIT - 1:]
        others = {'label': label, 'record_id': 0, value_key: sum(float(r.get(value_key) or 0.0) for r in remaining)}
        if any('orders_count' in r for r in remaining):
            others['orders_count'] = sum(int(r.get('orders_count') or 0) for r in remaining)
        if any('quantity' in r for r in remaining):
            others['quantity'] = sum(float(r.get('quantity') or 0.0) for r in remaining)
        top.append(others)
        return top

    @api.model
    def _get_team_performance(self, filters):
        team_label_sql = self._json_name_expr('team.name', 'No Team', 'crm_team')
        if self._is_product_filtered(filters):
            where, params = self._build_line_where(filters, ['sale', 'done'])
            query = ("SELECT %s AS label, COALESCE(team.id, 0) AS record_id, COALESCE(SUM(sol.price_total), 0.0) AS value, COUNT(DISTINCT so.id) AS orders_count FROM sale_order so LEFT JOIN crm_team team ON team.id = so.team_id JOIN sale_order_line sol ON sol.order_id = so.id WHERE %s GROUP BY team.id, team.name ORDER BY value DESC" % (team_label_sql, ' AND '.join(where)))
        else:
            where, params = self._build_order_where(filters, ['sale', 'done'])
            query = ("SELECT %s AS label, COALESCE(team.id, 0) AS record_id, COALESCE(SUM(so.amount_total), 0.0) AS value, COUNT(so.id) AS orders_count FROM sale_order so LEFT JOIN crm_team team ON team.id = so.team_id WHERE %s GROUP BY team.id, team.name ORDER BY value DESC" % (team_label_sql, ' AND '.join(where)))
        return self._limit_with_others(self._fetchall_dict(query, params))

    @api.model
    def _get_salesperson_performance(self, filters):
        if self._is_product_filtered(filters):
            where, params = self._build_line_where(filters, ['sale', 'done'])
            query = "SELECT COALESCE(partner.name, users.login, 'No Salesperson') AS label, COALESCE(users.id, 0) AS record_id, COALESCE(SUM(sol.price_total), 0.0) AS value, COUNT(DISTINCT so.id) AS orders_count FROM sale_order so LEFT JOIN res_users users ON users.id = so.user_id LEFT JOIN res_partner partner ON partner.id = users.partner_id JOIN sale_order_line sol ON sol.order_id = so.id WHERE %s GROUP BY users.id, partner.name, users.login ORDER BY value DESC" % ' AND '.join(where)
        else:
            where, params = self._build_order_where(filters, ['sale', 'done'])
            query = "SELECT COALESCE(partner.name, users.login, 'No Salesperson') AS label, COALESCE(users.id, 0) AS record_id, COALESCE(SUM(so.amount_total), 0.0) AS value, COUNT(so.id) AS orders_count FROM sale_order so LEFT JOIN res_users users ON users.id = so.user_id LEFT JOIN res_partner partner ON partner.id = users.partner_id WHERE %s GROUP BY users.id, partner.name, users.login ORDER BY value DESC" % ' AND '.join(where)
        return self._limit_with_others(self._fetchall_dict(query, params))

    @api.model
    def _get_top_customers(self, filters):
        partner_label_sql = self._partner_name_expr('partner.name', 'No Customer')
        if self._is_product_filtered(filters):
            where, params = self._build_line_where(filters, ['sale', 'done'])
            query = ("SELECT %s AS label, COALESCE(partner.id, 0) AS record_id, COALESCE(SUM(sol.price_total), 0.0) AS value, COUNT(DISTINCT so.id) AS orders_count FROM sale_order so LEFT JOIN res_partner partner ON partner.id = so.partner_id JOIN sale_order_line sol ON sol.order_id = so.id WHERE %s GROUP BY partner.id, partner.name ORDER BY value DESC" % (partner_label_sql, ' AND '.join(where)))
        else:
            where, params = self._build_order_where(filters, ['sale', 'done'])
            query = ("SELECT %s AS label, COALESCE(partner.id, 0) AS record_id, COALESCE(SUM(so.amount_total), 0.0) AS value, COUNT(so.id) AS orders_count FROM sale_order so LEFT JOIN res_partner partner ON partner.id = so.partner_id WHERE %s GROUP BY partner.id, partner.name ORDER BY value DESC" % (partner_label_sql, ' AND '.join(where)))
        return self._limit_with_others(self._fetchall_dict(query, params))

    @api.model
    def _get_top_products(self, filters):
        where, params = self._build_line_where(filters, ['sale', 'done'])
        product_label_sql = self._json_name_expr('product_template.name', 'No Product', 'product_template')
        query = ("SELECT COALESCE(%s, product.default_code, 'No Product') AS label, COALESCE(product.id, 0) AS record_id, COALESCE(SUM(sol.price_total), 0.0) AS value, COALESCE(SUM(sol.product_uom_qty), 0.0) AS quantity FROM sale_order so JOIN sale_order_line sol ON sol.order_id = so.id LEFT JOIN product_product product ON product.id = sol.product_id LEFT JOIN product_template product_template ON product_template.id = product.product_tmpl_id WHERE %s GROUP BY product.id, product_template.name, product.default_code ORDER BY value DESC" % (product_label_sql, ' AND '.join(where)))
        return self._limit_with_others(self._fetchall_dict(query, params))

    @api.model
    def _get_top_categories(self, filters):
        where, params = self._build_line_where(filters, ['sale', 'done'])
        category_label_sql = self._json_name_expr('category.name', 'No Category', 'product_category')
        query = ("SELECT %s AS label, COALESCE(category.id, 0) AS record_id, COALESCE(SUM(sol.price_total), 0.0) AS value FROM sale_order so JOIN sale_order_line sol ON sol.order_id = so.id LEFT JOIN product_product product ON product.id = sol.product_id LEFT JOIN product_template product_template ON product_template.id = product.product_tmpl_id LEFT JOIN product_category category ON category.id = product_template.categ_id WHERE %s GROUP BY category.id, category.name ORDER BY value DESC" % (category_label_sql, ' AND '.join(where)))
        return self._limit_with_others(self._fetchall_dict(query, params))

    @api.model
    def _get_weekday_heatmap(self, filters):
        if self._is_product_filtered(filters):
            where, params = self._build_line_where(filters, ['sale', 'done'])
            query = "SELECT EXTRACT(ISODOW FROM so.date_order) AS weekday_index, COALESCE(SUM(sol.price_total), 0.0) AS value FROM sale_order so JOIN sale_order_line sol ON sol.order_id = so.id WHERE %s GROUP BY EXTRACT(ISODOW FROM so.date_order) ORDER BY weekday_index" % ' AND '.join(where)
        else:
            where, params = self._build_order_where(filters, ['sale', 'done'])
            query = "SELECT EXTRACT(ISODOW FROM so.date_order) AS weekday_index, COALESCE(SUM(so.amount_total), 0.0) AS value FROM sale_order so WHERE %s GROUP BY EXTRACT(ISODOW FROM so.date_order) ORDER BY weekday_index" % ' AND '.join(where)
        rows = {int(row['weekday_index']): row for row in self._fetchall_dict(query, params)}
        labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        return [{'key': idx, 'label': label, 'value': float(rows.get(idx, {}).get('value') or 0.0)} for idx, label in enumerate(labels, start=1)]

    @api.model
    def _get_target_progress(self, filters, metrics):
        month_starts = []
        current = fields.Date.start_of(fields.Date.to_date(filters['date_from']), 'month')
        end = fields.Date.start_of(fields.Date.to_date(filters['date_to']), 'month')
        while current <= end:
            month_starts.append(current)
            current = current + relativedelta(months=1)
        targets = self.env['omg.sales.dashboard.target'].search([('company_id', 'in', filters['company_ids']), ('month_start', 'in', month_starts), ('active', '=', True)])
        if filters.get('team_ids'):
            targets = targets.filtered(lambda t: t.scope != 'team' or t.team_id.id in filters['team_ids'])
        if filters.get('user_ids'):
            targets = targets.filtered(lambda t: t.scope != 'user' or t.user_id.id in filters['user_ids'])

        target_map = {}
        for target in targets:
            if target.scope == 'team':
                key = 'team_%s' % target.team_id.id
                record_id = target.team_id.id
                label = target.team_id.display_name
            else:
                key = 'user_%s' % target.user_id.id
                record_id = target.user_id.id
                label = target.user_id.display_name
            target_map.setdefault(key, {'key': key, 'label': label, 'owner_type': target.scope, 'record_id': record_id, 'target_amount': 0.0})
            target_map[key]['target_amount'] += target.target_amount

        actual_by_owner = {}
        for row in self._get_team_performance(filters):
            if row.get('record_id'):
                actual_by_owner['team_%s' % row['record_id']] = row['value']
        for row in self._get_salesperson_performance(filters):
            if row.get('record_id'):
                actual_by_owner['user_%s' % row['record_id']] = row['value']
        lines = []
        for key, item in target_map.items():
            actual = actual_by_owner.get(key, 0.0)
            achievement = (actual / item['target_amount'] * 100.0) if item['target_amount'] else 0.0
            lines.append(dict(item, actual_amount=actual, achievement=achievement))
        lines.sort(key=lambda x: x['achievement'], reverse=True)
        total_target = sum(line['target_amount'] for line in lines)
        return {'overall_target_amount': total_target, 'overall_achievement': (metrics['confirmed_revenue'] / total_target * 100.0) if total_target else 0.0, 'lines': lines[:10]}

    @api.model
    def _line_cost_expression(self):
        self.env.cr.execute("SELECT 1 FROM information_schema.columns WHERE table_name = 'sale_order_line' AND column_name = 'purchase_price'")
        if self.env.cr.fetchone():
            return 'COALESCE(sol.purchase_price, 0.0) * COALESCE(sol.product_uom_qty, 0.0)'
        return '0.0'

    @api.model
    def _get_profitability(self, filters):
        where, params = self._build_line_where(filters, ['sale', 'done'])
        cost_expr = self._line_cost_expression()
        summary = self._fetchall_dict("SELECT COALESCE(SUM(sol.price_subtotal), 0.0) AS revenue, COALESCE(SUM(sol.price_subtotal - (%s)), 0.0) AS margin_amount FROM sale_order so JOIN sale_order_line sol ON sol.order_id = so.id LEFT JOIN product_product product ON product.id = sol.product_id LEFT JOIN product_template product_template ON product_template.id = product.product_tmpl_id WHERE %s" % (cost_expr, ' AND '.join(where)), params)
        revenue = float(summary[0]['revenue'] if summary else 0.0)
        margin_amount = float(summary[0]['margin_amount'] if summary else 0.0)
        product_label_sql = self._json_name_expr('product_template.name', 'No Product', 'product_template')
        top_products = self._fetchall_dict("SELECT COALESCE(%s, product.default_code, 'No Product') AS label, COALESCE(product.id, 0) AS record_id, COALESCE(SUM(sol.price_subtotal - (%s)), 0.0) AS value FROM sale_order so JOIN sale_order_line sol ON sol.order_id = so.id LEFT JOIN product_product product ON product.id = sol.product_id LEFT JOIN product_template product_template ON product_template.id = product.product_tmpl_id WHERE %s GROUP BY product.id, product_template.name, product.default_code ORDER BY value DESC LIMIT 10" % (product_label_sql, cost_expr, ' AND '.join(where)), params)
        partner_label_sql = self._partner_name_expr('partner.name', 'No Customer')
        top_customers = self._fetchall_dict("SELECT %s AS label, COALESCE(partner.id, 0) AS record_id, COALESCE(SUM(sol.price_subtotal - (%s)), 0.0) AS value FROM sale_order so JOIN sale_order_line sol ON sol.order_id = so.id LEFT JOIN res_partner partner ON partner.id = so.partner_id LEFT JOIN product_product product ON product.id = sol.product_id LEFT JOIN product_template product_template ON product_template.id = product.product_tmpl_id WHERE %s GROUP BY partner.id, partner.name ORDER BY value DESC LIMIT 10" % (partner_label_sql, cost_expr, ' AND '.join(where)), params)
        low_margin = self._fetchall_dict("SELECT so.id AS record_id, so.name AS label, COALESCE(SUM(sol.price_subtotal), 0.0) AS revenue, COALESCE(SUM(sol.price_subtotal - (%s)), 0.0) AS margin_amount FROM sale_order so JOIN sale_order_line sol ON sol.order_id = so.id LEFT JOIN product_product product ON product.id = sol.product_id LEFT JOIN product_template product_template ON product_template.id = product.product_tmpl_id WHERE %s GROUP BY so.id, so.name HAVING COALESCE(SUM(sol.price_subtotal), 0.0) > 0 ORDER BY (COALESCE(SUM(sol.price_subtotal - (%s)), 0.0) / NULLIF(COALESCE(SUM(sol.price_subtotal), 0.0), 0)) ASC LIMIT 5" % (cost_expr, ' AND '.join(where), cost_expr), params)
        for row in low_margin:
            revenue_value = float(row.get('revenue') or 0.0)
            row['margin_rate'] = (float(row.get('margin_amount') or 0.0) / revenue_value * 100.0) if revenue_value else 0.0
        return {'revenue': revenue, 'margin_amount': margin_amount, 'margin_rate': (margin_amount / revenue * 100.0) if revenue else 0.0, 'top_products': top_products, 'top_customers': top_customers, 'low_margin_orders': low_margin}

    @api.model
    def _get_alerts(self, metrics, profitability, targets):
        alerts = []
        if not metrics['confirmed_orders']:
            alerts.append({'level': 'warning', 'title': 'No confirmed orders', 'message': 'No confirmed sales orders match the current filters.'})
        if metrics['quotation_orders'] > metrics['confirmed_orders'] * 1.5 and metrics['quotation_orders'] > 3:
            alerts.append({'level': 'info', 'title': 'Quotations are stacking up', 'message': 'Quotation volume is much higher than confirmed orders. Review conversion follow-up.'})
        if metrics['win_rate'] < 35 and (metrics['quotation_orders'] + metrics['confirmed_orders']) > 3:
            alerts.append({'level': 'warning', 'title': 'Low win rate', 'message': 'Win rate is below 35% for the selected period.'})
        if targets.get('overall_target_amount') and targets.get('overall_achievement', 0.0) < 60:
            alerts.append({'level': 'danger', 'title': 'Target is behind plan', 'message': 'Achievement is below 60% of configured sales targets.'})
        if profitability.get('margin_rate', 0.0) < 15 and profitability.get('revenue', 0.0):
            alerts.append({'level': 'warning', 'title': 'Low margin', 'message': 'Approximate margin rate is under 15%. Review pricing or product mix.'})
        return alerts

    @api.model
    def _get_pivot_summary(self, filters):
        team_label_sql = self._json_name_expr('team.name', 'No Team', 'crm_team')
        if self._is_product_filtered(filters):
            where, params = self._build_line_where(filters)
            query = ("SELECT %s AS label, COALESCE(team.id, 0) AS record_id, COUNT(DISTINCT CASE WHEN so.state IN ('draft', 'sent') THEN so.id END) AS quotations, COUNT(DISTINCT CASE WHEN so.state IN ('sale', 'done') THEN so.id END) AS confirmed_orders, COALESCE(SUM(CASE WHEN so.state IN ('sale', 'done') THEN sol.price_total ELSE 0.0 END), 0.0) AS revenue FROM sale_order so JOIN sale_order_line sol ON sol.order_id = so.id LEFT JOIN crm_team team ON team.id = so.team_id WHERE %s GROUP BY team.id, team.name ORDER BY revenue DESC" % (team_label_sql, ' AND '.join(where)))
        else:
            where, params = self._build_order_where(filters)
            query = ("SELECT %s AS label, COALESCE(team.id, 0) AS record_id, COUNT(CASE WHEN so.state IN ('draft', 'sent') THEN so.id END) AS quotations, COUNT(CASE WHEN so.state IN ('sale', 'done') THEN so.id END) AS confirmed_orders, COALESCE(SUM(CASE WHEN so.state IN ('sale', 'done') THEN so.amount_total ELSE 0.0 END), 0.0) AS revenue FROM sale_order so LEFT JOIN crm_team team ON team.id = so.team_id WHERE %s GROUP BY team.id, team.name ORDER BY revenue DESC" % (team_label_sql, ' AND '.join(where)))
        rows = self._fetchall_dict(query, params)
        for row in rows:
            confirmed = int(row.get('confirmed_orders') or 0)
            quotations = int(row.get('quotations') or 0)
            revenue = float(row.get('revenue') or 0.0)
            row['average_order_value'] = revenue / confirmed if confirmed else 0.0
            row['conversion'] = confirmed / (confirmed + quotations) * 100.0 if (confirmed + quotations) else 0.0
        return rows[:10]

    @api.model
    def _get_orders(self, filters):
        where, params = self._build_order_where(filters)
        team_label_sql = self._json_name_expr('team.name', 'No Team', 'crm_team')
        customer_label_sql = self._partner_name_expr('customer.name', 'No Customer')
        query = ("SELECT so.id, so.name, TO_CHAR(so.date_order, 'YYYY-MM-DD HH24:MI') AS date_order, so.state, %s AS team_name, %s AS partner_name, COALESCE(user_partner.name, users.login, 'No Salesperson') AS salesperson_name, COALESCE(so.amount_total, 0.0) AS amount_total, COALESCE(so.amount_untaxed, 0.0) AS amount_untaxed FROM sale_order so LEFT JOIN crm_team team ON team.id = so.team_id LEFT JOIN res_partner customer ON customer.id = so.partner_id LEFT JOIN res_users users ON users.id = so.user_id LEFT JOIN res_partner user_partner ON user_partner.id = users.partner_id WHERE %s ORDER BY so.date_order DESC LIMIT 500" % (team_label_sql, customer_label_sql, ' AND '.join(where)))
        rows = self._fetchall_dict(query, params)
        return {'rows': rows, 'totals': {'amount_total': sum(float(row.get('amount_total') or 0.0) for row in rows), 'count': len(rows)}}
