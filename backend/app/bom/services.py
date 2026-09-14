"""BOM (Bill of Materials) generation from a parametric design."""

from __future__ import annotations

from app.bom.components import aggregate_parts, sheet_count
from app.bom.hardware import derive_hardware_breakdown
from app.design.derive import material_estimate, number_cabinets
from app.design.parametric import DesignModel
from app.design import rules as R


def generate_bom(design: DesignModel, catalog_by_id: dict[str, dict]) -> dict:
    """Returns a structured BOM: cabinet/material/appliance/countertop rows
    plus totals. catalog_by_id maps catalog item id -> row (price etc.)."""
    rows: list[dict] = []

    # cabinets
    for c in design.cabinets:
        cat = catalog_by_id.get(c.catalog_item_id or "") if c.catalog_item_id else None
        unit = float(cat["base_price"]) if cat else 0.0
        name = cat.get("name") if cat else c.name
        rows.append(
            {
                "category": "cabinet",
                "code": cat.get("code") if cat else "",
                "name": name,
                "qty": 1,
                "width_mm": c.width_mm,
                "height_mm": c.height_mm,
                "depth_mm": c.depth_mm,
                "unit_price": unit,
                "total_price": unit,
            }
        )

    # appliances
    for ap in design.appliances:
        cat = catalog_by_id.get(ap.catalog_item_id or "") if ap.catalog_item_id else None
        unit = float(cat["price"]) if cat else 0.0
        rows.append(
            {
                "category": "appliance",
                "code": cat.get("code") if cat else "",
                "name": ap.name,
                "qty": 1,
                "width_mm": ap.width_mm,
                "height_mm": ap.height_mm,
                "depth_mm": ap.depth_mm,
                "unit_price": unit,
                "total_price": unit,
            }
        )

    # countertops (approx surface)
    for ct in design.countertops:
        area = (ct.width_mm / 1000) * (ct.depth_mm / 1000)
        unit_price = 0.0
        mat_name = ct.material_name or "کورین"
        rows.append(
            {
                "category": "countertop",
                "code": "",
                "name": f"صفحه کابینت ({mat_name})",
                "qty": 1,
                "width_mm": ct.width_mm,
                "height_mm": ct.thickness_mm,
                "depth_mm": ct.depth_mm,
                "unit_price": round(unit_price, 2),
                "total_price": round(unit_price, 2),
            }
        )

    # materials consumption (component-derived sheet counts)
    sheets = sheet_count(design.cabinets)

    # cabinet numbering for the cut list (stable labels B1/W1/T1…)
    labels = number_cabinets(design)

    # hardware breakdown (derived: hinges/slides/pins/pulls per cabinet)
    hardware = derive_hardware_breakdown(design)
    for h in hardware["items"]:
        rows.append(
            {
                "category": "hardware",
                "code": h["code"],
                "name": h["name"],
                "qty": h["qty"],
                "width_mm": 0,
                "height_mm": 0,
                "depth_mm": 0,
                "unit_price": h["unit_price"],
                "total_price": h["total_price"],
            }
        )

    cabinet_total = sum(r["total_price"] for r in rows if r["category"] == "cabinet")
    appliance_total = sum(r["total_price"] for r in rows if r["category"] == "appliance")
    counter_total = sum(r["total_price"] for r in rows if r["category"] == "countertop")
    hardware_total = sum(r["total_price"] for r in rows if r["category"] == "hardware")
    total = cabinet_total + appliance_total + counter_total + hardware_total

    return {
        "rows": rows,
        "totals": {
            "cabinets": round(cabinet_total, 2),
            "appliances": round(appliance_total, 2),
            "countertops": round(counter_total, 2),
            "hardware": round(hardware_total, 2),
            "grand_total": round(total, 2),
            "accuracy": "±۱۰٪",
        },
        "sheets": sheets,
        "hardware": hardware,
        "parts": aggregate_parts(design.cabinets, labels),
        "material_estimate": material_estimate(design),
        "note": "این BOM برآورد تخمینی متریال و قیمت است؛ برای تولید نهایی به تأیید مهندسی نیاز دارد.",
    }
