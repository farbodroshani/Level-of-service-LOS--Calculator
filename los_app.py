import math
import tkinter as tk
from tkinter import ttk, messagebox, font
from typing import Dict

# ---------- Mode constants ----------

VOLUME_MODES = ["Directional volume", "Two-way volume"]
ANALYSIS_MODES = ["Calculate LOS", "Design for Target LOS"]

# ---------- Shared utility functions ----------

def linear_interpolate(x: float, points: Dict[float, float]) -> float:
    xs = sorted(points.keys())
    if x <= xs[0]:
        return points[xs[0]]
    if x >= xs[-1]:
        return points[xs[-1]]
    for i in range(len(xs) - 1):
        x0, x1 = xs[i], xs[i + 1]
        if x0 <= x <= x1:
            y0, y1 = points[x0], points[x1]
            if x1 == x0:
                return y0
            ratio = (x - x0) / (x1 - x0)
            return y0 + ratio * (y1 - y0)
    return points[xs[-1]]


def bilinear_interpolate(x: float, y: float, table: Dict[float, Dict[float, float]]) -> float:
    xs = sorted(table.keys())
    if x <= xs[0]:
        x_low, x_high = xs[0], xs[0]
    elif x >= xs[-1]:
        x_low, x_high = xs[-1], xs[-1]
    else:
        for i in range(len(xs) - 1):
            if xs[i] <= x <= xs[i + 1]:
                x_low, x_high = xs[i], xs[i + 1]
                break
    if x_low == x_high:
        return linear_interpolate(y, table[x_low])
    y_low_val = linear_interpolate(y, table[x_low])
    y_high_val = linear_interpolate(y, table[x_high])
    ratio = (x - x_low) / (x_high - x_low)
    return y_low_val + ratio * (y_high_val - y_low_val)


# ---------- Table data ----------

LANE_WIDTH_REDUCTION = [
    (12, 0.0),
    (11, 1.9),
    (10, 6.6),
    (0, 6.6),
]

RIGHT_CLEARANCE_RED = {
    2: {6: 0.0, 5: 0.6, 4: 1.2, 3: 1.8, 2: 2.4, 1: 3.0, 0: 3.6},
    3: {6: 0.0, 5: 0.4, 4: 0.8, 3: 1.2, 2: 1.6, 1: 2.0, 0: 2.4},
    4: {6: 0.0, 5: 0.2, 4: 0.4, 3: 0.6, 2: 0.8, 1: 1.0, 0: 1.2},
    5: {6: 0.0, 5: 0.1, 4: 0.2, 3: 0.3, 2: 0.4, 1: 0.5, 0: 0.6},
}

TOTAL_CLEARANCE_RED = {
    12: 0.0,
    10: 0.4,
    8: 0.9,
    6: 1.3,
    4: 1.8,
    2: 3.6,
    0: 5.4,
}

ACCESS_POINT_REDUCTION = {
    0: 0.0,
    10: 2.5,
    20: 5.0,
    30: 7.5,
    40: 10.0,
}

MEDIAN_REDUCTION = {"Undivided": 1.6, "TWLTL": 0.0, "Divided": 0.0}

PCE_GENERAL = {
    "Level": {"truck": 1.5, "rv": 1.2},
    "Rolling": {"truck": 2.5, "rv": 2.0},
    "Mountainous": {"truck": 4.5, "rv": 4.0},
}

FREEWAY_BREAKPOINTS = {
    55: 1800,
    60: 1600,
    65: 1400,
    70: 1200,
    75: 1000,
}

FREEWAY_SPEED_EQUATIONS = {
    55: (0.00002469, 1800),
    60: (0.00001816, 1600),
    65: (0.00001418, 1400),
    70: (0.00001160, 1200),
    75: (0.00001107, 1000),
}

LOS_THRESHOLDS = [
    (11, "A"),
    (18, "B"),
    (26, "C"),
    (35, "D"),
    (45, "E"),
]

MULTILANE_BREAKPOINT = 1400
LOS_MULTI_E = {60: 40, 55: 41, 50: 43, 45: 45}

TABLE_9_14 = {
    "Level": {100: 1.00, 200: 1.00, 300: 1.00, 400: 1.00, 500: 1.00, 600: 1.00, 700: 1.00, 800: 1.00, 900: 1.00},
    "Rolling": {100: 0.67, 200: 0.75, 300: 0.83, 400: 0.90, 500: 0.95, 600: 0.97, 700: 0.98, 800: 0.99, 900: 1.00},
}

TABLE_9_16_TRUCK = {
    "Level": {100: 1.9, 200: 1.5, 300: 1.4, 400: 1.3, 500: 1.2, 600: 1.1, 700: 1.1, 800: 1.1, 900: 1.0},
    "Rolling": {100: 2.7, 200: 2.3, 300: 2.1, 400: 2.0, 500: 1.8, 600: 1.7, 700: 1.6, 800: 1.4, 900: 1.3},
}
TABLE_9_16_RV = {"Level": 1.0, "Rolling": 1.1}

