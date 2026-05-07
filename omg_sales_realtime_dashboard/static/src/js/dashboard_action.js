/** @odoo-module **/

import { Component, onMounted, onWillStart, onWillUnmount, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const STORAGE_KEY = "omg_sales_realtime_dashboard.preferences";
const FAVORITES_KEY = "omg_sales_realtime_dashboard.favorites";
const PANEL_DEFS = [
    { key: "daily_revenue", label: "Daily Revenue", wide: true },
    { key: "daily_orders", label: "Daily Orders" },
    { key: "monthly_revenue", label: "Monthly Revenue" },
    { key: "quotation_funnel", label: "Quotation Funnel" },
    { key: "state_distribution", label: "State Mix" },
    { key: "team_performance", label: "Team Performance" },
    { key: "salesperson_performance", label: "Salesperson Performance" },
    { key: "top_customers", label: "Top Customers" },
    { key: "top_products", label: "Top Products" },
    { key: "top_categories", label: "Top Categories" },
    { key: "average_order_trend", label: "Average Order Trend", wide: true },
    { key: "weekday_heatmap", label: "Weekday Heatmap" },
    { key: "target_progress", label: "Target Progress", wide: true },
    { key: "profit_top_products", label: "Profit by Product" },
    { key: "profit_top_customers", label: "Profit by Customer" },
    { key: "low_margin_orders", label: "Low Margin Orders", wide: true },
    { key: "alerts", label: "Alerts" },
    { key: "pivot_summary", label: "Pivot Summary", wide: true },
];
const ALL_COLUMN_DEFS = [
    { key: "name", label: "Order", type: "text" },
    { key: "date_order", label: "Date", type: "text" },
    { key: "state", label: "State", type: "text" },
    { key: "team_name", label: "Sales Team", type: "text" },
    { key: "salesperson_name", label: "Salesperson", type: "text" },
    { key: "partner_name", label: "Customer", type: "text" },
    { key: "amount_total", label: "Total", type: "currency" },
    { key: "amount_untaxed", label: "Untaxed", type: "currency" },
];
const DEFAULT_VISIBLE_COLUMNS = {
    name: true,
    date_order: true,
    state: true,
    team_name: true,
    salesperson_name: true,
    partner_name: true,
    amount_total: true,
    amount_untaxed: false,
};

function loadJson(key, fallback) {
    try {
        const raw = window.localStorage.getItem(key);
        return raw ? JSON.parse(raw) : fallback;
    } catch (_error) {
        return fallback;
    }
}

function saveJson(key, value) {
    try {
        window.localStorage.setItem(key, JSON.stringify(value));
    } catch (_error) {
        return;
    }
}

export class OMGSalesRealtimeDashboard extends Component {
    static template = "omg_sales_realtime_dashboard.Dashboard";

    setup() {
        this.rpc = useService("rpc");
        this.action = useService("action");
        this.notification = useService("notification");

        const today = new Date();
        const start = new Date(today);
        start.setDate(today.getDate() - 29);

        const saved = loadJson(STORAGE_KEY, {});
        const favorites = loadJson(FAVORITES_KEY, []);
        const defaultPanelOrder = PANEL_DEFS.map((panel) => panel.key);
        const visiblePanels = {};
        const collapsedPanels = {};
        for (const key of defaultPanelOrder) {
            visiblePanels[key] = true;
            collapsedPanels[key] = false;
        }

        this.state = useState({
            loading: true,
            reloading: false,
            error: null,
            options: null,
            dashboard: null,
            viewMode: saved.viewMode || "dashboard",
            groupBy: saved.groupBy || "none",
            sortBy: saved.sortBy || "date_order",
            sortAsc: saved.sortAsc || false,
            openDropdown: null,
            showFilters: true,
            draftFilters: {
                date_from: saved.filters?.date_from || this.toInputDate(start),
                date_to: saved.filters?.date_to || this.toInputDate(today),
                team_ids: saved.filters?.team_ids || [],
                product_ids: saved.filters?.product_ids || [],
                partner_ids: saved.filters?.partner_ids || [],
                user_ids: saved.filters?.user_ids || [],
                refresh_interval_ms: saved.filters?.refresh_interval_ms || 0,
            },
            searches: { team_ids: "", product_ids: "", partner_ids: "", user_ids: "" },
            visibleColumns: Object.assign({}, DEFAULT_VISIBLE_COLUMNS, saved.visibleColumns || {}),
            visiblePanels: Object.assign({}, visiblePanels, saved.visiblePanels || {}),
            collapsedPanels: Object.assign({}, collapsedPanels, saved.collapsedPanels || {}),
            panelOrder: saved.panelOrder || defaultPanelOrder,
            favorites,
        });

        this.autoRefreshTimer = null;

        this.onRefreshNow = () => this.fetchDashboard(true);
        this.onApplyFilters = () => this.applyFilters();
        this.onResetFilters = () => this.resetFilters();
        this.onToggleFilters = () => this.toggleFilters();
        this.onOpenDashboardMode = () => this.toggleViewMode("dashboard");
        this.onOpenListMode = () => this.toggleViewMode("list");
        this.onToggleAutoRefresh = () => this.toggleAutoRefresh();
        this.onSaveFavorite = () => this.saveFavorite();
        this.onOpenOrdersList = () => this.openOrdersList();
        this.onExportCsv = () => this.exportCsv();
        this.onCollapseAllPanels = () => this.setAllPanelsCollapsed(true);
        this.onExpandAllPanels = () => this.setAllPanelsCollapsed(false);

        const methodsToBind = [
            'toggleFilters', 'toggleViewMode', 'toggleDropdown', 'closeDropdowns', 'updateSearch',
            'updateDate', 'setGroupBy', 'setRefreshInterval', 'toggleAutoRefresh', 'applyFilters',
            'resetFilters', 'applyPreset', 'filteredOptions', 'selectedItems', 'dropdownLabel',
            'toggleSelection', 'removeChip', 'clearSelection', 'selectAllVisible', 'saveFavorite',
            'applyFavorite', 'deleteFavorite', 'toggleColumn', 'togglePanel', 'togglePanelCollapsed',
            'setAllPanelsCollapsed', 'movePanel', 'setSort', 'exportCsv', 'openOrdersList',
            'onKpiClick', 'drilldownByState', 'drilldownByDate', 'drilldownByRecord', 'openOrder',
            'panelLabel', 'panelClass', 'formatCurrency', 'formatNumber', 'formatPercent',
            'formatValueByType', 'differenceClass', 'maxValue', 'horizontalBarStyle', 'verticalBarStyle',
            'heatStyle', 'donutStyle', 'linePath', 'areaPath', 'groupTotal', 'toInputDate',
        ];
        for (const methodName of methodsToBind) {
            this[methodName] = this[methodName].bind(this);
        }

        onWillStart(async () => {
            await this.loadOptions();
            await this.fetchDashboard();
        });
        onMounted(() => this.syncAutoRefresh());
        onWillUnmount(() => this.clearAutoRefresh());
    }

    get panelDefs() {
        return PANEL_DEFS.filter((panel) => this.state.visiblePanels[panel.key]).sort((a, b) => this.state.panelOrder.indexOf(a.key) - this.state.panelOrder.indexOf(b.key));
    }

    get allColumnDefs() {
        return ALL_COLUMN_DEFS;
    }

    get visibleColumns() {
        return ALL_COLUMN_DEFS.filter((column) => this.state.visibleColumns[column.key]);
    }

    get teamOptions() {
        return this.state.options ? this.state.options.teams : [];
    }

    get productOptions() {
        return this.state.options ? this.state.options.products : [];
    }

    get partnerOptions() {
        return this.state.options ? this.state.options.partners : [];
    }

    get salespersonOptions() {
        return this.state.options ? this.state.options.salespeople : [];
    }

    get filterDefinitions() {
        return {
            team_ids: this.teamOptions,
            product_ids: this.productOptions,
            partner_ids: this.partnerOptions,
            user_ids: this.salespersonOptions,
        };
    }

    get dashboard() {
        return this.state.dashboard || {};
    }

    get charts() {
        return this.dashboard.charts || {};
    }

    get currency() {
        return this.dashboard.currency || (this.state.options ? this.state.options.currency : null) || { symbol: "$", position: "before" };
    }

    get kpis() {
        return this.dashboard.kpis || [];
    }

    get comparisonCards() {
        return this.dashboard.comparison_cards || [];
    }

    get ordersRows() {
        return (this.dashboard.orders && this.dashboard.orders.rows) || [];
    }

    get groupedOrders() {
        const rows = [...this.ordersRows];
        const sortBy = this.state.sortBy;
        const sortAsc = this.state.sortAsc ? 1 : -1;
        rows.sort((left, right) => {
            const a = left[sortBy];
            const b = right[sortBy];
            if (typeof a === "number" || typeof b === "number") {
                return ((a || 0) - (b || 0)) * sortAsc;
            }
            return String(a || "").localeCompare(String(b || "")) * sortAsc;
        });
        if (this.state.groupBy === "none") {
            return [{ key: "all", label: "All Orders", rows }];
        }
        const groups = new Map();
        for (const row of rows) {
            let key = "Unknown";
            if (this.state.groupBy === "team") key = row.team_name || "No Team";
            if (this.state.groupBy === "salesperson") key = row.salesperson_name || "No Salesperson";
            if (this.state.groupBy === "customer") key = row.partner_name || "No Customer";
            if (this.state.groupBy === "state") key = row.state || "No State";
            if (this.state.groupBy === "month") key = (row.date_order || "").slice(0, 7) || "Unknown Month";
            if (!groups.has(key)) groups.set(key, []);
            groups.get(key).push(row);
        }
        return Array.from(groups.entries()).map(([key, groupRows]) => ({ key, label: key, rows: groupRows }));
    }

    async loadOptions() {
        this.state.options = await this.rpc("/omg_sales_realtime_dashboard/options", {});
    }

    buildPayloadFilters() {
        return { ...this.state.draftFilters, group_by: this.state.groupBy };
    }

    async fetchDashboard(showReload = false) {
        this.state.error = null;
        if (!this.state.dashboard) this.state.loading = true;
        else if (showReload) this.state.reloading = true;
        try {
            this.state.dashboard = await this.rpc("/omg_sales_realtime_dashboard/data", { filters: this.buildPayloadFilters() });
            this.persistPreferences();
            this.syncAutoRefresh();
        } catch (error) {
            console.error(error);
            this.state.error = error && error.message ? error.message : "Unable to load the dashboard.";
        } finally {
            this.state.loading = false;
            this.state.reloading = false;
        }
    }

    persistPreferences() {
        saveJson(STORAGE_KEY, {
            viewMode: this.state.viewMode,
            groupBy: this.state.groupBy,
            sortBy: this.state.sortBy,
            sortAsc: this.state.sortAsc,
            filters: this.state.draftFilters,
            visibleColumns: this.state.visibleColumns,
            visiblePanels: this.state.visiblePanels,
            collapsedPanels: this.state.collapsedPanels,
            panelOrder: this.state.panelOrder,
        });
        saveJson(FAVORITES_KEY, this.state.favorites);
    }

    clearAutoRefresh() {
        if (this.autoRefreshTimer) {
            window.clearInterval(this.autoRefreshTimer);
            this.autoRefreshTimer = null;
        }
    }

    syncAutoRefresh() {
        this.clearAutoRefresh();
        const interval = this.state.draftFilters.refresh_interval_ms;
        if (!interval) return;
        this.autoRefreshTimer = window.setInterval(() => this.fetchDashboard(), interval);
    }

    toggleFilters() { this.state.showFilters = !this.state.showFilters; }
    toggleViewMode(mode) { this.state.viewMode = mode; this.persistPreferences(); }
    toggleDropdown(key) { this.state.openDropdown = this.state.openDropdown === key ? null : key; }
    closeDropdowns() { this.state.openDropdown = null; }
    updateSearch(field, ev) { this.state.searches[field] = ev.target.value || ""; }
    updateDate(field, ev) { this.state.draftFilters[field] = ev.target.value; }
    setGroupBy(ev) { this.state.groupBy = ev.target.value; this.persistPreferences(); }
    setRefreshInterval(ev) { this.state.draftFilters.refresh_interval_ms = parseInt(ev.target.value, 10) || 0; this.persistPreferences(); this.syncAutoRefresh(); }
    toggleAutoRefresh() { this.state.draftFilters.refresh_interval_ms = this.state.draftFilters.refresh_interval_ms ? 0 : 30000; this.persistPreferences(); this.syncAutoRefresh(); }
    applyFilters() { this.closeDropdowns(); this.fetchDashboard(true); }

    resetFilters() {
        const today = new Date();
        const start = new Date(today);
        start.setDate(today.getDate() - 29);
        this.state.draftFilters = {
            date_from: this.toInputDate(start),
            date_to: this.toInputDate(today),
            team_ids: [], product_ids: [], partner_ids: [], user_ids: [], refresh_interval_ms: 0,
        };
        this.state.groupBy = "none";
        this.state.searches = { team_ids: "", product_ids: "", partner_ids: "", user_ids: "" };
        this.fetchDashboard(true);
    }

    applyPreset(key) {
        const today = new Date();
        let start = new Date(today);
        const end = new Date(today);
        if (key === "this_week") {
            const day = today.getDay() || 7;
            start.setDate(today.getDate() - (day - 1));
        } else if (key === "this_month") {
            start = new Date(today.getFullYear(), today.getMonth(), 1);
        } else if (key === "this_quarter") {
            const quarterStartMonth = Math.floor(today.getMonth() / 3) * 3;
            start = new Date(today.getFullYear(), quarterStartMonth, 1);
        } else if (key === "this_year") {
            start = new Date(today.getFullYear(), 0, 1);
        }
        this.state.draftFilters.date_from = this.toInputDate(start);
        this.state.draftFilters.date_to = this.toInputDate(end);
    }

    filteredOptions(field) {
        const options = this.filterDefinitions[field] || [];
        const query = (this.state.searches[field] || "").toLowerCase().trim();
        return query ? options.filter((item) => (item.name || "").toLowerCase().includes(query)) : options;
    }

    selectedItems(field) {
        const ids = this.state.draftFilters[field] || [];
        const map = new Map((this.filterDefinitions[field] || []).map((item) => [item.id, item]));
        return ids.map((id) => map.get(id)).filter(Boolean);
    }

    dropdownLabel(field, fallback) {
        const items = this.selectedItems(field);
        if (!items.length) return fallback;
        if (items.length === 1) return items[0].name;
        if (items.length === 2) return `${items[0].name}, ${items[1].name}`;
        return `${items[0].name}, ${items[1].name} +${items.length - 2}`;
    }

    toggleSelection(field, optionId) {
        const values = Array.from(this.state.draftFilters[field] || []);
        const index = values.indexOf(optionId);
        if (index >= 0) values.splice(index, 1);
        else values.push(optionId);
        this.state.draftFilters[field] = values;
    }

    removeChip(field, optionId) { this.state.draftFilters[field] = (this.state.draftFilters[field] || []).filter((id) => id !== optionId); }
    clearSelection(field) { this.state.draftFilters[field] = []; }
    selectAllVisible(field) { this.state.draftFilters[field] = Array.from(new Set([...(this.state.draftFilters[field] || []), ...this.filteredOptions(field).map((item) => item.id)])); }

    saveFavorite() {
        const name = window.prompt("Favorite name");
        if (!name) return;
        this.state.favorites.unshift({ name, filters: JSON.parse(JSON.stringify(this.state.draftFilters)), groupBy: this.state.groupBy });
        this.state.favorites = this.state.favorites.slice(0, 10);
        this.persistPreferences();
        this.notification.add("Favorite saved.", { type: "success" });
    }

    applyFavorite(index) {
        const favorite = this.state.favorites[index];
        if (!favorite) return;
        this.state.draftFilters = JSON.parse(JSON.stringify(favorite.filters));
        this.state.groupBy = favorite.groupBy || "none";
        this.fetchDashboard(true);
    }

    deleteFavorite(index) { this.state.favorites.splice(index, 1); this.persistPreferences(); }
    toggleColumn(key) { this.state.visibleColumns[key] = !this.state.visibleColumns[key]; this.persistPreferences(); }
    togglePanel(key) { this.state.visiblePanels[key] = !this.state.visiblePanels[key]; this.persistPreferences(); }
    togglePanelCollapsed(key) { this.state.collapsedPanels[key] = !this.state.collapsedPanels[key]; this.persistPreferences(); }
    setAllPanelsCollapsed(value) { for (const panel of PANEL_DEFS) this.state.collapsedPanels[panel.key] = value; this.persistPreferences(); }

    movePanel(key, direction) {
        const order = [...this.state.panelOrder];
        const index = order.indexOf(key);
        const next = direction === "up" ? index - 1 : index + 1;
        if (index < 0 || next < 0 || next >= order.length) return;
        const [item] = order.splice(index, 1);
        order.splice(next, 0, item);
        this.state.panelOrder = order;
        this.persistPreferences();
    }

    setSort(field) {
        if (this.state.sortBy === field) this.state.sortAsc = !this.state.sortAsc;
        else {
            this.state.sortBy = field;
            this.state.sortAsc = !["amount_total", "amount_untaxed"].includes(field);
        }
        this.persistPreferences();
    }

    groupTotal(rows) { return rows.reduce((sum, row) => sum + (row.amount_total || 0), 0); }

    exportCsv() {
        const lines = [this.visibleColumns.map((column) => `"${column.label}"`).join(",")];
        for (const row of this.ordersRows) {
            lines.push(this.visibleColumns.map((column) => `"${String(row[column.key] || "").replace(/"/g, '""')}"`).join(","));
        }
        const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "sales_dashboard_export.csv";
        link.click();
        URL.revokeObjectURL(link.href);
    }

    baseDomain() {
        const f = this.state.draftFilters;
        const domain = [["date_order", ">=", `${f.date_from} 00:00:00`], ["date_order", "<=", `${f.date_to} 23:59:59`]];
        if (f.team_ids.length) domain.push(["team_id", "in", f.team_ids]);
        if (f.partner_ids.length) domain.push(["partner_id", "in", f.partner_ids]);
        if (f.user_ids.length) domain.push(["user_id", "in", f.user_ids]);
        if (f.product_ids.length) domain.push(["order_line.product_id", "in", f.product_ids]);
        return domain;
    }

    async openOrdersList(extraDomain = []) {
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: "Matching Sales Orders",
            res_model: "sale.order",
            views: [[false, "list"], [false, "form"], [false, "pivot"], [false, "graph"]],
            domain: [...this.baseDomain(), ...extraDomain],
            target: "current",
        });
    }

    async openOrder(orderId) {
        await this.action.doAction({ type: "ir.actions.act_window", res_model: "sale.order", res_id: orderId, views: [[false, "form"]], target: "current" });
    }

    onKpiClick(kpiKey) {
        const domain = [];
        if (["confirmed_revenue", "confirmed_orders", "average_order_value", "approx_margin"].includes(kpiKey)) domain.push(["state", "in", ["sale", "done"]]);
        if (kpiKey === "quotation_revenue") domain.push(["state", "in", ["draft", "sent"]]);
        this.openOrdersList(domain);
    }

    drilldownByState(item) { if (item && item.key) this.openOrdersList([["state", "=", item.key]]); }
    drilldownByDate(item) { if (item && item.date) this.openOrdersList([["date_order", ">=", `${item.date} 00:00:00`], ["date_order", "<=", `${item.date} 23:59:59`]]); }
    drilldownByRecord(field, recordId) {
        if (!recordId) return;
        const mapping = { team_id: "team_id", user_id: "user_id", partner_id: "partner_id", product_id: "order_line.product_id" };
        if (mapping[field]) this.openOrdersList([[mapping[field], "=", recordId]]);
    }

    formatCurrency(value) {
        const formatted = Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 });
        return this.currency.position === "after" ? `${formatted} ${this.currency.symbol}` : `${this.currency.symbol}${formatted}`;
    }

    formatNumber(value) { return Number(value || 0).toLocaleString(); }
    formatPercent(value) { return `${Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 1 })}%`; }
    formatValueByType(value, type) { return type === "currency" ? this.formatCurrency(value) : type === "percentage" ? this.formatPercent(value) : this.formatNumber(value); }
    differenceClass(value) { return value > 0 ? "is-up" : value < 0 ? "is-down" : "is-neutral"; }

    toInputDate(value) {
        const d = value instanceof Date ? value : new Date(value);
        return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    }

    maxValue(series, key = "value") { return Math.max(0, ...((series || []).map((item) => Number(item[key] || 0)))); }
    horizontalBarStyle(value, series) { const max = this.maxValue(series); return `width:${max ? (Number(value || 0) / max) * 100 : 0}%;`; }
    verticalBarStyle(value, series) { const max = this.maxValue(series); return `height:${max ? Math.max(10, (Number(value || 0) / max) * 100) : 0}%;`; }
    heatStyle(value, series) { const max = this.maxValue(series); const opacity = max ? Math.max(0.08, Number(value || 0) / max) : 0.08; return `background: rgba(113, 75, 103, ${opacity});`; }

    donutStyle(series) {
        const colors = ["#714b67", "#8c6784", "#a57e9b", "#c1a9b6", "#d8cad5"];
        const total = (series || []).reduce((sum, item) => sum + Number(item.value || 0), 0) || 1;
        let start = 0;
        const parts = (series || []).map((item, index) => {
            const pct = Number(item.value || 0) / total * 100;
            const end = start + pct;
            const piece = `${colors[index % colors.length]} ${start}% ${end}%`;
            start = end;
            return piece;
        });
        return `background: conic-gradient(${parts.join(",")});`;
    }

    linePath(series, width = 900, height = 240, padding = 24) {
        if (!series || !series.length) return "";
        const max = this.maxValue(series) || 1;
        const step = series.length > 1 ? (width - padding * 2) / (series.length - 1) : 0;
        return series.map((item, index) => {
            const x = padding + step * index;
            const y = height - padding - ((Number(item.value || 0) / max) * (height - padding * 2));
            return `${index ? "L" : "M"} ${x.toFixed(2)} ${y.toFixed(2)}`;
        }).join(" ");
    }

    areaPath(series, width = 900, height = 240, padding = 24) {
        if (!series || !series.length) return "";
        const line = this.linePath(series, width, height, padding);
        const step = series.length > 1 ? (width - padding * 2) / (series.length - 1) : 0;
        const startX = padding;
        const endX = padding + step * (series.length - 1);
        const baseline = height - padding;
        return `${line} L ${endX.toFixed(2)} ${baseline} L ${startX.toFixed(2)} ${baseline} Z`;
    }


    panelLabel(key) { const panel = PANEL_DEFS.find((item) => item.key === key); return panel ? panel.label : key; }
    panelClass(panel) { return panel.wide ? "o_omg_sales_dashboard__panel o_omg_sales_dashboard__panel--wide" : "o_omg_sales_dashboard__panel"; }
}

registry.category("actions").add("omg_sales_realtime_dashboard.dashboard", OMGSalesRealtimeDashboard);
