from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Product:
    name: str
    category: str
    cost_price: float
    sale_price: float
    stock_quantity: float
    unit: str
    id: Optional[int] = None


@dataclass
class Customer:
    name: str
    address: str
    phone: str
    notes: str = ""
    id: Optional[int] = None


@dataclass
class SaleItem:
    product_id: int
    quantity: float
    unit_price: float
    cost_price: float
    total_amount: float
    total_cost: float
    id: Optional[int] = None
    sale_id: Optional[int] = None


@dataclass
class Expense:
    expense_date: date
    category: str
    description: str
    amount: float
    id: Optional[int] = None
