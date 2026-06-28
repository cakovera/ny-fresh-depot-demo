from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from database import init_db, seed_demo_customers
from invoice import create_invoice_pdf, invoice_items
from reports import (
    customer_profit_report,
    dashboard_metrics,
    date_range_for_filter,
    expenses_report,
    product_profit_report,
    sales_report,
    totals_report,
)
from services import (
    EXPENSE_CATEGORIES,
    UNITS,
    add_customer,
    add_expense,
    add_product,
    create_sale,
    delete_customer,
    delete_expense,
    delete_product,
    delete_sale,
    get_customers,
    get_expenses,
    get_products,
    get_sale_items,
    get_sales_summary,
    replace_sale,
    update_customer,
    update_expense,
    update_product,
)


st.set_page_config(page_title="NY Fresh Depot Inventory", page_icon="NY", layout="wide")
init_db()
seed_demo_customers()


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --primary: #256f46;
            --ink: #17231b;
            --muted: #65736b;
            --line: #dfe8e1;
        }
        .stApp {
            background: #f7faf7;
            color: var(--ink);
        }
        [data-testid="stSidebar"] {
            background: #183823;
        }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span {
            color: #eef8f0 !important;
        }
        [data-testid="stSidebar"] .stRadio label {
            border-radius: 8px;
            padding: 4px 8px;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] label,
        [data-testid="stSidebar"] [data-baseweb="select"] span,
        [data-testid="stSidebar"] [data-baseweb="select"] div {
            color: #17231b !important;
        }
        h1, h2, h3 {
            letter-spacing: 0;
            color: var(--ink);
        }
        [data-testid="stAppViewContainer"] label,
        [data-testid="stAppViewContainer"] label span,
        [data-testid="stAppViewContainer"] .stTextInput label,
        [data-testid="stAppViewContainer"] .stNumberInput label,
        [data-testid="stAppViewContainer"] .stSelectbox label,
        [data-testid="stAppViewContainer"] .stDateInput label,
        [data-testid="stAppViewContainer"] .stTextArea label {
            color: #17231b !important;
            opacity: 1 !important;
        }
        .app-header {
            padding: 18px 20px;
            border: 1px solid var(--line);
            border-left: 7px solid var(--primary);
            border-radius: 8px;
            background: #ffffff;
            margin-bottom: 18px;
        }
        .app-header h1 {
            margin: 0 0 4px 0;
            font-size: 30px;
            line-height: 1.15;
        }
        .app-header p {
            margin: 0;
            color: var(--muted);
        }
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 14px 16px;
        }
        [data-testid="stMetric"] *,
        [data-testid="stMetricLabel"] *,
        [data-testid="stMetricValue"] * {
            color: #17231b !important;
            opacity: 1 !important;
        }
        .stButton > button, .stDownloadButton > button {
            border-radius: 7px;
            border: 1px solid var(--primary);
            font-weight: 650;
        }
        div[data-testid="stExpander"] {
            border: 1px solid var(--line);
            border-radius: 8px;
            background: #ffffff;
        }
        div[data-testid="stExpander"] details,
        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] summary * {
            background: #ffffff !important;
            color: #17231b !important;
            opacity: 1 !important;
        }
        div[data-testid="stExpander"] label,
        div[data-testid="stExpander"] label *,
        div[data-testid="stExpander"] p,
        div[data-testid="stExpander"] span {
            color: #17231b !important;
            opacity: 1 !important;
        }
        div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {
            border: 1px solid var(--line);
            border-radius: 8px;
            overflow: hidden;
            background: #ffffff;
        }
        input, textarea {
            background: #ffffff !important;
            color: #17231b !important;
        }
        [data-baseweb="input"] > div,
        [data-baseweb="textarea"] > div,
        [data-baseweb="select"] > div {
            background: #ffffff !important;
            color: #17231b !important;
            border-color: #c9d8cf !important;
        }
        [data-baseweb="input"] *,
        [data-baseweb="textarea"] *,
        [data-baseweb="select"] * {
            color: #17231b !important;
            opacity: 1 !important;
        }
        [data-baseweb="popover"] * {
            background: #ffffff !important;
            color: #17231b !important;
            opacity: 1 !important;
        }
        div[data-testid="stForm"] {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 12px;
        }
        div[data-testid="stForm"] *:not(button):not(svg):not(path) {
            color: #17231b !important;
            opacity: 1 !important;
        }
        @media (max-width: 640px) {
            .app-header {
                padding: 14px 14px;
                margin-bottom: 14px;
            }
            .app-header h1 {
                font-size: 22px;
            }
            .app-header p {
                font-size: 14px;
            }
            [data-testid="stMetric"] {
                padding: 12px 12px;
            }
            [data-testid="stMetricLabel"] p,
            [data-testid="stMetricValue"] div {
                font-size: 15px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


apply_theme()


LANGUAGES = {
    "Turkce": "tr",
    "English": "en",
}

TEXT = {
    "tr": {
        "menu_label": "Sayfa",
        "language": "Dil",
        "sidebar_caption": "Depo Operasyonlari",
        "dashboard": "Dashboard",
        "products": "Urunler",
        "customers": "Musteriler",
        "sales_delivery": "Satis / Teslimat",
        "expenses": "Masraflar",
        "reports": "Raporlar",
        "invoice": "Fatura Olustur",
        "products_subtitle": "Stok, maliyet ve satis fiyatlarini tek ekrandan yonetin.",
        "customers_subtitle": "Manav tezgahlari, adresler ve teslimat notlari.",
        "sales_subtitle": "Teslimatlari kaydedin, stok otomatik dussun.",
        "expenses_subtitle": "Nakliye, iscilik, benzin ve depo giderlerini kar hesabina dahil edin.",
        "reports_subtitle": "Satis, maliyet, masraf ve net kar analizleri.",
        "dashboard_subtitle": "Gunluk performans, stok degeri ve en iyi musteri/urun sinyalleri.",
        "invoice_subtitle": "Satislardan fatura taslagi cekin, satirlari ve PDF bilgilerini duzenleyin.",
        "add_product": "Yeni urun ekle",
        "product_name": "Urun adi",
        "category": "Kategori",
        "unit": "Birim",
        "cost_price": "Alis maliyeti",
        "sale_price": "Satis fiyati",
        "stock_quantity": "Stok miktari",
        "add_product_btn": "Urun ekle",
        "product_required": "Urun adi zorunludur.",
        "product_added": "Urun eklendi.",
        "product_list": "Urun listesi",
        "edit_delete_product": "Urun duzenle / sil",
        "select_product": "Urun sec",
        "save": "Kaydet",
        "delete": "Sil",
        "product_updated": "Urun guncellendi.",
        "product_deleted": "Urun silindi.",
        "add_customer": "Yeni musteri ekle",
        "customer_name": "Musteri adi",
        "phone": "Telefon",
        "address": "Adres",
        "notes": "Notlar",
        "add_customer_btn": "Musteri ekle",
        "customer_required": "Musteri adi zorunludur.",
        "customer_added": "Musteri eklendi.",
        "edit_delete_customer": "Musteri duzenle / sil",
        "select_customer": "Musteri sec",
        "customer_updated": "Musteri guncellendi.",
        "customer_deleted": "Musteri silindi.",
        "add_products_first": "Once urun ekleyin.",
        "line_count": "Kalem sayisi",
        "product_line": "Urun",
        "quantity": "Miktar",
        "unit_price": "Birim fiyat",
        "total": "Toplam",
        "need_customer_product": "Satis kaydi icin en az bir musteri ve bir urun gerekir.",
        "new_sale": "Yeni satis kaydi",
        "customer": "Musteri",
        "date": "Tarih",
        "note": "Not",
        "save_sale": "Satisi kaydet",
        "sale_saved": "Satis kaydedildi ve stoktan dusuldu.",
        "sales_records": "Satis kayitlari",
        "edit_delete_sale": "Satis duzenle / sil",
        "select_sale": "Satis sec",
        "current_items": "Mevcut kalemler",
        "update_sale": "Satisi guncelle",
        "sale_updated": "Satis guncellendi.",
        "delete_sale": "Satisi sil",
        "sale_deleted": "Satis silindi ve stok geri eklendi.",
        "amount": "Tutar",
        "description": "Aciklama",
        "add_expense_btn": "Masraf ekle",
        "expense_added": "Masraf eklendi.",
        "edit_delete_expense": "Masraf duzenle / sil",
        "select_expense": "Masraf sec",
        "expense_updated": "Masraf guncellendi.",
        "expense_deleted": "Masraf silindi.",
        "filter": "Filtre",
        "daily": "Gunluk",
        "weekly": "Haftalik",
        "monthly": "Aylik",
        "custom": "Ozel",
        "start": "Baslangic",
        "end": "Bitis",
        "total_sales": "Toplam satis",
        "total_cost": "Toplam maliyet",
        "net_profit": "Net kar",
        "all_sales": "Tum satislar",
        "by_customer": "Musteri bazinda",
        "by_product": "Urun bazinda",
        "today_sales": "Bugunku satis",
        "today_profit": "Bugunku kar",
        "stock_value": "Toplam stok degeri",
        "inventory_cost_value": "Toplam urun maliyeti",
        "inventory_sales_value": "Toplam satis degeri",
        "inventory_potential_profit": "Potansiyel kar",
        "total_units": "Toplam stok adedi",
        "top_products": "En cok satilan urunler",
        "top_customers": "En cok alisveris yapan musteriler",
        "invoice_no_sales": "Bu musteri ve tarih araligi icin satis bulunamadi.",
        "invoice_info": "Fatura bilgileri",
        "invoice_settings": "Isletme ve fatura ayarlari",
        "business_name": "Isletme adi",
        "invoice_title": "Fatura basligi",
        "invoice_number": "Fatura no",
        "invoice_date": "Fatura tarihi",
        "due_date": "Vade tarihi",
        "accent_color": "PDF vurgu rengi",
        "business_address": "Isletme adresi",
        "business_phone": "Isletme telefonu",
        "business_email": "Isletme email",
        "invoice_items": "Fatura kalemleri",
        "discount": "Indirim",
        "delivery_fee": "Teslimat / islem ucreti",
        "tax_rate": "Vergi orani (%)",
        "payment_terms": "Odeme sartlari",
        "invoice_note": "Fatura notu",
        "subtotal": "Ara toplam",
        "grand_total": "Genel toplam",
        "create_pdf": "Profesyonel PDF fatura olustur",
        "invoice_created": "Fatura olusturuldu. Genel toplam:",
        "download_pdf": "PDF indir",
    },
    "en": {
        "menu_label": "Page",
        "language": "Language",
        "sidebar_caption": "Warehouse Operations",
        "dashboard": "Dashboard",
        "products": "Products",
        "customers": "Customers",
        "sales_delivery": "Sales / Delivery",
        "expenses": "Expenses",
        "reports": "Reports",
        "invoice": "Create Invoice",
        "products_subtitle": "Manage stock, cost, and sales prices from one screen.",
        "customers_subtitle": "Produce stand customers, addresses, and delivery notes.",
        "sales_subtitle": "Record deliveries and deduct stock automatically.",
        "expenses_subtitle": "Include freight, labor, gas, rent, and warehouse costs in profit.",
        "reports_subtitle": "Sales, cost, expense, and net profit analysis.",
        "dashboard_subtitle": "Daily performance, stock value, and top customer/product signals.",
        "invoice_subtitle": "Pull invoice drafts from sales, then edit lines and PDF details.",
        "add_product": "Add new product",
        "product_name": "Product name",
        "category": "Category",
        "unit": "Unit",
        "cost_price": "Cost price",
        "sale_price": "Sales price",
        "stock_quantity": "Stock quantity",
        "add_product_btn": "Add product",
        "product_required": "Product name is required.",
        "product_added": "Product added.",
        "product_list": "Product list",
        "edit_delete_product": "Edit / delete product",
        "select_product": "Select product",
        "save": "Save",
        "delete": "Delete",
        "product_updated": "Product updated.",
        "product_deleted": "Product deleted.",
        "add_customer": "Add new customer",
        "customer_name": "Customer name",
        "phone": "Phone",
        "address": "Address",
        "notes": "Notes",
        "add_customer_btn": "Add customer",
        "customer_required": "Customer name is required.",
        "customer_added": "Customer added.",
        "edit_delete_customer": "Edit / delete customer",
        "select_customer": "Select customer",
        "customer_updated": "Customer updated.",
        "customer_deleted": "Customer deleted.",
        "add_products_first": "Add products first.",
        "line_count": "Line count",
        "product_line": "Product",
        "quantity": "Quantity",
        "unit_price": "Unit price",
        "total": "Total",
        "need_customer_product": "At least one customer and one product are required for a sale.",
        "new_sale": "New sale record",
        "customer": "Customer",
        "date": "Date",
        "note": "Note",
        "save_sale": "Save sale",
        "sale_saved": "Sale saved and deducted from stock.",
        "sales_records": "Sales records",
        "edit_delete_sale": "Edit / delete sale",
        "select_sale": "Select sale",
        "current_items": "Current items",
        "update_sale": "Update sale",
        "sale_updated": "Sale updated.",
        "delete_sale": "Delete sale",
        "sale_deleted": "Sale deleted and stock restored.",
        "amount": "Amount",
        "description": "Description",
        "add_expense_btn": "Add expense",
        "expense_added": "Expense added.",
        "edit_delete_expense": "Edit / delete expense",
        "select_expense": "Select expense",
        "expense_updated": "Expense updated.",
        "expense_deleted": "Expense deleted.",
        "filter": "Filter",
        "daily": "Daily",
        "weekly": "Weekly",
        "monthly": "Monthly",
        "custom": "Custom",
        "start": "Start",
        "end": "End",
        "total_sales": "Total sales",
        "total_cost": "Total cost",
        "net_profit": "Net profit",
        "all_sales": "All sales",
        "by_customer": "By customer",
        "by_product": "By product",
        "today_sales": "Today's sales",
        "today_profit": "Today's profit",
        "stock_value": "Total stock value",
        "inventory_cost_value": "Total inventory cost",
        "inventory_sales_value": "Total sales value",
        "inventory_potential_profit": "Potential profit",
        "total_units": "Total stock units",
        "top_products": "Top selling products",
        "top_customers": "Top customers",
        "invoice_no_sales": "No sales found for this customer and date range.",
        "invoice_info": "Invoice information",
        "invoice_settings": "Business and invoice settings",
        "business_name": "Business name",
        "invoice_title": "Invoice title",
        "invoice_number": "Invoice no",
        "invoice_date": "Invoice date",
        "due_date": "Due date",
        "accent_color": "PDF accent color",
        "business_address": "Business address",
        "business_phone": "Business phone",
        "business_email": "Business email",
        "invoice_items": "Invoice items",
        "discount": "Discount",
        "delivery_fee": "Delivery / handling fee",
        "tax_rate": "Tax rate (%)",
        "payment_terms": "Payment terms",
        "invoice_note": "Invoice note",
        "subtotal": "Subtotal",
        "grand_total": "Grand total",
        "create_pdf": "Create professional PDF invoice",
        "invoice_created": "Invoice created. Grand total:",
        "download_pdf": "Download PDF",
    },
}


def lang_code() -> str:
    return LANGUAGES.get(st.session_state.get("language", "Turkce"), "tr")


def t(key: str) -> str:
    code = lang_code()
    return TEXT.get(code, TEXT["tr"]).get(key, TEXT["tr"].get(key, key))


def money(value: float) -> str:
    return f"${value:,.2f}"


def show_df(df: pd.DataFrame) -> None:
    st.dataframe(df, use_container_width=True, hide_index=True)


def page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="app-header">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def products_page() -> None:
    page_header(t("products"), t("products_subtitle"))
    products = get_products()

    if not products.empty:
        inventory_cost = float((products["cost_price"] * products["stock_quantity"]).sum())
        inventory_sales = float((products["sale_price"] * products["stock_quantity"]).sum())
        inventory_profit = inventory_sales - inventory_cost
        total_units = float(products["stock_quantity"].sum())
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(t("inventory_cost_value"), money(inventory_cost))
        m2.metric(t("inventory_sales_value"), money(inventory_sales))
        m3.metric(t("inventory_potential_profit"), money(inventory_profit))
        m4.metric(t("total_units"), f"{total_units:,.2f}")

    with st.expander(t("add_product"), expanded=True):
        with st.form("add_product"):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input(t("product_name"))
            category = c2.text_input(t("category"), value="Produce")
            unit = c3.selectbox(t("unit"), UNITS)
            c4, c5, c6 = st.columns(3)
            cost = c4.number_input(t("cost_price"), min_value=0.0, step=0.25)
            price = c5.number_input(t("sale_price"), min_value=0.0, step=0.25)
            stock = c6.number_input(t("stock_quantity"), min_value=0.0, step=1.0)
            if st.form_submit_button(t("add_product_btn"), type="primary"):
                try:
                    if not name.strip():
                        raise ValueError(t("product_required"))
                    add_product(name, category, cost, price, stock, unit)
                    st.success(t("product_added"))
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    st.subheader(t("product_list"))
    show_df(products)

    if not products.empty:
        st.subheader(t("edit_delete_product"))
        selected_id = st.selectbox(t("select_product"), products["id"], format_func=lambda x: products.loc[products["id"] == x, "name"].iloc[0])
        row = products.loc[products["id"] == selected_id].iloc[0]
        with st.form("edit_product"):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input(t("product_name"), value=row["name"])
            category = c2.text_input(t("category"), value=row["category"])
            unit = c3.selectbox(t("unit"), UNITS, index=UNITS.index(row["unit"]) if row["unit"] in UNITS else 0)
            c4, c5, c6 = st.columns(3)
            cost = c4.number_input(t("cost_price"), min_value=0.0, value=float(row["cost_price"]), step=0.25)
            price = c5.number_input(t("sale_price"), min_value=0.0, value=float(row["sale_price"]), step=0.25)
            stock = c6.number_input(t("stock_quantity"), min_value=0.0, value=float(row["stock_quantity"]), step=1.0)
            save, delete = st.columns(2)
            if save.form_submit_button(t("save")):
                try:
                    update_product(int(selected_id), name, category, cost, price, stock, unit)
                    st.success(t("product_updated"))
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
            if delete.form_submit_button(t("delete")):
                try:
                    delete_product(int(selected_id))
                    st.success(t("product_deleted"))
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))


