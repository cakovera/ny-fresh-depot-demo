from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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


def _money(value: float) -> str:
    return f"${value:,.2f}"


def _table_from_df(df: pd.DataFrame, max_rows: int = 30) -> Table:
    if df.empty:
        data = [["No data"]]
    else:
        view = df.head(max_rows).copy()
        for column in view.columns:
            if pd.api.types.is_float_dtype(view[column]) or pd.api.types.is_integer_dtype(view[column]):
                view[column] = view[column].map(lambda value: f"{value:,.2f}" if pd.notna(value) else "")
        data = [list(view.columns)] + view.astype(str).values.tolist()

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#256f46")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d9e2dc")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7faf7")]),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def create_report_pdf(start_date: date, end_date: date, language: str = "tr") -> bytes:
    totals = totals_report(start_date, end_date)
    sales = sales_report(start_date, end_date)
    customers = customer_profit_report(start_date, end_date)
    products = product_profit_report(start_date, end_date)
    expenses = expenses_report(start_date, end_date)

    labels = {
        "tr": {
            "title": "NY Fresh Depot Raporu",
            "period": "Tarih araligi",
            "summary": "Ozet",
            "sales": "Tum satislar",
            "customers": "Musteri bazinda",
            "products": "Urun bazinda",
            "expenses": "Masraflar",
            "total_sales": "Toplam satis",
            "total_cost": "Toplam maliyet",
            "total_expenses": "Toplam masraf",
            "gross_profit": "Brut kar",
            "net_profit": "Net kar",
        },
        "en": {
            "title": "NY Fresh Depot Report",
            "period": "Date range",
            "summary": "Summary",
            "sales": "All sales",
            "customers": "By customer",
            "products": "By product",
            "expenses": "Expenses",
            "total_sales": "Total sales",
            "total_cost": "Total cost",
            "total_expenses": "Total expenses",
            "gross_profit": "Gross profit",
            "net_profit": "Net profit",
        },
    }
    text = labels.get(language, labels["tr"])

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(text["title"], styles["Title"]),
        Paragraph(f"{text['period']}: {start_date.isoformat()} - {end_date.isoformat()}", styles["Normal"]),
        Spacer(1, 14),
        Paragraph(text["summary"], styles["Heading2"]),
    ]

    summary = Table(
        [
            [text["total_sales"], _money(totals["total_sales"])],
            [text["total_cost"], _money(totals["total_cost"])],
            [text["total_expenses"], _money(totals["total_expenses"])],
            [text["gross_profit"], _money(totals["gross_profit"])],
            [text["net_profit"], _money(totals["net_profit"])],
        ],
        colWidths=[180, 120],
    )
    summary.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d9e2dc")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7faf7")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([summary, Spacer(1, 14)])

    for title, df in [
        (text["customers"], customers),
        (text["products"], products),
        (text["expenses"], expenses),
        (text["sales"], sales),
    ]:
        story.append(Paragraph(title, styles["Heading2"]))
        story.append(_table_from_df(df))
        story.append(Spacer(1, 14))

    doc.build(story)
    return buffer.getvalue()