TABLE_9_20 = {
    65: {
        100: {0: 1.1, 20: 2.2, 40: 2.8, 60: 3.0, 80: 3.1, 100: 3.1},
        200: {0: 2.2, 20: 3.3, 40: 3.9, 60: 4.0, 80: 4.2, 100: 4.2},
        400: {0: 1.6, 20: 2.3, 40: 2.7, 60: 2.8, 80: 2.9, 100: 2.9},
        600: {0: 1.4, 20: 1.5, 40: 1.7, 60: 1.9, 80: 2.0, 100: 2.0},
        800: {0: 0.7, 20: 1.0, 40: 1.2, 60: 1.4, 80: 1.5, 100: 1.5},
        1000: {0: 0.6, 20: 0.8, 40: 1.1, 60: 1.1, 80: 1.2, 100: 1.2},
        1200: {0: 0.6, 20: 0.8, 40: 0.9, 60: 1.0, 80: 1.1, 100: 1.1},
        1400: {0: 0.6, 20: 0.7, 40: 0.9, 60: 0.9, 80: 0.9, 100: 0.9},
        1600: {0: 0.6, 20: 0.7, 40: 0.7, 60: 0.7, 80: 0.8, 100: 0.8}},
    60: {
        100: {0: 0.7, 20: 1.7, 40: 2.5, 60: 2.8, 80: 2.9, 100: 2.9},
        200: {0: 1.9, 20: 2.9, 40: 3.7, 60: 4.0, 80: 4.2, 100: 4.2},
        400: {0: 1.4, 20: 2.0, 40: 2.5, 60: 2.7, 80: 3.9, 100: 3.9},
        600: {0: 1.1, 20: 1.3, 40: 1.6, 60: 1.9, 80: 2.0, 100: 2.0},
        800: {0: 0.6, 20: 0.9, 40: 1.1, 60: 1.3, 80: 1.4, 100: 1.4},
        1000: {0: 0.6, 20: 0.7, 40: 0.9, 60: 1.1, 80: 1.2, 100: 1.2},
        1200: {0: 0.5, 20: 0.7, 40: 0.9, 60: 0.9, 80: 1.1, 100: 1.1},
        1400: {0: 0.5, 20: 0.6, 40: 0.8, 60: 0.8, 80: 0.9, 100: 0.9},
        1600: {0: 0.5, 20: 0.6, 40: 0.7, 60: 0.7, 80: 0.7, 100: 0.7}},
    55: {
        100: {0: 0.5, 20: 1.2, 40: 2.2, 60: 2.6, 80: 2.7, 100: 2.7},
        200: {0: 1.5, 20: 2.4, 40: 3.5, 60: 3.9, 80: 4.1, 100: 4.1},
        400: {0: 1.3, 20: 1.9, 40: 2.4, 60: 2.7, 80: 2.8, 100: 2.8},
        600: {0: 0.9, 20: 1.1, 40: 1.6, 60: 1.8, 80: 1.9, 100: 1.9},
        800: {0: 0.5, 20: 0.7, 40: 1.1, 60: 1.2, 80: 1.4, 100: 1.4},
        1000: {0: 0.5, 20: 0.6, 40: 0.8, 60: 0.9, 80: 1.1, 100: 1.1},
        1200: {0: 0.5, 20: 0.6, 40: 0.7, 60: 0.9, 80: 1.0, 100: 1.0},
        1400: {0: 0.5, 20: 0.6, 40: 0.7, 60: 0.7, 80: 0.9, 100: 0.9},
        1600: {0: 0.5, 20: 0.6, 40: 0.6, 60: 0.6, 80: 0.7, 100: 0.7}},
    50: {
        100: {0: 0.2, 20: 0.7, 40: 1.9, 60: 2.4, 80: 2.5, 100: 2.5},
        200: {0: 1.2, 20: 2.0, 40: 3.3, 60: 3.9, 80: 4.0, 100: 4.0},
        400: {0: 1.1, 20: 1.6, 40: 2.2, 60: 2.6, 80: 2.7, 100: 2.7},
        600: {0: 0.6, 20: 0.9, 40: 1.4, 60: 1.7, 80: 1.9, 100: 1.9},
        800: {0: 0.4, 20: 0.6, 40: 0.9, 60: 1.2, 80: 1.3, 100: 1.3},
        1000: {0: 0.4, 20: 0.4, 40: 0.7, 60: 0.9, 80: 1.1, 100: 1.1},
        1200: {0: 0.4, 20: 0.4, 40: 0.7, 60: 0.8, 80: 1.0, 100: 1.0},
        1400: {0: 0.4, 20: 0.4, 40: 0.6, 60: 0.7, 80: 0.8, 100: 0.8},
        1600: {0: 0.4, 20: 0.4, 40: 0.5, 60: 0.5, 80: 0.5, 100: 0.5}},
    45: {
        100: {0: 0.1, 20: 0.4, 40: 1.7, 60: 2.2, 80: 2.4, 100: 2.4},
        200: {0: 0.9, 20: 1.6, 40: 3.1, 60: 3.8, 80: 4.0, 100: 4.0},
        400: {0: 0.9, 20: 0.5, 40: 2.0, 60: 2.5, 80: 2.7, 100: 2.7},
        600: {0: 0.4, 20: 0.3, 40: 1.3, 60: 1.7, 80: 1.8, 100: 1.8},
        800: {0: 0.3, 20: 0.3, 40: 0.8, 60: 1.1, 80: 1.2, 100: 1.2},
        1000: {0: 0.3, 20: 0.3, 40: 0.6, 60: 0.8, 80: 1.1, 100: 1.1},
        1200: {0: 0.3, 20: 0.3, 40: 0.6, 60: 0.7, 80: 1.0, 100: 1.0},
        1400: {0: 0.3, 20: 0.3, 40: 0.6, 60: 0.6, 80: 0.7, 100: 0.7},
        1600: {0: 0.3, 20: 0.3, 40: 0.4, 60: 0.4, 80: 0.6, 100: 0.6}},
}

TABLE_9_21 = {
    "Level": {100: 1.00, 200: 1.00, 300: 1.00, 400: 1.00, 500: 1.00, 600: 1.00, 700: 1.00, 800: 1.00, 900: 1.00},
    "Rolling": {100: 0.73, 200: 0.80, 300: 0.85, 400: 0.90, 500: 0.96, 600: 0.97, 700: 0.99, 800: 1.00, 900: 1.00},
}

TABLE_9_23_TRUCK = {
    "Level": {100: 1.1, 200: 1.1, 300: 1.1, 400: 1.1, 500: 1.0, 600: 1.0, 700: 1.0, 800: 1.0, 900: 1.0},
    "Rolling": {100: 1.9, 200: 1.8, 300: 1.7, 400: 1.6, 500: 1.4, 600: 1.2, 700: 1.0, 800: 1.0, 900: 1.0},
}
TABLE_9_23_RV = {"Level": 1.0, "Rolling": 1.0}

TABLE_9_25 = {
    "50/50": {
        200: {0: 9.0, 20: 29.2, 40: 43.4, 60: 49.4, 80: 51.0, 100: 52.6},
        400: {0: 16.2, 20: 41.0, 40: 54.2, 60: 61.6, 80: 63.8, 100: 65.8},
        600: {0: 15.8, 20: 38.2, 40: 47.8, 60: 53.2, 80: 55.2, 100: 56.8},
        800: {0: 15.8, 20: 33.8, 40: 40.4, 60: 44.0, 80: 44.8, 100: 46.6},
        1400: {0: 12.8, 20: 20.0, 40: 23.8, 60: 26.2, 80: 27.4, 100: 28.6},
        2000: {0: 10.0, 20: 13.6, 40: 15.8, 60: 17.4, 80: 18.2, 100: 18.8},
        2600: {0: 5.5, 20: 7.7, 40: 8.7, 60: 9.5, 80: 10.1, 100: 10.3},
        3200: {0: 3.3, 20: 4.7, 40: 5.1, 60: 5.5, 80: 5.7, 100: 6.1},
    },
    "60/40": {
        200: {0: 11.0, 20: 30.6, 40: 41.0, 60: 51.2, 80: 52.3, 100: 53.5},
        400: {0: 14.6, 20: 36.1, 40: 44.8, 60: 53.4, 80: 55.0, 100: 56.3},
        600: {0: 14.8, 20: 36.9, 40: 44.0, 60: 51.1, 80: 52.8, 100: 54.6},
        800: {0: 13.6, 20: 28.2, 40: 33.4, 60: 38.6, 80: 39.9, 100: 41.3},
        1400: {0: 11.8, 20: 18.9, 40: 22.1, 60: 25.4, 80: 26.4, 100: 27.3},
        2000: {0: 9.1, 20: 13.5, 40: 15.6, 60: 16.0, 80: 16.8, 100: 17.3},
        2600: {0: 5.9, 20: 7.7, 40: 8.6, 60: 9.6, 80: 10.0, 100: 10.2},
    },
    "70/30": {
        200: {0: 9.9, 20: 28.1, 40: 38.0, 60: 47.8, 80: 48.5, 100: 49.0},
        400: {0: 10.6, 20: 30.3, 40: 38.6, 60: 46.7, 80: 47.7, 100: 48.8},
        600: {0: 10.9, 20: 30.9, 40: 37.5, 60: 43.9, 80: 45.4, 100: 47.0},
        800: {0: 10.3, 20: 23.6, 40: 28.4, 60: 33.3, 80: 34.5, 100: 35.5},
        1400: {0: 8.0, 20: 14.6, 40: 17.7, 60: 20.8, 80: 21.6, 100: 22.3},
        2000: {0: 7.3, 20: 9.7, 40: 11.7, 60: 13.3, 80: 14.0, 100: 14.5},
    },
    "80/20": {
        200: {0: 8.9, 20: 27.1, 40: 37.1, 60: 47.0, 80: 47.4, 100: 47.9},
        400: {0: 6.6, 20: 26.1, 40: 34.5, 60: 42.7, 80: 43.5, 100: 44.1},
        600: {0: 4.0, 20: 24.5, 40: 31.3, 60: 38.1, 80: 39.1, 100: 40.0},
        800: {0: 3.8, 20: 18.5, 40: 23.5, 60: 28.4, 80: 29.1, 100: 29.9},
        1400: {0: 3.5, 20: 10.3, 40: 13.3, 60: 16.3, 80: 16.9, 100: 32.2},
        2000: {0: 3.5, 20: 7.0, 40: 8.5, 60: 10.1, 80: 10.4, 100: 10.7},
    },
    "90/10": {
        200: {0: 4.6, 20: 24.1, 40: 33.6, 60: 43.1, 80: 43.4, 100: 43.6},
        400: {0: 0.0, 20: 20.2, 40: 28.3, 60: 36.3, 80: 36.7, 100: 37.0},
        600: {0: -3.1, 20: 16.8, 40: 23.5, 60: 30.1, 80: 30.6, 100: 31.1},
        800: {0: -2.8, 20: 10.5, 40: 15.2, 60: 19.9, 80: 20.3, 100: 20.8},
        1400: {0: -1.2, 20: 5.5, 40: 8.3, 60: 11.0, 80: 11.5, 100: 11.9},
    },
}
TABLE_9_26 = {
    100: (-0.0014, 0.973),
    400: (-0.0022, 0.923),
    600: (-0.0033, 0.870),
    800: (-0.0045, 0.833),
    1000: (-0.0049, 0.829),
    1200: (-0.0054, 0.825),
    1400: (-0.0058, 0.821),
    1600: (-0.0062, 0.817),
}