def customers_page() -> None:
    page_header(t("customers"), t("customers_subtitle"))
    customers = get_customers()
    with st.expander(t("add_customer"), expanded=True):
        with st.form("add_customer"):
            c1, c2 = st.columns(2)
            name = c1.text_input(t("customer_name"))
            phone = c2.text_input(t("phone"))
            address = st.text_input(t("address"))
            notes = st.text_area(t("notes"))
            if st.form_submit_button(t("add_customer_btn"), type="primary"):
                try:
                    if not name.strip():
                        raise ValueError(t("customer_required"))
                    add_customer(name, address, phone, notes)
                    st.success(t("customer_added"))
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    show_df(customers)
    if not customers.empty:
        st.subheader(t("edit_delete_customer"))
        selected_id = st.selectbox(t("select_customer"), customers["id"], format_func=lambda x: customers.loc[customers["id"] == x, "name"].iloc[0])
        row = customers.loc[customers["id"] == selected_id].iloc[0]
        with st.form("edit_customer"):
            c1, c2 = st.columns(2)
            name = c1.text_input(t("customer_name"), value=row["name"])
            phone = c2.text_input(t("phone"), value=row["phone"] or "")
            address = st.text_input(t("address"), value=row["address"] or "")
            notes = st.text_area(t("notes"), value=row["notes"] or "")
            save, delete = st.columns(2)
            if save.form_submit_button(t("save")):
                try:
                    update_customer(int(selected_id), name, address, phone, notes)
                    st.success(t("customer_updated"))
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
            if delete.form_submit_button(t("delete")):
                delete_customer(int(selected_id))
                st.success(t("customer_deleted"))
                st.rerun()


