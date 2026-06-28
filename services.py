from __future__ import annotations

from datetime import date
from typing import Iterable

import pandas as pd

from database import get_connection


UNITS = ["kasa", "lb", "adet", "box"]
EXPENSE_CATEGORIES = ["Nakliye", "Iscilik", "Benzin", "Kira", "Depo masrafi", "Diger"]


def _to_iso(value: date | str) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def fetch_df(query: str, params: Iterable = ()) -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=tuple(params))


def get_products() -> pd.DataFrame:
    return fetch_df("SELECT * FROM products ORDER BY name")


def get_customers() -> pd.DataFrame:
    return fetch_df("SELECT * FROM customers ORDER BY name")


def product_exists(name: str, exclude_id: int | None = None) -> bool:
    query = "SELECT id FROM products WHERE lower(name) = lower(?)"
    params: list = [name.strip()]
    if exclude_id:
        query += " AND id != ?"
        params.append(exclude_id)
    with get_connection() as conn:
        return conn.execute(query, params).fetchone() is not None


def add_product(name: str, category: str, cost_price: float, sale_price: float, stock_quantity: float, unit: str) -> None:
    if product_exists(name):
        raise ValueError("Ayni urun zaten mevcut.")
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO products (name, category, cost_price, sale_price, stock_quantity, unit)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name.strip(), category.strip(), cost_price, sale_price, stock_quantity, unit),
        )


def update_product(product_id: int, name: str, category: str, cost_price: float, sale_price: float, stock_quantity: float, unit: str) -> None:
    if product_exists(name, exclude_id=product_id):
        raise ValueError("Bu isimde baska bir urun mevcut.")
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE products
            SET name = ?, category = ?, cost_price = ?, sale_price = ?, stock_quantity = ?, unit = ?
            WHERE id = ?
            """,
            (name.strip(), category.strip(), cost_price, sale_price, stock_quantity, unit, product_id),
        )


def delete_product(product_id: int) -> None:
    with get_connection() as conn:
        used = conn.execute("SELECT 1 FROM sale_items WHERE product_id = ? LIMIT 1", (product_id,)).fetchone()
        if used:
            raise ValueError("Bu urun satis kayitlarinda kullanildigi icin silinemez.")
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))


def customer_exists(name: str, exclude_id: int | None = None) -> bool:
    query = "SELECT id FROM customers WHERE lower(name) = lower(?)"
    params: list = [name.strip()]
    if exclude_id:
        query += " AND id != ?"
        params.append(exclude_id)
    with get_connection() as conn:
        return conn.execute(query, params).fetchone() is not None


def add_customer(name: str, address: str, phone: str, notes: str) -> None:
    if customer_exists(name):
        raise ValueError("Ayni musteri zaten mevcut.")
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO customers (name, address, phone, notes) VALUES (?, ?, ?, ?)",
            (name.strip(), address.strip(), phone.strip(), notes.strip()),
        )


def update_customer(customer_id: int, name: str, address: str, phone: str, notes: str) -> None:
    if customer_exists(name, exclude_id=customer_id):
        raise ValueError("Bu isimde baska bir musteri mevcut.")
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE customers
            SET name = ?, address = ?, phone = ?, notes = ?
            WHERE id = ?
            """,
            (name.strip(), address.strip(), phone.strip(), notes.strip(), customer_id),
        )


def delete_customer(customer_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))


