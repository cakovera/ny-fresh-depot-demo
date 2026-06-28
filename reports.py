from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from services import fetch_df


def date_range_for_filter(period: str, start_date: date | None = None, end_date: date | None = None) -> tuple[date, date]:
    today = date.today()
    if period == "Gunluk":
        return today, today
    if period == "Haftalik":
        return today - timedelta(days=today.weekday()), today
    if period == "Aylik":
        return today.replace(day=1), today
    return start_date or today, end_date or today


def sales_report(start_date: date, end_date: date) -> pd.DataFrame:
    return fetch_df(
        """
        SELECT s.sale_date, c.name AS customer, p.name AS product, p.category,
               si.quantity, p.unit, si.unit_price,
               si.total_amount AS sales,
               si.total_cost AS cost,
               si.total_amount - si.total_cost AS profit
        FROM sale_items si
        JOIN sales s ON s.id = si.sale_id
        JOIN customers c ON c.id = s.customer_id
        JOIN products p ON p.id = si.product_id
        WHERE date(s.sale_date) BETWEEN date(?) AND date(?)
        ORDER BY s.sale_date DESC, c.name, p.name
        """,
        (start_date.isoformat(), end_date.isoformat()),
    )


def expenses_report(start_date: date, end_date: date) -> pd.DataFrame:
    return fetch_df(
        """
        SELECT expense_date, category, description, amount
        FROM expenses
        WHERE date(expense_date) BETWEEN date(?) AND date(?)
        ORDER BY expense_date DESC
        """,
        (start_date.isoformat(), end_date.isoformat()),
    )


def totals_report(start_date: date, end_date: date) -> dict:
    sales = sales_report(start_date, end_date)
    expenses = expenses_report(start_date, end_date)
    total_sales = float(sales["sales"].sum()) if not sales.empty else 0.0
    total_cost = float(sales["cost"].sum()) if not sales.empty else 0.0
    total_expenses = float(expenses["amount"].sum()) if not expenses.empty else 0.0
    gross_profit = total_sales - total_cost
    net_profit = gross_profit - total_expenses
    return {
        "total_sales": total_sales,
        "total_cost": total_cost,
        "total_expenses": total_expenses,
        "gross_profit": gross_profit,
        "net_profit": net_profit,
    }


def customer_profit_report(start_date: date, end_date: date) -> pd.DataFrame:
    df = sales_report(start_date, end_date)
    if df.empty:
        return pd.DataFrame(columns=["customer", "sales", "cost", "profit"])
    return (
        df.groupby("customer", as_index=False)[["sales", "cost", "profit"]]
        .sum()
        .sort_values("sales", ascending=False)
    )


def product_profit_report(start_date: date, end_date: date) -> pd.DataFrame:
    df = sales_report(start_date, end_date)
    if df.empty:
        return pd.DataFrame(columns=["product", "quantity", "sales", "cost", "profit"])
    return (
        df.groupby("product", as_index=False)[["quantity", "sales", "cost", "profit"]]
        .sum()
        .sort_values("sales", ascending=False)
    )


def dashboard_metrics() -> dict:
    today = date.today()
    totals = totals_report(today, today)
    stock = fetch_df("SELECT SUM(cost_price * stock_quantity) AS stock_value FROM products")
    top_products = fetch_df(
        """
        SELECT p.name AS product, SUM(si.quantity) AS quantity, SUM(si.total_amount) AS sales
        FROM sale_items si
        JOIN products p ON p.id = si.product_id
        GROUP BY p.id
        ORDER BY quantity DESC
        LIMIT 5
        """
    )
    top_customers = fetch_df(
        """
        SELECT c.name AS customer, SUM(si.total_amount) AS sales
        FROM sale_items si
        JOIN sales s ON s.id = si.sale_id
        JOIN customers c ON c.id = s.customer_id
        GROUP BY c.id
        ORDER BY sales DESC
        LIMIT 5
        """
    )
    stock_value = 0.0 if stock.empty or pd.isna(stock.iloc[0]["stock_value"]) else float(stock.iloc[0]["stock_value"])
    return {
        "today_sales": totals["total_sales"],
        "today_profit": totals["net_profit"],
        "stock_value": stock_value,
        "top_products": top_products,
        "top_customers": top_customers,
    }