def build_sale_items(products: pd.DataFrame, prefix: str, defaults: pd.DataFrame | None = None) -> list[dict]:
    if products.empty:
        st.warning(t("add_products_first"))
        return []
    count = st.number_input(t("line_count"), min_value=1, max_value=20, value=max(1, len(defaults) if defaults is not None else 1), key=f"{prefix}_count")
    items = []
    for index in range(int(count)):
        default = defaults.iloc[index] if defaults is not None and index < len(defaults) else None
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        product_ids = products["id"].tolist()
        default_product_id = int(default["product_id"]) if default is not None else product_ids[0]
        product_id = c1.selectbox(
            f"{t('product_line')} {index + 1}",
            product_ids,
            index=product_ids.index(default_product_id) if default_product_id in product_ids else 0,
            format_func=lambda x: products.loc[products["id"] == x, "name"].iloc[0],
            key=f"{prefix}_product_{index}",
        )
        product = products.loc[products["id"] == product_id].iloc[0]
        quantity = c2.number_input(t("quantity"), min_value=0.01, value=float(default["quantity"]) if default is not None else 1.0, step=1.0, key=f"{prefix}_qty_{index}")
        unit_price = c3.number_input(t("unit_price"), min_value=0.0, value=float(default["unit_price"]) if default is not None else float(product["sale_price"]), step=0.25, key=f"{prefix}_price_{index}")
        c4.metric(t("total"), money(quantity * unit_price))
        items.append({"product_id": int(product_id), "quantity": quantity, "unit_price": unit_price})
    return items


