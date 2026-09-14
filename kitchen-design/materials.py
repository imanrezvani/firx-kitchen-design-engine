# Material estimation report for selected concept (Concept A)
import math

SHEET_18 = 2.977      # m2 per 1220x2440 18mm MDF sheet
SHEET_06 = 2.977      # m2 per 1220x2440 6mm back panel

def estimate():
    # ---- cabinet module counts (Concept A) ----
    lower_units_600eq = 7.0        # B1,B3,B4 (600) + B2 (900) + A1 (300) + A2,A3 (600)
    tall_units = 2                 # A4 fridge, A5 pantry
    upper_units = 3                # S1, S3, W1 (600 x 1350 to-ceiling)
    overwindow_m2 = 1.0            # 1500x300 over-window cabinet

    m2_lower = lower_units_600eq * 2.0
    m2_tall = tall_units * 5.5
    m2_upper = upper_units * 3.0
    m2_total_18 = m2_lower + m2_tall + m2_upper + overwindow_m2
    sheets_18 = math.ceil(m2_total_18 / SHEET_18 * 1.15)

    back_m2 = 8.1
    sheets_06 = math.ceil(back_m2 / SHEET_06)

    counter_m2 = 3.2               # west 3000 + north 2100, depth 620
    edge_band_m = 100              # total edge banding
    hinges = 32
    slides = 26
    handles = 29
    toe_kick_m = 4.8

    # ---- costs (EUR, mid-range) ----
    price = {
        '18mm MDF sheet': (sheets_18, 40.0),
        '6mm back panel': (sheets_06, 14.0),
        'Countertop quartz m2': (round(counter_m2, 2), 230.0),
        'Edge banding m': (edge_band_m, 1.5),
        'Hinges pcs': (hinges, 2.8),
        'Drawer slides pcs': (slides, 26.0),
        'Handles pcs': (handles, 8.0),
        'Toe-kick plinth (offcut)': (1, 15.0),
        'Adhesives + consumables': (1, 90.0),
    }
    subtotal = 0.0
    rows = []
    for name, (qty, unit) in price.items():
        cost = round(qty * unit, 0)
        subtotal += cost
        rows.append((name, qty, unit, cost))
    contingency = round(subtotal * 0.10)
    total = round(subtotal + contingency)

    appliances = {
        'Undermount stainless sink 860 x 470': 160.0,
        'Kitchen mixer faucet': 140.0,
        'Extractor hood 600 (recirculating)': 260.0,
        'Induction hob 600 (4 zones)': 380.0,
        'Built-in oven 60 cm': 560.0,
        'Integrated dishwasher 600': 520.0,
        'Built-in fridge/freezer 177 cm': 980.0,
    }
    app_total = round(sum(appliances.values()))
    return {
        'sheets_18': sheets_18, 'sheets_06': sheets_06,
        'm2_18': round(m2_total_18, 1), 'm2_back': round(back_m2, 1),
        'counter_m2': counter_m2, 'edge_m': edge_band_m,
        'hinges': hinges, 'slides': slides, 'handles': handles,
        'toe_m': toe_kick_m, 'rows': rows,
        'subtotal': subtotal, 'contingency': contingency, 'total': total,
        'appliances': appliances, 'app_total': app_total,
    }

if __name__ == '__main__':
    import json
    print(json.dumps(estimate(), indent=1, default=str))
