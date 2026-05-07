# Developer Guide

## Module map
- `models/sales_dashboard_service.py`: aggregated backend payload for dashboard analytics
- `models/dashboard_target.py`: monthly targets by team or salesperson
- `controllers/dashboard_controller.py`: JSON endpoints for options and dashboard data
- `static/src/js/dashboard_action.js`: OWL client action logic
- `static/src/xml/dashboard_templates.xml`: dashboard template
- `static/src/scss/dashboard.scss`: static enterprise-style design

## Notes
- Product filters switch several metrics to line-based aggregation.
- Raw SQL is used for speed, so access is restricted manually for non-managers.
- Profitability is approximate and uses `sale_order_line.purchase_price` when available, otherwise product standard cost.
- Favorites and UI personalization are stored in browser local storage.