def sales_page() -> None:
    page_header(t("sales_delivery"), t("sales_subtitle"))
    customers = get_customers()
    products = get_products()
    if customers.empty or products.empty:
        st.info(t("need_customer_product"))
        return

    with st.expander(t("new_sale"), expanded=True):
        with st.form("new_sale"):
            c1, c2 = st.columns(2)
            customer_id = c1.selectbox(t("customer"), customers["id"], format_func=lambda x: customers.loc[customers["id"] == x, "name"].iloc[0])
            sale_date = c2.date_input(t("date"), value=date.today())
            notes = st.text_input(t("note"))
            items = build_sale_items(products, "new_sale")
            if st.form_submit_button(t("save_sale"), type="primary"):
                try:
                    create_sale(int(customer_id), sale_date, items, notes)
                    st.success(t("sale_saved"))
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    st.subheader(t("sales_records"))
    sales = get_sales_summary()
    show_df(sales)

    if not sales.empty:
        st.subheader(t("edit_delete_sale"))
        sale_id = st.selectbox(t("select_sale"), sales["id"], format_func=lambda x: f"#{x} - {sales.loc[sales['id'] == x, 'customer'].iloc[0]}")
        sale_row = sales.loc[sales["id"] == sale_id].iloc[0]
        current_items = get_sale_items(int(sale_id))
        st.caption(t("current_items"))
        show_df(current_items[["product_name", "quantity", "unit", "unit_price", "total_amount"]])
        with st.form("edit_sale"):
            c1, c2 = st.columns(2)
            current_customer_name = sale_row["customer"]
            current_customer_id = int(customers.loc[customers["name"] == current_customer_name, "id"].iloc[0])
            customer_id = c1.selectbox(
                t("customer"),
                customers["id"],
                index=customers["id"].tolist().index(current_customer_id),
                format_func=lambda x: customers.loc[customers["id"] == x, "name"].iloc[0],
                key="edit_customer",
            )
            sale_date = c2.date_input(t("date"), value=pd.to_datetime(sale_row["sale_date"]).date(), key="edit_date")
            notes = st.text_input(t("note"), value=sale_row["notes"] or "")
            items = build_sale_items(products, "edit_sale", current_items)
            save, delete = st.columns(2)
            if save.form_submit_button(t("update_sale")):
                try:
                    replace_sale(int(sale_id), int(customer_id), sale_date, items, notes)
                    st.success(t("sale_updated"))
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
            if delete.form_submit_button(t("delete_sale")):
                delete_sale(int(sale_id))
                st.success(t("sale_deleted"))
                st.rerun()