def create_sale(customer_id: int, sale_date: date, items: list[dict], notes: str = "") -> int:
    if not items:
        raise ValueError("En az bir urun ekleyin.")
    with get_connection() as conn:
        sale_id = conn.execute(
            "INSERT INTO sales (customer_id, sale_date, notes) VALUES (?, ?, ?)",
            (customer_id, _to_iso(sale_date), notes.strip()),
        ).lastrowid
        for item in items:
            product = conn.execute("SELECT * FROM products WHERE id = ?", (item["product_id"],)).fetchone()
            if product is None:
                raise ValueError("Urun bulunamadi.")
            quantity = float(item["quantity"])
            unit_price = float(item["unit_price"])
            new_stock = float(product["stock_quantity"]) - quantity
            if new_stock < 0:
                raise ValueError(f"{product['name']} icin negatif stok olusur. Mevcut stok: {product['stock_quantity']}")
            total_amount = quantity * unit_price
            total_cost = quantity * float(product["cost_price"])
            conn.execute(
                """
                INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, cost_price, total_amount, total_cost)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (sale_id, product["id"], quantity, unit_price, product["cost_price"], total_amount, total_cost),
            )
            conn.execute("UPDATE products SET stock_quantity = ? WHERE id = ?", (new_stock, product["id"]))
        return int(sale_id)


def get_sales_summary() -> pd.DataFrame:
    return fetch_df(
        """
        SELECT s.id, s.sale_date, c.name AS customer, s.notes,
               ROUND(SUM(si.total_amount), 2) AS total_amount,
               ROUND(SUM(si.total_cost), 2) AS total_cost,
               ROUND(SUM(si.total_amount - si.total_cost), 2) AS gross_profit
        FROM sales s
        JOIN customers c ON c.id = s.customer_id
        JOIN sale_items si ON si.sale_id = s.id
        GROUP BY s.id
        ORDER BY s.sale_date DESC, s.id DESC
        """
    )


def get_sale_items(sale_id: int) -> pd.DataFrame:
    return fetch_df(
        """
        SELECT si.*, p.name AS product_name, p.unit
        FROM sale_items si
        JOIN products p ON p.id = si.product_id
        WHERE si.sale_id = ?
        ORDER BY si.id
        """,
        (sale_id,),
    )


def delete_sale(sale_id: int) -> None:
    with get_connection() as conn:
        items = conn.execute("SELECT product_id, quantity FROM sale_items WHERE sale_id = ?", (sale_id,)).fetchall()
        for item in items:
            conn.execute(
                "UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?",
                (item["quantity"], item["product_id"]),
            )
        conn.execute("DELETE FROM sales WHERE id = ?", (sale_id,))


def replace_sale(sale_id: int, customer_id: int, sale_date: date, items: list[dict], notes: str = "") -> None:
    with get_connection() as conn:
        old_items = conn.execute("SELECT product_id, quantity FROM sale_items WHERE sale_id = ?", (sale_id,)).fetchall()
        for item in old_items:
            conn.execute(
                "UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?",
                (item["quantity"], item["product_id"]),
            )
        conn.execute("DELETE FROM sale_items WHERE sale_id = ?", (sale_id,))
        conn.execute(
            "UPDATE sales SET customer_id = ?, sale_date = ?, notes = ? WHERE id = ?",
            (customer_id, _to_iso(sale_date), notes.strip(), sale_id),
        )
        for item in items:
            product = conn.execute("SELECT * FROM products WHERE id = ?", (item["product_id"],)).fetchone()
            quantity = float(item["quantity"])
            unit_price = float(item["unit_price"])
            new_stock = float(product["stock_quantity"]) - quantity
            if new_stock < 0:
                raise ValueError(f"{product['name']} icin negatif stok olusur. Mevcut stok: {product['stock_quantity']}")
            total_amount = quantity * unit_price
            total_cost = quantity * float(product["cost_price"])
            conn.execute(
                """
                INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, cost_price, total_amount, total_cost)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (sale_id, product["id"], quantity, unit_price, product["cost_price"], total_amount, total_cost),
            )
            conn.execute("UPDATE products SET stock_quantity = ? WHERE id = ?", (new_stock, product["id"]))


def add_expense(expense_date: date, category: str, description: str, amount: float) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO expenses (expense_date, category, description, amount) VALUES (?, ?, ?, ?)",
            (_to_iso(expense_date), category, description.strip(), amount),
        )


def update_expense(expense_id: int, expense_date: date, category: str, description: str, amount: float) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE expenses SET expense_date = ?, category = ?, description = ?, amount = ? WHERE id = ?",
            (_to_iso(expense_date), category, description.strip(), amount, expense_id),
        )


def delete_expense(expense_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))


def get_expenses() -> pd.DataFrame:
    return fetch_df("SELECT * FROM expenses ORDER BY expense_date DESC, id DESC")


def save_invoice(customer_id: int, start_date: date, end_date: date, total_amount: float, file_name: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO invoices (customer_id, start_date, end_date, invoice_date, total_amount, file_name)
            VALUES (?, ?, ?, date('now'), ?, ?)
            """,
            (customer_id, _to_iso(start_date), _to_iso(end_date), total_amount, file_name),
        )