# ---------- Calculation helpers ----------

# Note: All inputs are assumed to be in Imperial units (feet, miles, etc.)
# No conversion needed as the app only accepts Imperial units


def lane_width_adjustment(width_ft: float) -> float:
    for threshold, value in LANE_WIDTH_REDUCTION:
        if width_ft >= threshold:
            return value
    return LANE_WIDTH_REDUCTION[-1][1]


def right_clearance_adjustment(clearance_ft: float, lanes: int) -> float:
    table = RIGHT_CLEARANCE_RED.get(min(max(lanes, 2), 5))
    values = sorted(table.keys(), reverse=True)
    for threshold in values:
        if clearance_ft >= threshold:
            return table[threshold]
    return table[values[-1]]


def total_clearance_adjustment(tlc_ft: float) -> float:
    keys = sorted(TOTAL_CLEARANCE_RED.keys())
    nearest = keys[0]
    for k in keys:
        if tlc_ft >= k:
            nearest = k
    return TOTAL_CLEARANCE_RED[nearest]


def hv_factor_general(truck_pct: float, rv_pct: float, terrain: str) -> float:
    pt = truck_pct / 100.0
    pr = rv_pct / 100.0
    et = PCE_GENERAL[terrain]["truck"]
    er = PCE_GENERAL[terrain]["rv"]
    return 1.0 / (1.0 + pt * (et - 1.0) + pr * (er - 1.0))


def los_from_density(density: float) -> str:
    for threshold, grade in LOS_THRESHOLDS:
        if density <= threshold:
            return grade
    return "F"


def nearest_split_key(split_pct: float) -> str:
    options = [50, 60, 70, 80, 90]
    major = max(split_pct, 100 - split_pct)
    chosen = min(options, key=lambda x: abs(x - major))
    return f"{chosen}/{100 - chosen}"


# ---------- Facility-specific calculators ----------

def calculate_freeway(inputs: Dict[str, float]) -> Dict[str, float]:
    # All inputs are in Imperial units (feet, miles, etc.)
    lane_width = inputs["lane_width"]
    lateral_clearance = inputs["lateral_clearance"]
    ramp_density = inputs["ramp_density"]
    
    steps = []
    steps.append("=== FREEWAY ANALYSIS - STEP BY STEP ===\n")
    
    # Step 1: FFS calculation
    steps.append("\n--- STEP 1: Calculate Free-Flow Speed (FFS) ---")
    lane_adj = lane_width_adjustment(lane_width)
    steps.append(f"Lane width adjustment (fLW): {lane_adj} mi/h")
    clearance_adj = right_clearance_adjustment(lateral_clearance, int(inputs["lanes"]))
    steps.append(f"Lateral clearance adjustment (fLC): {clearance_adj} mi/h")
    steps.append(f"Ramp density: {ramp_density:.2f} ramps/mi")
    ramp_adj = 3.22 * (ramp_density ** 0.84)
    steps.append(f"Ramp density adjustment: 3.22 × ({ramp_density:.2f})^0.84 = {ramp_adj:.2f} mi/h")
    ffs = 75.4 - lane_adj - clearance_adj - ramp_adj
    steps.append(f"FFS = 75.4 - {lane_adj} - {clearance_adj} - {ramp_adj:.2f} = {ffs:.2f} mi/h")
    
    # Step 2: Select curve
    steps.append("\n--- STEP 2: Select FFS Curve ---")
    curve_choices = [55, 60, 65, 70, 75]
    curve = min(curve_choices, key=lambda x: abs(x - ffs))
    steps.append(f"Computed FFS: {ffs:.2f} mi/h")
    steps.append(f"Nearest standard curve: {curve} mi/h")
    
    # Step 3: Adjust volume
    steps.append("\n--- STEP 3: Adjust Demand Volume ---")
    f_hv = hv_factor_general(inputs["trucks"], inputs["rvs"], inputs["terrain"])
    pt = inputs["trucks"] / 100.0
    pr = inputs["rvs"] / 100.0
    et = PCE_GENERAL[inputs["terrain"]]["truck"]
    er = PCE_GENERAL[inputs["terrain"]]["rv"]
    steps.append(f"Truck %: {inputs['trucks']}%, RV %: {inputs['rvs']}%")
    steps.append(f"Terrain: {inputs['terrain']} → ET={et}, ER={er}")
    steps.append(f"fHV = 1 / [1 + {pt:.3f}×({et}-1) + {pr:.3f}×({er}-1)] = {f_hv:.3f}")
    
    volume = inputs["volume"]
    if inputs.get("is_two_way", False):
        split = inputs.get("directional_split", 50.0) / 100.0
        steps.append(f"Two-way volume: {volume} veh/h, Split: {split*100:.1f}%")
        volume = volume * split
        steps.append(f"Directional volume: {volume:.0f} veh/h")
    else:
        steps.append(f"Directional volume: {volume} veh/h")
    
    steps.append(f"PHF: {inputs['phf']}, Lanes: {inputs['lanes']}, fp: {inputs['driver_factor']}")
    vp = volume / (inputs["phf"] * inputs["lanes"] * inputs["driver_factor"] * f_hv)
    steps.append(f"vp = {volume:.0f} / ({inputs['phf']} × {inputs['lanes']} × {inputs['driver_factor']} × {f_hv:.3f})")
    steps.append(f"vp = {vp:.2f} pc/h/ln")
    
    # Step 4: Calculate speed
    steps.append("\n--- STEP 4: Calculate Speed ---")
    breakpoint = FREEWAY_BREAKPOINTS[curve]
    steps.append(f"Breakpoint for {curve} mi/h curve: {breakpoint} pc/h/ln")
    if vp <= breakpoint:
        speed = curve
        steps.append(f"vp ({vp:.2f}) ≤ breakpoint ({breakpoint})")
        steps.append(f"Speed = FFS = {speed} mi/h")
    else:
        coef, ref = FREEWAY_SPEED_EQUATIONS[curve]
        steps.append(f"vp ({vp:.2f}) > breakpoint ({breakpoint})")
        steps.append(f"Using Eq. 9.1: S = {curve} - {coef}×(vp - {ref})²")
        speed = curve - coef * (vp - ref) ** 2
        steps.append(f"S = {curve} - {coef}×({vp:.2f} - {ref})² = {speed:.2f} mi/h")
        speed = max(speed, 0.1)
    
    # Step 5: Calculate density and LOS
    steps.append("\n--- STEP 5: Calculate Density and LOS ---")
    density = vp / speed if speed else float("inf")
    steps.append(f"Density = vp / Speed = {vp:.2f} / {speed:.2f} = {density:.2f} pc/mi/ln")
    los = los_from_density(density)
    steps.append(f"LOS thresholds: A(≤11), B(≤18), C(≤26), D(≤35), E(≤45), F(>45)")
    steps.append(f"Level of Service: {los}")
    
    return {
        "FFS": round(ffs, 2),
        "CurveFFS": curve,
        "vp": round(vp, 2),
        "Speed": round(speed, 2),
        "Density": round(density, 2),
        "LOS": los,
        "steps": "\n".join(steps),
    }