def expenses_page() -> None:
    page_header(t("expenses"), t("expenses_subtitle"))
    with st.form("add_expense"):
        c1, c2, c3 = st.columns(3)
        expense_date = c1.date_input(t("date"), value=date.today())
        category = c2.selectbox(t("category"), EXPENSE_CATEGORIES)
        amount = c3.number_input(t("amount"), min_value=0.0, step=1.0)
        description = st.text_input(t("description"))
        if st.form_submit_button(t("add_expense_btn"), type="primary"):
            add_expense(expense_date, category, description, amount)
            st.success(t("expense_added"))
            st.rerun()

    expenses = get_expenses()
    show_df(expenses)
    if not expenses.empty:
        st.subheader(t("edit_delete_expense"))
        expense_id = st.selectbox(t("select_expense"), expenses["id"], format_func=lambda x: f"#{x} - {expenses.loc[expenses['id'] == x, 'category'].iloc[0]}")
        row = expenses.loc[expenses["id"] == expense_id].iloc[0]
        with st.form("edit_expense"):
            c1, c2, c3 = st.columns(3)
            expense_date = c1.date_input(t("date"), value=pd.to_datetime(row["expense_date"]).date(), key="expense_date_edit")
            category = c2.selectbox(t("category"), EXPENSE_CATEGORIES, index=EXPENSE_CATEGORIES.index(row["category"]) if row["category"] in EXPENSE_CATEGORIES else 0)
            amount = c3.number_input(t("amount"), min_value=0.0, value=float(row["amount"]), step=1.0)
            description = st.text_input(t("description"), value=row["description"] or "")
            save, delete = st.columns(2)
            if save.form_submit_button(t("save")):
                update_expense(int(expense_id), expense_date, category, description, amount)
                st.success(t("expense_updated"))
                st.rerun()
            if delete.form_submit_button(t("delete")):
                delete_expense(int(expense_id))
                st.success(t("expense_deleted"))
                st.rerun()


