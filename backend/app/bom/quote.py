"""Client-facing quote document derived from the parametric model.

Serializes the deterministic cost breakdown (app.bom.costing.derive_cost)
into a self-contained RTL HTML document that the browser can print or save as
PDF. No PDF dependency, no separate pricing source — the numbers are the same
pure-function output the /cost endpoint returns.

This is a presentation layer only; it never writes back into the model.
"""

from __future__ import annotations

from html import escape

from app.bom.costing import derive_cost
from app.design.parametric import DesignModel

FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"


def _fa(n: float | int | None) -> str:
    if n is None:
        return "—"
    return str(round(n)).translate(str.maketrans("0123456789", FA_DIGITS))


def _money(n: float | None) -> str:
    if not n:
        return "۰"
    return str(round(n)).translate(str.maketrans("0123456789", FA_DIGITS))


def quote_html(design: DesignModel, cost: dict) -> str:
    """Build a printable RTL quote page from the derived cost breakdown."""
    c = cost
    rows = [
        ("متریال", c["subtotals"]["materials"]),
        ("یراق‌آلات", c["subtotals"]["hardware"]),
        ("لب‌چسب", c["subtotals"]["edge_banding"]),
        ("اکسسوری", c["subtotals"]["accessories"]),
        ("نیروی کار", c["subtotals"]["labor"]),
        ("لوازم", c["subtotals"]["appliances"]),
        ("صفحه کابینت", c["subtotals"]["countertops"]),
        ("هزینه سربار", c["markup"]["overhead"]),
        ("سود", c["markup"]["margin_amount"]),
        ("مالیات", c["markup"]["tax"]),
        ("هزینه ارسال", c["markup"]["delivery_fee"]),
    ]
    rows_html = "\n".join(
        f"<tr><td>{escape(n)}</td><td class='num'>{_money(v)} تومان</td></tr>"
        for n, v in rows
    )
    room = design.room
    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<title>پیش‌فاکتور طرح</title>
<style>
  body {{ font-family: Tahoma, 'Segoe UI', sans-serif; color: #222; margin: 40px; }}
  h1 {{ font-size: 22px; margin-bottom: 4px; }}
  .sub {{ color: #666; font-size: 13px; margin-bottom: 24px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
  td, th {{ padding: 8px 10px; border-bottom: 1px solid #e2e2e2; }}
  th {{ text-align: right; background: #f6f6f6; }}
  .num {{ text-align: left; font-variant-numeric: tabular-nums; }}
  .total td {{ font-weight: bold; font-size: 16px; background: #f6f6f6; }}
  .summary {{ display: flex; gap: 24px; margin-top: 24px; font-size: 14px; }}
  .summary b {{ font-size: 16px; }}
  .note {{ margin-top: 28px; font-size: 11px; color: #999; }}
</style>
</head>
<body>
<h1>پیش‌فاکتور طرح آشپزخانه</h1>
<div class="sub">طرح «{escape(design.name)}» · فضای {_fa(room.width_mm)}×{_fa(room.length_mm)} میلی‌متر ·
{_fa(len(design.cabinets))} کابینت · {_fa(len(design.appliances))} لوازم</div>
<table>
  <thead><tr><th>ردیف</th><th>مبلغ</th></tr></thead>
  <tbody>
    {rows_html}
    <tr class="total"><td>جمع نهایی</td><td class="num">{_money(c['summary']['total_retail'])} تومان</td></tr>
  </tbody>
</table>
<div class="summary">
  <span>قیمت به‌ازای هر متر خطی: <b>{_money(c['summary']['price_per_linear_m'])} تومان</b></span>
  <span>تعداد کابینت: <b>{_fa(c['summary']['cabinet_count'])}</b></span>
</div>
<p class="note">این پیش‌فاکتور به‌صورت خودکار از مدل پارامتریک طرح تولید شده است و تخمینی برای تصمیم‌گیری است.</p>
</body>
</html>"""