def calculate_multilane(inputs: Dict[str, float]) -> Dict[str, float]:
    # All inputs are in Imperial units (feet, miles, etc.)
    lane_width = inputs["lane_width"]
    right_clearance = inputs["right_clearance"]
    left_clearance = inputs["left_clearance"]
    access_points = inputs["access_points"]
    
    steps = []
    steps.append("=== MULTILANE HIGHWAY ANALYSIS - STEP BY STEP ===\n")
    
    # Step 1: FFS calculation
    steps.append("\n--- STEP 1: Calculate Free-Flow Speed (FFS) ---")
    steps.append(f"Base FFS (BFFS): {inputs['bffs']} mi/h")
    lane_adj = lane_width_adjustment(lane_width)
    steps.append(f"Lane width adjustment (fLW): {lane_adj} mi/h")
    tlc = min(right_clearance, 6.0) + min(left_clearance, 6.0)
    steps.append(f"Total lateral clearance (TLC): min({right_clearance:.1f}, 6) + min({left_clearance:.1f}, 6) = {tlc:.1f} ft")
    clearance_adj = total_clearance_adjustment(tlc)
    steps.append(f"Lateral clearance adjustment (fLC): {clearance_adj} mi/h")
    median_adj = MEDIAN_REDUCTION[inputs["median"]]
    steps.append(f"Median type: {inputs['median']} → adjustment (fM): {median_adj} mi/h")
    access_adj = linear_interpolate(access_points, ACCESS_POINT_REDUCTION)
    steps.append(f"Access points: {access_points:.1f} per mi → adjustment (fA): {access_adj:.2f} mi/h")
    ffs = inputs["bffs"] - lane_adj - clearance_adj - median_adj - access_adj
    steps.append(f"FFS = {inputs['bffs']} - {lane_adj} - {clearance_adj} - {median_adj} - {access_adj:.2f} = {ffs:.2f} mi/h")
    
    # Step 2: Select curve
    steps.append("\n--- STEP 2: Select FFS Curve ---")
    curve_options = [45, 50, 55, 60]
    curve = min(curve_options, key=lambda x: abs(x - ffs))
    steps.append(f"Computed FFS: {ffs:.2f} mi/h")
    steps.append(f"Nearest standard curve: {curve} mi/h")
    
    # Step 3: Adjust volume
    steps.append("\n--- STEP 3: Adjust Demand Volume ---")
    f_hv = hv_factor_general(inputs["trucks"], inputs["rvs"], inputs["terrain"])
    pt = inputs["trucks"] / 100.0
    pr = inputs["rvs"] / 100.0
    et = PCE_GENERAL[inputs["terrain"]]["truck"]
    er = PCE_GENERAL[inputs["terrain"]]["rv"]
    steps.append(f"Truck %: {inputs['trucks']}%, RV %: {inputs['rvs']}%")
    steps.append(f"Terrain: {inputs['terrain']} → ET={et}, ER={er}")
    steps.append(f"fHV = 1 / [1 + {pt:.3f}×({et}-1) + {pr:.3f}×({er}-1)] = {f_hv:.3f}")
    
    volume = inputs["volume"]
    if inputs.get("is_two_way", False):
        split = inputs.get("directional_split", 50.0) / 100.0
        steps.append(f"Two-way volume: {volume} veh/h, Split: {split*100:.1f}%")
        volume = volume * split
        steps.append(f"Directional volume: {volume:.0f} veh/h")
    else:
        steps.append(f"Directional volume: {volume} veh/h")
    
    steps.append(f"PHF: {inputs['phf']}, Lanes: {inputs['lanes']}, fp: {inputs['driver_factor']}")
    vp = volume / (inputs["phf"] * inputs["lanes"] * inputs["driver_factor"] * f_hv)
    steps.append(f"vp = {volume:.0f} / ({inputs['phf']} × {inputs['lanes']} × {inputs['driver_factor']} × {f_hv:.3f})")
    steps.append(f"vp = {vp:.2f} pc/h/ln")
    
    # Step 4: Calculate speed
    steps.append("\n--- STEP 4: Calculate Speed ---")
    steps.append(f"Breakpoint: {MULTILANE_BREAKPOINT} pc/h/ln")
    if vp <= MULTILANE_BREAKPOINT:
        speed = curve
        steps.append(f"vp ({vp:.2f}) ≤ breakpoint ({MULTILANE_BREAKPOINT})")
        steps.append(f"Speed = FFS = {speed} mi/h")
    else:
        coef_table = {60: (5.00, 800), 55: (3.78, 700), 50: (3.49, 600), 45: (2.78, 500)}
        coef, denom = coef_table[curve]
        steps.append(f"vp ({vp:.2f}) > breakpoint ({MULTILANE_BREAKPOINT})")
        steps.append(f"Using Eq. 9.6: S = {curve} - {coef}×[(vp - 1400)/{denom}]^1.31")
        speed = curve - coef * ((vp - 1400) / denom) ** 1.31
        steps.append(f"S = {curve} - {coef}×[({vp:.2f} - 1400)/{denom}]^1.31 = {speed:.2f} mi/h")
        speed = max(speed, 0.1)
    
    # Step 5: Calculate density and LOS
    steps.append("\n--- STEP 5: Calculate Density and LOS ---")
    density = vp / speed if speed else float("inf")
    steps.append(f"Density = vp / Speed = {vp:.2f} / {speed:.2f} = {density:.2f} pc/mi/ln")
    los = los_from_density(density)
    steps.append(f"LOS thresholds: A(≤11), B(≤18), C(≤26), D(≤35), E(≤{LOS_MULTI_E[curve]})")
    if density > LOS_MULTI_E[curve]:
        los = "F"
        steps.append(f"Density ({density:.2f}) > E threshold ({LOS_MULTI_E[curve]})")
    steps.append(f"Level of Service: {los}")
    
    return {
        "FFS": round(ffs, 2),
        "CurveFFS": curve,
        "vp": round(vp, 2),
        "Speed": round(speed, 2),
        "Density": round(density, 2),
        "LOS": los,
        "steps": "\n".join(steps),
    }