def reports_page() -> None:
    page_header(t("reports"), t("reports_subtitle"))
    c1, c2, c3 = st.columns(3)
    period_options = {
        t("daily"): "Gunluk",
        t("weekly"): "Haftalik",
        t("monthly"): "Aylik",
        t("custom"): "Ozel",
    }
    period_label = c1.selectbox(t("filter"), list(period_options.keys()))
    start_default, end_default = date_range_for_filter(period_options[period_label])
    start_date = c2.date_input(t("start"), value=start_default)
    end_date = c3.date_input(t("end"), value=end_default)
    totals = totals_report(start_date, end_date)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(t("total_sales"), money(totals["total_sales"]))
    m2.metric(t("total_cost"), money(totals["total_cost"]))
    m3.metric(t("expenses"), money(totals["total_expenses"]))
    m4.metric(t("net_profit"), money(totals["net_profit"]))

    tabs = st.tabs([t("all_sales"), t("by_customer"), t("by_product"), t("expenses")])
    with tabs[0]:
        show_df(sales_report(start_date, end_date))
    with tabs[1]:
        show_df(customer_profit_report(start_date, end_date))
    with tabs[2]:
        show_df(product_profit_report(start_date, end_date))
    with tabs[3]:
        show_df(expenses_report(start_date, end_date))


