import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).with_name("warehouse.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                category TEXT NOT NULL,
                cost_price REAL NOT NULL CHECK(cost_price >= 0),
                sale_price REAL NOT NULL CHECK(sale_price >= 0),
                stock_quantity REAL NOT NULL DEFAULT 0,
                unit TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                address TEXT,
                phone TEXT,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                sale_date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity REAL NOT NULL CHECK(quantity > 0),
                unit_price REAL NOT NULL CHECK(unit_price >= 0),
                cost_price REAL NOT NULL CHECK(cost_price >= 0),
                total_amount REAL NOT NULL CHECK(total_amount >= 0),
                total_cost REAL NOT NULL CHECK(total_cost >= 0),
                FOREIGN KEY(sale_id) REFERENCES sales(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_date TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL CHECK(amount >= 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cost_date TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL CHECK(amount >= 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                invoice_date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                file_name TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE CASCADE
            );
            """
        )


def seed_demo_customers() -> None:
    demo_customers = [
        ("Union Square Fruit Stand", "E 17th St & Broadway, New York, NY", "(212) 555-0141", "Morning delivery preferred."),
        ("Canal Street Produce Cart", "Canal St & Lafayette St, New York, NY", "(212) 555-0188", "Needs mixed fruit boxes."),
        ("Brooklyn Market Stall", "Flatbush Ave, Brooklyn, NY", "(718) 555-0119", "Weekend volume is high."),
    ]
    with get_connection() as conn:
        existing = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        if existing == 0:
            conn.executemany(
                "INSERT INTO customers (name, address, phone, notes) VALUES (?, ?, ?, ?)",
                demo_customers,
            )