def calculate_two_lane(inputs: Dict[str, float]) -> Dict[str, float]:
    # All inputs are in Imperial units (feet, miles, etc.)
    lane_width = inputs["lane_width"]
    shoulder_width = inputs["shoulder_width"]
    access_points = inputs["access_points"]
    
    steps = []
    steps.append("=== TWO-LANE HIGHWAY ANALYSIS - STEP BY STEP ===\n")
    
    # Step 1: FFS calculation
    steps.append("\n--- STEP 1: Calculate Free-Flow Speed (FFS) ---")
    steps.append(f"Base FFS (BFFS): {inputs['bffs']} mi/h")
    
    lane_adj = linear_interpolate(lane_width, {9: 2.2, 10: 1.1, 11: 0.4, 12: 0.0})
    steps.append(f"Lane width: {lane_width:.1f} ft → adjustment (fLW): {lane_adj:.2f} mi/h")
    
    shoulder_adj = linear_interpolate(shoulder_width, {0: 4.2, 2: 2.6, 4: 1.3, 6: 0.0})
    steps.append(f"Shoulder width: {shoulder_width:.1f} ft → adjustment (fS): {shoulder_adj:.2f} mi/h")
    
    access_adj = linear_interpolate(access_points, ACCESS_POINT_REDUCTION)
    steps.append(f"Access points: {access_points:.1f} per mi → adjustment (fA): {access_adj:.2f} mi/h")
    
    ffs = inputs["bffs"] - lane_adj - shoulder_adj - access_adj
    steps.append(f"FFS = {inputs['bffs']} - {lane_adj:.2f} - {shoulder_adj:.2f} - {access_adj:.2f} = {ffs:.2f} mi/h")
    
    # Step 2: Volume splitting
    steps.append("\n--- STEP 2: Split Two-Way Volume ---")
    total_volume = inputs["volume"]
    split = max(min(inputs["directional_split"], 100.0), 0.0)
    steps.append(f"Total two-way volume: {total_volume} veh/h")
    steps.append(f"Directional split: {split:.1f}% (toward analysis direction)")
    
    v_d = total_volume * split / 100.0
    v_o = total_volume - v_d
    steps.append(f"Analysis direction volume (Vd): {v_d:.0f} veh/h")
    steps.append(f"Opposing direction volume (Vo): {v_o:.0f} veh/h")
    
    terrain = inputs["terrain"]
    pt = inputs["trucks"] / 100.0
    pr = inputs["rvs"] / 100.0
    steps.append(f"\nTerrain: {terrain}")
    steps.append(f"Truck %: {inputs['trucks']}%, RV %: {inputs['rvs']}%")
    steps.append(f"PHF: {inputs['phf']}")

    # Step 3: ATS calculation
    steps.append("\n--- STEP 3: Calculate Average Travel Speed (ATS) ---")
    
    fg_ats = linear_interpolate(v_d, TABLE_9_14[terrain])
    steps.append(f"Grade adjustment factor (fg) from Table 9.14: {fg_ats:.3f}")
    
    et = linear_interpolate(v_d, TABLE_9_16_TRUCK[terrain])
    er = TABLE_9_16_RV[terrain]
    steps.append(f"PCE for trucks (ET) from Table 9.16: {et:.2f}")
    steps.append(f"PCE for RVs (ER) from Table 9.16: {er:.2f}")
    
    f_hv_ats = 1.0 / (1.0 + pt * (et - 1.0) + pr * (er - 1.0))
    steps.append(f"Heavy vehicle factor: fHV = 1 / [1 + {pt:.3f}×({et:.2f}-1) + {pr:.3f}×({er:.2f}-1)] = {f_hv_ats:.3f}")
    
    v_d_ats = v_d / (inputs["phf"] * fg_ats * max(f_hv_ats, 1e-6))
    v_o_ats = v_o / (inputs["phf"] * fg_ats * max(f_hv_ats, 1e-6))
    steps.append(f"Adjusted flow rate (Vd): {v_d:.0f} / ({inputs['phf']} × {fg_ats:.3f} × {f_hv_ats:.3f}) = {v_d_ats:.2f} pc/h")
    steps.append(f"Adjusted flow rate (Vo): {v_o:.0f} / ({inputs['phf']} × {fg_ats:.3f} × {f_hv_ats:.3f}) = {v_o_ats:.2f} pc/h")

    percent_np = inputs["no_passing"]
    ffs_lookup = min(max(45, round(ffs / 5.0) * 5), 65)
    steps.append(f"\nNo-passing zones: {percent_np:.0f}%")
    steps.append(f"FFS rounded for table lookup: {ffs_lookup} mi/h")
    
    fnp_ats = bilinear_interpolate(v_o, percent_np, TABLE_9_20[ffs_lookup])
    steps.append(f"No-passing adjustment (fnp) from Table 9.20: {fnp_ats:.2f} mi/h")
    
    ats = ffs - 0.00776 * (v_d_ats + v_o_ats) - fnp_ats
    steps.append(f"\nUsing Eq. 9.10:")
    steps.append(f"ATS = {ffs:.2f} - 0.00776×({v_d_ats:.2f} + {v_o_ats:.2f}) - {fnp_ats:.2f}")
    steps.append(f"ATS = {ats:.2f} mi/h")

    # Step 4: PTSF calculation
    steps.append("\n--- STEP 4: Calculate Percent Time Spent Following (PTSF) ---")
    
    fg_ptsf = linear_interpolate(v_d, TABLE_9_21[terrain])
    steps.append(f"Grade adjustment factor (fg) from Table 9.21: {fg_ptsf:.3f}")
    
    et_ptsf = linear_interpolate(v_d, TABLE_9_23_TRUCK[terrain])
    er_ptsf = TABLE_9_23_RV[terrain]
    steps.append(f"PCE for trucks (ET) from Table 9.23: {et_ptsf:.2f}")
    steps.append(f"PCE for RVs (ER) from Table 9.23: {er_ptsf:.2f}")
    
    f_hv_ptsf = 1.0 / (1.0 + pt * (et_ptsf - 1.0) + pr * (er_ptsf - 1.0))
    steps.append(f"Heavy vehicle factor: fHV = 1 / [1 + {pt:.3f}×({et_ptsf:.2f}-1) + {pr:.3f}×({er_ptsf:.2f}-1)] = {f_hv_ptsf:.3f}")
    
    v_d_ptsf = v_d / (inputs["phf"] * fg_ptsf * max(f_hv_ptsf, 1e-6))
    v_o_ptsf = v_o / (inputs["phf"] * fg_ptsf * max(f_hv_ptsf, 1e-6))
    steps.append(f"Adjusted flow rate (Vd): {v_d:.0f} / ({inputs['phf']} × {fg_ptsf:.3f} × {f_hv_ptsf:.3f}) = {v_d_ptsf:.2f} pc/h")
    steps.append(f"Adjusted flow rate (Vo): {v_o:.0f} / ({inputs['phf']} × {fg_ptsf:.3f} × {f_hv_ptsf:.3f}) = {v_o_ptsf:.2f} pc/h")

    a_table = {k: v[0] for k, v in TABLE_9_26.items()}
    b_table = {k: v[1] for k, v in TABLE_9_26.items()}
    a = linear_interpolate(v_o, a_table)
    b = linear_interpolate(v_o, b_table)
    steps.append(f"\nFrom Table 9.26 (interpolated for Vo = {v_o_ptsf:.2f}):")
    steps.append(f"  a = {a:.6f}")
    steps.append(f"  b = {b:.3f}")
    
    base_term = v_d_ptsf ** b if v_d_ptsf > 0 else 0
    bptsf = 100 * (1 - math.exp(a * base_term))
    steps.append(f"\nUsing Eq. 9.11:")
    steps.append(f"BPTSF = 100 × [1 - exp({a:.6f} × {v_d_ptsf:.2f}^{b:.3f})]")
    steps.append(f"BPTSF = {bptsf:.2f}%")

    split_key = nearest_split_key(split)
    steps.append(f"\nDirectional split key for table lookup: {split_key}")
    
    fnp_table = TABLE_9_25[split_key]
    fnp_ptsf = bilinear_interpolate(total_volume, percent_np, fnp_table)
    steps.append(f"No-passing adjustment (fnp,d/np) from Table 9.25: {fnp_ptsf:.2f}%")
    
    v_total_adj = v_d_ptsf + v_o_ptsf
    ratio = (v_d_ptsf / v_total_adj) if v_total_adj else 0.0
    steps.append(f"Directional flow ratio: {v_d_ptsf:.2f} / ({v_d_ptsf:.2f} + {v_o_ptsf:.2f}) = {ratio:.3f}")
    
    ptsf = bptsf + fnp_ptsf * ratio
    steps.append(f"\nUsing Eq. 9.12:")
    steps.append(f"PTSF = {bptsf:.2f} + {fnp_ptsf:.2f} × {ratio:.3f}")
    steps.append(f"PTSF = {ptsf:.2f}%")

    # Step 5: LOS determination
    steps.append("\n--- STEP 5: Determine Level of Service (LOS) ---")
    pffs_percent = (ats / ffs) * 100.0 if ffs else 0.0
    steps.append(f"Percent of FFS (PFFS) = (ATS / FFS) × 100 = ({ats:.2f} / {ffs:.2f}) × 100 = {pffs_percent:.2f}%")
    steps.append(f"Highway Class: {inputs['class_type']}")
    
    if inputs["class_type"] == "Class I":
        steps.append("\nClass I criteria:")
        steps.append("  ATS thresholds: A(>55), B(>50), C(>45), D(>40), E(≤40)")
        steps.append("  PTSF thresholds: A(≤35), B(≤50), C(≤65), D(≤80), E(>80)")
        ats_grade = "A" if ats > 55 else "B" if ats > 50 else "C" if ats > 45 else "D" if ats > 40 else "E"
        ptsf_grade = "A" if ptsf <= 35 else "B" if ptsf <= 50 else "C" if ptsf <= 65 else "D" if ptsf <= 80 else "E"
        steps.append(f"  ATS = {ats:.2f} mi/h → LOS {ats_grade} (based on ATS)")
        steps.append(f"  PTSF = {ptsf:.2f}% → LOS {ptsf_grade} (based on PTSF)")
        los = min(ats_grade, ptsf_grade)
        steps.append(f"  Final LOS: {los} (worse of the two)")
    elif inputs["class_type"] == "Class II":
        steps.append("\nClass II criteria (PTSF only):")
        steps.append("  PTSF thresholds: A(≤40), B(≤55), C(≤70), D(≤85), E(>85)")
        los = "A" if ptsf <= 40 else "B" if ptsf <= 55 else "C" if ptsf <= 70 else "D" if ptsf <= 85 else "E"
        steps.append(f"  PTSF = {ptsf:.2f}% → LOS {los}")
    else:  # Class III
        steps.append("\nClass III criteria (PFFS only):")
        steps.append("  PFFS thresholds: A(≥91.7), B(≥83.3), C(≥75), D(≥66.7), E(<66.7)")
        los = "A" if pffs_percent >= 91.7 else "B" if pffs_percent >= 83.3 else "C" if pffs_percent >= 75 else "D" if pffs_percent >= 66.7 else "E"
        steps.append(f"  PFFS = {pffs_percent:.2f}% → LOS {los}")
    
    steps.append(f"\nLevel of Service: {los}")
    
    return {
        "FFS": round(ffs, 2),
        "ATS": round(ats, 2),
        "PTSF": round(ptsf, 2),
        "PFFS": round(pffs_percent, 2),
        "LOS": los,
        "steps": "\n".join(steps),
    }