def dashboard_page() -> None:
    page_header("NY Fresh Depot Dashboard", t("dashboard_subtitle"))
    metrics = dashboard_metrics()
    c1, c2, c3 = st.columns(3)
    c1.metric(t("today_sales"), money(metrics["today_sales"]))
    c2.metric(t("today_profit"), money(metrics["today_profit"]))
    c3.metric(t("stock_value"), money(metrics["stock_value"]))
    c4, c5 = st.columns(2)
    with c4:
        st.subheader(t("top_products"))
        show_df(metrics["top_products"])
    with c5:
        st.subheader(t("top_customers"))
        show_df(metrics["top_customers"])


def invoice_page() -> None:
    page_header(t("invoice"), t("invoice_subtitle"))
    customers = get_customers()
    if customers.empty:
        st.info(t("add_customer"))
        return

    c1, c2, c3 = st.columns(3)
    customer_id = c1.selectbox(
        t("customer"),
        customers["id"],
        format_func=lambda x: customers.loc[customers["id"] == x, "name"].iloc[0],
    )
    start_date = c2.date_input(t("start"), value=date.today().replace(day=1))
    end_date = c3.date_input(t("end"), value=date.today())
    customer = customers.loc[customers["id"] == customer_id].iloc[0]
    customer_name = customer["name"]

    base_items = invoice_items(int(customer_id), start_date, end_date)
    if base_items.empty:
        st.warning(t("invoice_no_sales"))
        return

    st.subheader(t("invoice_info"))
    with st.expander(t("invoice_settings"), expanded=True):
        c1, c2, c3 = st.columns(3)
        business_name = c1.text_input(t("business_name"), value="NY Fresh Depot")
        invoice_title = c2.text_input(t("invoice_title"), value="INVOICE")
        invoice_number = c3.text_input(t("invoice_number"), value=f"INV-{int(customer_id)}-{start_date:%Y%m%d}-{end_date:%Y%m%d}")
        c4, c5, c6 = st.columns(3)
        invoice_date = c4.date_input(t("invoice_date"), value=date.today())
        due_date = c5.date_input(t("due_date"), value=date.today())
        accent_color = c6.color_picker(t("accent_color"), value="#256f46")
        business_address = st.text_input(t("business_address"), value="Hunts Point Produce Market, Bronx, NY")
        c7, c8 = st.columns(2)
        business_phone = c7.text_input(t("business_phone"), value="(212) 555-0100")
        business_email = c8.text_input(t("business_email"), value="billing@nyfreshdepot.com")

    st.subheader(t("invoice_items"))
    editable_items = base_items[["product", "quantity", "unit", "unit_price", "total"]].copy()
    edited_items = st.data_editor(
        editable_items,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "product": st.column_config.TextColumn(t("product_line"), required=True),
            "quantity": st.column_config.NumberColumn(t("quantity"), min_value=0.0, step=1.0, format="%.2f"),
            "unit": st.column_config.SelectboxColumn(t("unit"), options=UNITS),
            "unit_price": st.column_config.NumberColumn(t("unit_price"), min_value=0.0, step=0.25, format="$%.2f"),
            "total": st.column_config.NumberColumn(t("total"), min_value=0.0, step=0.25, format="$%.2f"),
        },
        key=f"invoice_editor_{customer_id}_{start_date}_{end_date}",
    )
    edited_items["quantity"] = pd.to_numeric(edited_items["quantity"], errors="coerce").fillna(0)
    edited_items["unit_price"] = pd.to_numeric(edited_items["unit_price"], errors="coerce").fillna(0)
    edited_items["total"] = edited_items["quantity"] * edited_items["unit_price"]

    c1, c2, c3 = st.columns(3)
    discount = c1.number_input(t("discount"), min_value=0.0, value=0.0, step=1.0)
    delivery_fee = c2.number_input(t("delivery_fee"), min_value=0.0, value=0.0, step=1.0)
    tax_rate = c3.number_input(t("tax_rate"), min_value=0.0, value=0.0, step=0.25)
    default_terms = "Due on receipt. Please make checks payable to NY Fresh Depot." if lang_code() == "en" else "Teslim alindiginda odenir. Cekleri NY Fresh Depot adina duzenleyiniz."
    default_note = "Thank you for your business." if lang_code() == "en" else "Alisverisiniz icin tesekkur ederiz."
    payment_terms = st.text_input(t("payment_terms"), value=default_terms)
    notes = st.text_area(t("invoice_note"), value=default_note)

    subtotal = float(edited_items["total"].sum())
    tax_base = max(0.0, subtotal - discount + delivery_fee)
    grand_total = tax_base + (tax_base * tax_rate / 100)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(t("subtotal"), money(subtotal))
    m2.metric(t("discount"), money(discount))
    m3.metric(t("delivery_fee"), money(delivery_fee))
    m4.metric(t("grand_total"), money(grand_total))

    invoice_details = {
        "business_name": business_name,
        "business_address": business_address,
        "business_phone": business_phone,
        "business_email": business_email,
        "invoice_title": invoice_title,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "due_date": due_date,
        "accent_color": accent_color,
        "discount": discount,
        "delivery_fee": delivery_fee,
        "tax_rate": tax_rate,
        "payment_terms": payment_terms,
        "notes": notes,
        "customer_address": customer["address"] or "",
        "customer_phone": customer["phone"] or "",
    }

    if st.button(t("create_pdf"), type="primary"):
        try:
            pdf_bytes, total = create_invoice_pdf(
                int(customer_id),
                customer_name,
                start_date,
                end_date,
                invoice_details=invoice_details,
                edited_items=edited_items,
            )
            st.success(f"{t('invoice_created')} {money(total)}")
            st.download_button(
                t("download_pdf"),
                data=pdf_bytes,
                file_name=f"{invoice_number}.pdf",
                mime="application/pdf",
            )
        except ValueError as exc:
            st.error(str(exc))


st.sidebar.title("NY Fresh Depot")
st.sidebar.selectbox(t("language"), list(LANGUAGES.keys()), key="language")
st.sidebar.caption(t("sidebar_caption"))

PAGE_DEFS = [
    ("dashboard", dashboard_page),
    ("products", products_page),
    ("customers", customers_page),
    ("sales_delivery", sales_page),
    ("expenses", expenses_page),
    ("reports", reports_page),
    ("invoice", invoice_page),
]
PAGES = {t(label_key): page_func for label_key, page_func in PAGE_DEFS}
choice = st.sidebar.radio(t("menu_label"), list(PAGES.keys()))
PAGES[choice]()
