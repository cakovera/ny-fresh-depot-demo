from __future__ import annotations

from datetime import date
from io import BytesIO

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from services import fetch_df, save_invoice


BUSINESS_NAME = "NY Fresh Depot"


def invoice_items(customer_id: int, start_date: date, end_date: date):
    return fetch_df(
        """
        SELECT p.name AS product, p.unit,
               SUM(si.quantity) AS quantity,
               si.unit_price,
               SUM(si.total_amount) AS total
        FROM sale_items si
        JOIN sales s ON s.id = si.sale_id
        JOIN products p ON p.id = si.product_id
        WHERE s.customer_id = ?
          AND date(s.sale_date) BETWEEN date(?) AND date(?)
        GROUP BY p.id, si.unit_price
        ORDER BY p.name
        """,
        (customer_id, start_date.isoformat(), end_date.isoformat()),
    )


def _money(value: float) -> str:
    return f"${value:,.2f}"


def create_invoice_pdf(
    customer_id: int,
    customer_name: str,
    start_date: date,
    end_date: date,
    invoice_details: dict | None = None,
    edited_items: pd.DataFrame | None = None,
) -> tuple[bytes, float]:
    invoice_details = invoice_details or {}
    items = edited_items.copy() if edited_items is not None else invoice_items(customer_id, start_date, end_date)
    if items.empty:
        raise ValueError("Secilen tarih araliginda faturalandirilacak satis yok.")

    for column in ["product", "quantity", "unit", "unit_price", "total"]:
        if column not in items.columns:
            raise ValueError(f"Fatura kalemlerinde eksik kolon: {column}")

    items = items[items["product"].astype(str).str.strip() != ""].copy()
    if items.empty:
        raise ValueError("Faturada en az bir kalem olmalidir.")

    items["quantity"] = pd.to_numeric(items["quantity"], errors="coerce").fillna(0)
    items["unit_price"] = pd.to_numeric(items["unit_price"], errors="coerce").fillna(0)
    items["total"] = pd.to_numeric(items["total"], errors="coerce").fillna(items["quantity"] * items["unit_price"])
    subtotal = float(items["total"].sum())
    discount = max(0.0, float(invoice_details.get("discount", 0) or 0))
    delivery_fee = max(0.0, float(invoice_details.get("delivery_fee", 0) or 0))
    tax_rate = max(0.0, float(invoice_details.get("tax_rate", 0) or 0))
    taxable_base = max(0.0, subtotal - discount + delivery_fee)
    tax_amount = taxable_base * tax_rate / 100
    total = taxable_base + tax_amount

    accent = invoice_details.get("accent_color", "#256f46") or "#256f46"
    business_name = invoice_details.get("business_name") or BUSINESS_NAME
    invoice_title = invoice_details.get("invoice_title") or "INVOICE"
    invoice_number = invoice_details.get("invoice_number") or f"INV-{customer_id}-{start_date:%Y%m%d}-{end_date:%Y%m%d}"
    invoice_date = invoice_details.get("invoice_date") or date.today()
    due_date = invoice_details.get("due_date") or invoice_date

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, rightMargin=40, leftMargin=40, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Muted", parent=styles["Normal"], textColor=colors.HexColor("#5f6b7a"), leading=14))
    styles.add(ParagraphStyle(name="InvoiceTitle", parent=styles["Title"], fontSize=26, textColor=colors.HexColor(accent), alignment=2))
    styles.add(ParagraphStyle(name="SmallRight", parent=styles["Normal"], alignment=2, leading=14))

    business_lines = [
        f"<b>{business_name}</b>",
        invoice_details.get("business_address", "Hunts Point Produce Market, Bronx, NY"),
        invoice_details.get("business_phone", "(212) 555-0100"),
        invoice_details.get("business_email", "billing@nyfreshdepot.com"),
    ]
    bill_to_lines = [
        "<b>Bill To</b>",
        customer_name,
        invoice_details.get("customer_address", ""),
        invoice_details.get("customer_phone", ""),
    ]
    meta_lines = [
        f"<b>{invoice_title}</b>",
        f"Invoice No: {invoice_number}",
        f"Invoice Date: {invoice_date}",
        f"Due Date: {due_date}",
        f"Sales Period: {start_date.isoformat()} to {end_date.isoformat()}",
    ]

    header = Table(
        [
            [
                Paragraph("<br/>".join([line for line in business_lines if line]), styles["Normal"]),
                Paragraph("<br/>".join(meta_lines), styles["SmallRight"]),
            ]
        ],
        colWidths=[3.55 * inch, 3.25 * inch],
    )
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))

    story = [header, Spacer(1, 10), HRFlowable(width="100%", color=colors.HexColor(accent), thickness=1.3), Spacer(1, 16)]
    story.append(Paragraph("<br/>".join([line for line in bill_to_lines if line]), styles["Normal"]))
    story.append(Spacer(1, 16))

    table_data = [["Product", "Qty", "Unit", "Unit Price", "Total"]]
    for _, row in items.iterrows():
        table_data.append(
            [
                str(row["product"]),
                f"{float(row['quantity']):,.2f}",
                str(row["unit"]),
                _money(float(row["unit_price"])),
                _money(float(row["total"])),
            ]
        )

    table = Table(table_data, colWidths=[220, 70, 60, 90, 90])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(accent)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor(accent)),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7faf7")]),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d9e2dc")),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 14))

    totals_data = [
        ["Subtotal", _money(subtotal)],
        ["Discount", f"-{_money(discount)}"],
        ["Delivery / Handling", _money(delivery_fee)],
        [f"Tax ({tax_rate:.2f}%)", _money(tax_amount)],
        ["Grand Total", _money(total)],
    ]
    totals_table = Table(totals_data, colWidths=[130, 110], hAlign="RIGHT")
    totals_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -2), 0.25, colors.HexColor("#d9e2dc")),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor(accent)),
                ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(totals_table)

    notes = invoice_details.get("notes", "")
    payment_terms = invoice_details.get("payment_terms", "")
    if notes or payment_terms:
        story.append(Spacer(1, 18))
    if payment_terms:
        story.append(Paragraph(f"<b>Payment Terms:</b> {payment_terms}", styles["Muted"]))
    if notes:
        story.append(Paragraph(f"<b>Notes:</b> {notes}", styles["Muted"]))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    file_name = f"{invoice_number}.pdf"
    save_invoice(customer_id, start_date, end_date, total, file_name)
    return pdf_bytes, total