def grade_from_table(ptsf: float, pffs_percent: float, ats: float, class_type: str) -> str:
    if class_type == "Class I":
        ats_grade = "A" if ats > 55 else "B" if ats > 50 else "C" if ats > 45 else "D" if ats > 40 else "E"
        ptsf_grade = "A" if ptsf <= 35 else "B" if ptsf <= 50 else "C" if ptsf <= 65 else "D" if ptsf <= 80 else "E"
        return min(ats_grade, ptsf_grade)
    if class_type == "Class II":
        return "A" if ptsf <= 40 else "B" if ptsf <= 55 else "C" if ptsf <= 70 else "D" if ptsf <= 85 else "E"
    if class_type == "Class III":
        return "A" if pffs_percent >= 91.7 else "B" if pffs_percent >= 83.3 else "C" if pffs_percent >= 75 else "D" if pffs_percent >= 66.7 else "E"
    return "N/A"


def design_for_target_los(inputs: Dict[str, float], facility_type: str, target_los: str) -> Dict:
    """Binary search to find minimum lanes needed for target LOS."""
    max_lanes = 8
    for lanes in range(1, max_lanes + 1):
        test_inputs = inputs.copy()
        test_inputs["lanes"] = lanes
        if facility_type == "Freeway":
            result = calculate_freeway(test_inputs)
        elif facility_type == "Multilane":
            result = calculate_multilane(test_inputs)
        else:
            return {"error": "Design mode only supports Freeway and Multilane"}
        
        if result["LOS"] <= target_los:
            return {"lanes_required": lanes, "result": result}
    
    return {"error": f"Cannot achieve LOS {target_los} with up to {max_lanes} lanes"}


# ---------- UI ----------

class LOSCalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Highway Level of Service Calculator - HCM 2010")
        self.geometry("1200x750")
        self.resizable(True, True)
        self.configure(bg="#f0f0f0")
        
        # Custom fonts
        self.title_font = font.Font(family="Segoe UI", size=12, weight="bold")
        self.label_font = font.Font(family="Segoe UI", size=10)
        self.entry_font = font.Font(family="Segoe UI", size=9)
        
        # Header
        header = tk.Frame(self, bg="#2c3e50", height=60)
        header.pack(fill="x", side="top")
        tk.Label(header, text="Level of Service Calculator", 
                 font=font.Font(family="Segoe UI", size=16, weight="bold"),
                 bg="#2c3e50", fg="white").pack(pady=15)
        
        # Main container
        main_container = tk.Frame(self, bg="#f0f0f0")
        main_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Left panel - Controls
        left_panel = tk.Frame(main_container, bg="white", relief="groove", bd=2)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Analysis mode selector
        mode_frame = tk.Frame(left_panel, bg="white")
        mode_frame.pack(fill="x", padx=15, pady=10)
        tk.Label(mode_frame, text="Analysis Mode:", font=self.title_font, bg="white").pack(anchor="w")
        self.analysis_mode_var = tk.StringVar(value=ANALYSIS_MODES[0])
        mode_selector = ttk.Combobox(mode_frame, textvariable=self.analysis_mode_var, 
                                     values=ANALYSIS_MODES, state="readonly", font=self.entry_font)
        mode_selector.pack(fill="x", pady=5)
        mode_selector.bind("<<ComboboxSelected>>", lambda _: self.show_form())
        
        # Facility type selector
        facility_frame = tk.Frame(left_panel, bg="white")
        facility_frame.pack(fill="x", padx=15, pady=10)
        tk.Label(facility_frame, text="Facility Type:", font=self.title_font, bg="white").pack(anchor="w")
        self.facility_var = tk.StringVar(value="Freeway")
        options = ["Freeway", "Multilane Highway", "Two-Lane Highway"]
        facility_selector = ttk.Combobox(facility_frame, textvariable=self.facility_var, 
                                        values=options, state="readonly", font=self.entry_font)
        facility_selector.pack(fill="x", pady=5)
        facility_selector.bind("<<ComboboxSelected>>", lambda _: self.show_form())
        
        # Scrollable form frame
        canvas_frame = tk.Frame(left_panel, bg="white")
        canvas_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.form_frame = tk.Frame(self.canvas, bg="white")
        
        self.canvas.create_window((0, 0), window=self.form_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.form_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Right panel - Output (wider and expandable)
        right_panel = tk.Frame(main_container, bg="white", relief="groove", bd=2, width=500)
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))
        right_panel.pack_propagate(False)
        
        tk.Label(right_panel, text="Results", font=self.title_font, bg="white").pack(pady=10)
        
        self.output = tk.Text(right_panel, font=self.entry_font, wrap="word", 
                             relief="flat", bg="#f9f9f9", padx=10, pady=10)
        self.output.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Footer with copyright and citations
        footer = tk.Frame(self, bg="#34495e", height=50)
        footer.pack(fill="x", side="bottom")
        
        copyright_label = tk.Label(footer, text="© 2025 Farbod Roshani. All rights reserved.", 
                                   font=font.Font(family="Segoe UI", size=9),
                                   bg="#34495e", fg="white")
        copyright_label.pack(pady=(5, 2))
        
        citation_label = tk.Label(footer, 
                                 text="Based on: Highway Capacity Manual (HCM 2010) | Hoel, Garber & Sarkar - Traffic and Highway Engineering (2020)", 
                                 font=font.Font(family="Segoe UI", size=8),
                                 bg="#34495e", fg="#bdc3c7")
        citation_label.pack(pady=(0, 5))
        
        self.show_form()

    def show_form(self):
        for child in self.form_frame.winfo_children():
            child.destroy()
        
        mode = self.analysis_mode_var.get()
        facility = self.facility_var.get()
        
        if facility == "Freeway":
            self.build_freeway_form(mode)
        elif facility == "Multilane Highway":
            self.build_multilane_form(mode)
        else:
            self.build_two_lane_form(mode)

    def add_section_header(self, parent, text):
        frame = tk.Frame(parent, bg="#34495e", height=30)
        frame.pack(fill="x", pady=(10, 5))
        tk.Label(frame, text=text, font=self.title_font, bg="#34495e", fg="white").pack(pady=5)

    def add_field(self, parent, label, key, default=""):
        tk.Label(parent, text=label, font=self.label_font, bg="white", anchor="w").pack(fill="x", pady=(5, 2))
        entry = ttk.Entry(parent, font=self.entry_font)
        entry.insert(0, default)
        entry.pack(fill="x", pady=(0, 5))
        self.widgets[key] = entry

    def build_freeway_form(self, mode):
        self.widgets = {}
        
        # Volume configuration
        self.add_section_header(self.form_frame, "Volume Configuration")
        tk.Label(self.form_frame, text="Volume input type:", font=self.label_font, bg="white").pack(anchor="w", pady=(5, 2))
        volume_mode = ttk.Combobox(self.form_frame, values=VOLUME_MODES, state="readonly", font=self.entry_font)
        volume_mode.set(VOLUME_MODES[0])
        volume_mode.pack(fill="x", pady=(0, 5))
        self.widgets["volume_mode"] = volume_mode
        
        self.add_field(self.form_frame, "Directional split toward analysis (%):", "directional_split", "50")
        
        # Traffic data
        self.add_section_header(self.form_frame, "Traffic Data")
        self.add_field(self.form_frame, "Demand volume (veh/h):", "volume", "4000")
        self.add_field(self.form_frame, "Peak hour factor (PHF):", "phf", "0.92")
        
        if mode == ANALYSIS_MODES[1]:  # Design mode
            tk.Label(self.form_frame, text="Target Level of Service:", font=self.label_font, bg="white").pack(anchor="w", pady=(5, 2))
            los_box = ttk.Combobox(self.form_frame, values=["A", "B", "C", "D", "E"], state="readonly", font=self.entry_font)
            los_box.set("C")
            los_box.pack(fill="x", pady=(0, 5))
            self.widgets["target_los"] = los_box
        else:
            self.add_field(self.form_frame, "Number of lanes (directional):", "lanes", "3")
        
        self.add_field(self.form_frame, "Driver population factor:", "driver_factor", "1.0")
        self.add_field(self.form_frame, "% Trucks:", "trucks", "6")
        self.add_field(self.form_frame, "% RVs:", "rvs", "2")
        
        # Geometric data
        self.add_section_header(self.form_frame, "Geometric Data")
        self.add_field(self.form_frame, "Lane width (ft):", "lane_width", "12")
        self.add_field(self.form_frame, "Right lateral clearance (ft):", "lateral_clearance", "6")
        self.add_field(self.form_frame, "Total ramp density (ramps/mi):", "ramp_density", "1.0")
        
        tk.Label(self.form_frame, text="Terrain:", font=self.label_font, bg="white").pack(anchor="w", pady=(5, 2))
        terrain_box = ttk.Combobox(self.form_frame, values=list(PCE_GENERAL.keys()), state="readonly", font=self.entry_font)
        terrain_box.set("Level")
        terrain_box.pack(fill="x", pady=(0, 5))
        self.widgets["terrain"] = terrain_box
        
        # Compute button
        btn_frame = tk.Frame(self.form_frame, bg="white")
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Calculate", command=self.handle_freeway).pack()

    def build_multilane_form(self, mode):
        self.widgets = {}
        
        self.add_section_header(self.form_frame, "Volume Configuration")
        tk.Label(self.form_frame, text="Volume input type:", font=self.label_font, bg="white").pack(anchor="w", pady=(5, 2))
        volume_mode = ttk.Combobox(self.form_frame, values=VOLUME_MODES, state="readonly", font=self.entry_font)
        volume_mode.set(VOLUME_MODES[0])
        volume_mode.pack(fill="x", pady=(0, 5))
        self.widgets["volume_mode"] = volume_mode
        
        self.add_field(self.form_frame, "Directional split toward analysis (%):", "directional_split", "50")
        
        self.add_section_header(self.form_frame, "Traffic Data")
        self.add_field(self.form_frame, "Demand volume (veh/h):", "volume", "1900")
        self.add_field(self.form_frame, "Peak hour factor (PHF):", "phf", "0.90")
        
        if mode == ANALYSIS_MODES[1]:
            tk.Label(self.form_frame, text="Target Level of Service:", font=self.label_font, bg="white").pack(anchor="w", pady=(5, 2))
            los_box = ttk.Combobox(self.form_frame, values=["A", "B", "C", "D", "E"], state="readonly", font=self.entry_font)
            los_box.set("C")
            los_box.pack(fill="x", pady=(0, 5))
            self.widgets["target_los"] = los_box
        else:
            self.add_field(self.form_frame, "Number of lanes (directional):", "lanes", "2")
        
        self.add_field(self.form_frame, "Driver population factor:", "driver_factor", "1.0")
        self.add_field(self.form_frame, "% Trucks:", "trucks", "13")
        self.add_field(self.form_frame, "% RVs:", "rvs", "2")
        
        self.add_section_header(self.form_frame, "Geometric Data")
        self.add_field(self.form_frame, "Base FFS (mi/h):", "bffs", "55")
        self.add_field(self.form_frame, "Lane width (ft):", "lane_width", "11")
        self.add_field(self.form_frame, "Right lateral clearance (ft):", "right_clearance", "4")
        self.add_field(self.form_frame, "Left lateral clearance (ft):", "left_clearance", "2")
        self.add_field(self.form_frame, "Access points per mile:", "access_points", "12")
        
        tk.Label(self.form_frame, text="Median type:", font=self.label_font, bg="white").pack(anchor="w", pady=(5, 2))
        median_box = ttk.Combobox(self.form_frame, values=list(MEDIAN_REDUCTION.keys()), state="readonly", font=self.entry_font)
        median_box.set("Undivided")
        median_box.pack(fill="x", pady=(0, 5))
        self.widgets["median"] = median_box
        
        tk.Label(self.form_frame, text="Terrain:", font=self.label_font, bg="white").pack(anchor="w", pady=(5, 2))
        terrain_box = ttk.Combobox(self.form_frame, values=list(PCE_GENERAL.keys()), state="readonly", font=self.entry_font)
        terrain_box.set("Level")
        terrain_box.pack(fill="x", pady=(0, 5))
        self.widgets["terrain"] = terrain_box
        
        btn_frame = tk.Frame(self.form_frame, bg="white")
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Calculate", command=self.handle_multilane).pack()

    def build_two_lane_form(self, mode):
        self.widgets = {}
        
        if mode == ANALYSIS_MODES[1]:
            messagebox.showinfo("Info", "Design mode is not available for Two-Lane Highways.\nSwitching to Calculate LOS mode.")
            self.analysis_mode_var.set(ANALYSIS_MODES[0])
        
        self.add_section_header(self.form_frame, "Traffic Data")
        self.add_field(self.form_frame, "Two-way volume (veh/h):", "volume", "1600")
        self.add_field(self.form_frame, "Directional split toward analysis (%):", "directional_split", "50")
        self.add_field(self.form_frame, "Peak hour factor (PHF):", "phf", "0.95")
        self.add_field(self.form_frame, "% Trucks:", "trucks", "14")
        self.add_field(self.form_frame, "% RVs:", "rvs", "4")
        
        self.add_section_header(self.form_frame, "Geometric Data")
        self.add_field(self.form_frame, "Base FFS (mi/h):", "bffs", "60")
        self.add_field(self.form_frame, "Lane width (ft):", "lane_width", "11")
        self.add_field(self.form_frame, "Shoulder width (ft):", "shoulder_width", "4")
        self.add_field(self.form_frame, "Access points per mile:", "access_points", "20")
        self.add_field(self.form_frame, "% No-passing zones:", "no_passing", "50")
        
        tk.Label(self.form_frame, text="Terrain:", font=self.label_font, bg="white").pack(anchor="w", pady=(5, 2))
        terrain_box = ttk.Combobox(self.form_frame, values=["Level", "Rolling"], state="readonly", font=self.entry_font)
        terrain_box.set("Rolling")
        terrain_box.pack(fill="x", pady=(0, 5))
        self.widgets["terrain"] = terrain_box
        
        tk.Label(self.form_frame, text="Highway class:", font=self.label_font, bg="white").pack(anchor="w", pady=(5, 2))
        class_box = ttk.Combobox(self.form_frame, values=["Class I", "Class II", "Class III"], state="readonly", font=self.entry_font)
        class_box.set("Class I")
        class_box.pack(fill="x", pady=(0, 5))
        self.widgets["class_type"] = class_box
        
        btn_frame = tk.Frame(self.form_frame, bg="white")
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Calculate", command=self.handle_two_lane).pack()

    def gather_inputs(self) -> Dict:
        inputs = {}
        # All inputs are in Imperial units - no conversion needed
        
        for key, widget in self.widgets.items():
            if key in ["volume_mode", "terrain", "median", "class_type", "target_los"]:
                inputs[key] = widget.get()
            else:
                try:
                    inputs[key] = float(widget.get())
                except:
                    pass
        
        if "volume_mode" in inputs:
            inputs["is_two_way"] = (inputs["volume_mode"] == VOLUME_MODES[1])
        
        return inputs

    def handle_freeway(self):
        try:
            inputs = self.gather_inputs()
            mode = self.analysis_mode_var.get()
            
            if mode == ANALYSIS_MODES[1]:  # Design mode
                target_los = inputs.get("target_los", "C")
                result = design_for_target_los(inputs, "Freeway", target_los)
                if "error" in result:
                    self.output.delete("1.0", "end")
                    self.output.insert("1.0", f"Error: {result['error']}")
                else:
                    self.output.delete("1.0", "end")
                    self.output.insert("1.0", f"=== DESIGN RESULTS ===\n\n")
                    self.output.insert("end", f"Target LOS: {target_los}\n")
                    self.output.insert("end", f"Lanes Required: {result['lanes_required']}\n\n")
                    self.output.insert("end", "Performance with designed lanes:\n")
                    for k, v in result['result'].items():
                        if k != "steps":
                            self.output.insert("end", f"  {k}: {v}\n")
            else:  # Calculate mode
                result = calculate_freeway(inputs)
                self.output.delete("1.0", "end")
                self.output.insert("1.0", "=== FREEWAY ANALYSIS RESULTS ===\n\n")
                for key, value in result.items():
                    if key != "steps":
                        self.output.insert("end", f"{key}: {value}\n")
                
                # Show detailed calculations button
                if "steps" in result:
                    self.output.insert("end", "\n")
                    btn = tk.Button(self.output, text="View Step-by-Step Calculations", 
                                   command=lambda: self.show_steps_window(result["steps"]))
                    self.output.window_create("end", window=btn)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def handle_multilane(self):
        try:
            inputs = self.gather_inputs()
            mode = self.analysis_mode_var.get()
            
            if mode == ANALYSIS_MODES[1]:
                target_los = inputs.get("target_los", "C")
                result = design_for_target_los(inputs, "Multilane", target_los)
                if "error" in result:
                    self.output.delete("1.0", "end")
                    self.output.insert("1.0", f"Error: {result['error']}")
                else:
                    self.output.delete("1.0", "end")
                    self.output.insert("1.0", f"=== DESIGN RESULTS ===\n\n")
                    self.output.insert("end", f"Target LOS: {target_los}\n")
                    self.output.insert("end", f"Lanes Required: {result['lanes_required']}\n\n")
                    self.output.insert("end", "Performance with designed lanes:\n")
                    for k, v in result['result'].items():
                        if k != "steps":
                            self.output.insert("end", f"  {k}: {v}\n")
            else:
                result = calculate_multilane(inputs)
                self.output.delete("1.0", "end")
                self.output.insert("1.0", "=== MULTILANE HIGHWAY RESULTS ===\n\n")
                for key, value in result.items():
                    if key != "steps":
                        self.output.insert("end", f"{key}: {value}\n")
                
                # Show detailed calculations button
                if "steps" in result:
                    self.output.insert("end", "\n")
                    btn = tk.Button(self.output, text="View Step-by-Step Calculations", 
                                   command=lambda: self.show_steps_window(result["steps"]))
                    self.output.window_create("end", window=btn)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def handle_two_lane(self):
        try:
            inputs = self.gather_inputs()
            result = calculate_two_lane(inputs)
            self.output.delete("1.0", "end")
            self.output.insert("1.0", "=== TWO-LANE HIGHWAY RESULTS ===\n\n")
            for key, value in result.items():
                if key != "steps":
                    self.output.insert("end", f"{key}: {value}\n")
            
            # Show detailed calculations button
            if "steps" in result:
                self.output.insert("end", "\n")
                btn = tk.Button(self.output, text="View Step-by-Step Calculations", 
                               command=lambda: self.show_steps_window(result["steps"]))
                self.output.window_create("end", window=btn)
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def show_steps_window(self, steps_text):
        """Display step-by-step calculations in a new window."""
        steps_window = tk.Toplevel(self)
        steps_window.title("Step-by-Step Calculations")
        steps_window.geometry("700x600")
        steps_window.configure(bg="#f0f0f0")
        
        # Header
        header = tk.Frame(steps_window, bg="#2c3e50", height=50)
        header.pack(fill="x", side="top")
        tk.Label(header, text="Detailed Calculation Steps", 
                 font=font.Font(family="Segoe UI", size=14, weight="bold"),
                 bg="#2c3e50", fg="white").pack(pady=12)
        
        # Text area with scrollbar
        text_frame = tk.Frame(steps_window, bg="white")
        text_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        text_widget = tk.Text(text_frame, wrap="word", font=font.Font(family="Consolas", size=9),
                             yscrollcommand=scrollbar.set, bg="#f9f9f9", padx=15, pady=15)
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)
        
        text_widget.insert("1.0", steps_text)
        text_widget.config(state="disabled")  # Make read-only
        
        # Close button
        btn_frame = tk.Frame(steps_window, bg="#f0f0f0")
        btn_frame.pack(fill="x", padx=15, pady=10)
        ttk.Button(btn_frame, text="Close", command=steps_window.destroy).pack()


if __name__ == "__main__":
    app = LOSCalculatorApp()
    app.mainloop()
