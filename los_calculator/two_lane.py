"""HCM 7 Chapter 15: Two-Lane Highways."""
import math
from typing import Dict, List, Tuple

from .common import clamp


# Exhibit 15-5: passing lane capacity (veh/h) by heavy vehicle % bin and vertical class
PASSING_LANE_CAPACITY = [
    (5, (1500, 1500, 1500, 1500, 1500)),
    (10, (1500, 1500, 1500, 1500, 1400)),
    (15, (1400, 1400, 1400, 1300, 1300)),
    (20, (1300, 1300, 1300, 1300, 1200)),
    (25, (1300, 1300, 1300, 1200, 1100)),
    (float("inf"), (1100, 1100, 1100, 1100, 1100)),
]
TWO_LANE_CAPACITY = 1700  # Passing Constrained and Passing Zone segments (veh/h)

# Exhibit 15-6: follower density LOS thresholds (followers/mi/ln)
FD_THRESHOLDS = {
    "high": [(2.0, "A"), (4.0, "B"), (8.0, "C"), (12.0, "D")],   # posted speed >= 50 mi/h
    "low": [(2.5, "A"), (5.0, "B"), (10.0, "C"), (15.0, "D")],   # posted speed < 50 mi/h
}

# Exhibit 15-10: (min, max) segment length (mi) by segment type and vertical class
SEGMENT_LENGTH_LIMITS = {
    "Passing Constrained": {1: (0.25, 3.0), 2: (0.25, 3.0), 3: (0.25, 1.1), 4: (0.5, 3.0), 5: (0.5, 3.0)},
    "Passing Zone": {1: (0.25, 2.0), 2: (0.25, 2.0), 3: (0.25, 1.1), 4: (0.5, 2.0), 5: (0.5, 2.0)},
    "Passing Lane": {1: (0.5, 3.0), 2: (0.5, 3.0), 3: (0.5, 1.1), 4: (0.5, 3.0), 5: (0.5, 3.0)},
}

# Exhibit 15-11: vertical class as (upgrade, downgrade).
# Rows: length ≤0.1, ≤0.2, ..., ≤1.1, >1.1 mi. Columns: grade ≤1, ≤2, ..., ≤9, >9 %.
VERTICAL_CLASS = [
    ["11", "11", "11", "11", "11", "11", "11", "21", "22", "22"],
    ["11", "11", "11", "11", "21", "22", "22", "32", "33", "33"],
    ["11", "11", "11", "21", "22", "32", "33", "43", "44", "55"],
    ["11", "11", "21", "22", "32", "33", "44", "54", "55", "55"],
    ["11", "11", "21", "22", "33", "43", "54", "55", "55", "55"],
    ["11", "11", "21", "32", "33", "44", "55", "55", "55", "55"],
    ["11", "11", "21", "32", "43", "44", "55", "55", "55", "55"],
    ["11", "11", "21", "33", "44", "54", "55", "55", "55", "55"],
    ["11", "11", "21", "33", "44", "55", "55", "55", "55", "55"],
    ["11", "11", "22", "33", "44", "55", "55", "55", "55", "55"],
    ["11", "11", "22", "33", "44", "55", "55", "55", "55", "55"],
    ["11", "11", "22", "44", "44", "55", "55", "55", "55", "55"],
]

# Exhibit 15-12: a0..a5 for Equation 15-4
COEF_A = {
    1: (0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000),
    2: (-0.45036, 0.00814, 0.01543, 0.01358, 0.00000, 0.00000),
    3: (-0.29591, 0.00743, 0.00000, 0.01246, 0.00000, 0.00000),
    4: (-0.40902, 0.00975, 0.00767, -0.18363, 0.00423, 0.00000),
    5: (-0.38360, 0.01074, 0.01945, -0.69848, 0.01069, 0.12700),
}

# Exhibits 15-13/15-14: b0..b5 for Equation 15-8 (None = use Equation 15-9 / 15-10)
COEF_B = {
    False: {
        1: (0.0558, 0.0542, 0.3278, 0.1029, 0.0000, 0.0000),
        2: (5.7280, -0.0809, 0.7404, None, None, 3.1155),
        3: (9.3079, -0.1706, 1.1292, None, None, 3.1155),
        4: (9.0115, -0.1994, 1.8252, None, None, 3.2685),
        5: (23.9144, -0.6925, 1.9473, None, None, 3.5115),
    },
    True: {
        1: (-1.1379, 0.0941, 0.0000, None, None, 0.0000),
        2: (-2.0688, 0.1053, 0.0000, None, None, 0.0000),
        3: (-0.5074, 0.0935, 0.0000, 0.0000, None, 0.0000),
        4: (8.0354, -0.0860, 0.0000, None, None, 4.1900),
        5: (7.2991, -0.3535, 0.0000, None, None, 4.8700),
    },
}

# Exhibits 15-15/15-16: c0..c3 for Equation 15-9
COEF_C = {
    False: {
        1: (0.1029, 0.0000, 0.0000, 0.0000),
        2: (-13.8036, 0.0000, 0.2446, 0.0000),
        3: (-11.9703, 0.0000, 0.2542, 0.0000),
        4: (-12.5113, 0.0000, 0.2656, 0.0000),
        5: (-14.8961, 0.0000, 0.4370, 0.0000),
    },
    True: {
        1: (0.0000, 0.2667, 0.0000, 0.0000),
        2: (0.0000, 0.4479, 0.0000, 0.0000),
        3: (0.0000, 0.0000, 0.0000, 0.0000),
        4: (-27.1244, 11.5196, 0.4681, -0.1873),
        5: (-45.3391, 17.3749, 1.0587, -0.3729),
    },
}

# Exhibits 15-17/15-18: d0..d3 for Equation 15-10
COEF_D = {
    False: {
        1: (0.0000, 0.0000, 0.0000, 0.0000),
        2: (-1.7765, 0.0000, 0.0392, 0.0000),
        3: (-3.5550, 0.0000, 0.0826, 0.0000),
        4: (-5.7775, 0.0000, 0.1373, 0.0000),
        5: (-18.2910, 2.3875, 0.4494, -0.0520),
    },
    True: {
        1: (0.0000, 0.1252, 0.0000, 0.0000),
        2: (0.0000, 0.1631, 0.0000, 0.0000),
        3: (0.0000, -0.2201, 0.0000, 0.0072),
        4: (0.0000, -0.7506, 0.0000, 0.0193),
        5: (3.8457, -0.9112, 0.0000, 0.0170),
    },
}

# Exhibits 15-19/15-20: f0..f8 for Equation 15-11
COEF_F = {
    False: {
        1: (0.67576, 0.00000, 0.00000, 0.12060, -0.35919, 0.00000, 0.00000, 0.00000, 0.00000),
        2: (0.34524, 0.00591, 0.02031, 0.14911, -0.43784, -0.00296, 0.02956, 0.00000, 0.41622),
        3: (0.17291, 0.00917, 0.05698, 0.27734, -0.61893, -0.00918, 0.09184, 0.00000, 0.41622),
        4: (0.67689, 0.00534, -0.13037, 0.25699, -0.68465, -0.00709, 0.07087, 0.00000, 0.33950),
        5: (1.13262, 0.00000, -0.26367, 0.18811, -0.64304, -0.00867, 0.08675, 0.00000, 0.30590),
    },
    True: {
        1: (0.91793, -0.00557, 0.36862, 0.00000, 0.00000, 0.00611, 0.00000, -0.00419, 0.00000),
        2: (0.65105, 0.00000, 0.34931, 0.00000, 0.00000, 0.00722, 0.00000, -0.00391, 0.00000),
        3: (0.40117, 0.00000, 0.68633, 0.00000, 0.00000, 0.02350, 0.00000, -0.02088, 0.00000),
        4: (1.13282, -0.00798, 0.35425, 0.00000, 0.00000, 0.01521, 0.00000, -0.00987, 0.00000),
        5: (1.12077, -0.00550, 0.25431, 0.00000, 0.00000, 0.01269, 0.00000, -0.01053, 0.00000),
    },
}

# Exhibits 15-24/15-25: b0..b7 for percent followers at capacity (Eq. 15-18 / 15-19)
COEF_PF_CAP = {
    False: {
        1: (37.68080, 3.05089, -7.90866, -0.94321, 13.64266, -0.00050, -0.05500, 7.13758),
        2: (58.21104, 5.73387, -13.66293, -0.66126, 9.08575, -0.00950, -0.03602, 7.14619),
        3: (113.20439, 10.01778, -18.90000, 0.46542, -6.75338, -0.03000, -0.05800, 10.03239),
        4: (58.29978, -0.53611, 7.35076, -0.27046, 4.49850, -0.01100, -0.02968, 8.89680),
        5: (3.32968, -0.84377, 7.08952, -1.32089, 19.98477, -0.01250, -0.02960, 9.99453),
    },
    True: {
        1: (61.73075, 6.73922, -23.68853, -0.84126, 11.44533, -1.05124, 1.50390, 0.00491),
        2: (12.30096, 9.57465, -30.79427, -1.79448, 25.76436, -0.66350, 1.26039, -0.00323),
        3: (206.07369, -4.29885, 0.00000, 1.96483, -30.32556, -0.75812, 1.06453, -0.00839),
        4: (263.13428, 5.38749, -19.04859, 2.73018, -42.76919, -1.31277, -0.32242, 0.01412),
        5: (126.95629, 5.95754, -19.22229, 0.43238, -7.35636, -1.03017, -2.66026, 0.01389),
    },
}

# Exhibits 15-26/15-27: c0..c7 for percent followers at 25% of capacity (Eq. 15-20 / 15-21)
COEF_PF_25 = {
    False: {
        1: (18.01780, 10.00000, -21.60000, -0.97853, 12.05214, -0.00750, -0.06700, 11.60405),
        2: (47.83887, 12.80000, -28.20000, -0.61758, 5.80000, -0.04550, -0.03344, 11.35573),
        3: (125.40000, 19.50000, -34.90000, 0.90672, -16.10000, -0.11000, -0.06200, 14.71136),
        4: (103.13534, 14.68459, -23.72704, 0.66444, -11.95763, -0.10000, 0.00172, 14.70067),
        5: (89.00000, 19.02642, -34.54240, 0.29792, -6.62528, -0.16000, 0.00480, 17.56611),
    },
    True: {
        1: (80.37105, 14.44997, -46.41831, -0.23367, 0.84914, -0.56747, 0.89427, 0.00119),
        2: (18.37886, 14.71856, -47.78892, -1.43373, 18.32040, -0.13226, 0.77217, -0.00778),
        3: (239.98930, 15.90683, -46.87525, 2.73582, -42.88130, -0.53746, 0.76271, -0.00428),
        4: (223.68435, 10.26908, -35.60830, 2.31877, -38.30034, -0.60275, -0.67758, 0.00117),
        5: (137.37633, 11.00106, -38.89043, 0.78501, -14.88672, -0.72576, -2.49546, 0.00872),
    },
}

# Exhibit 15-28: d1, d2 for Equation 15-22; Exhibit 15-29: e0..e4 for Equation 15-23
COEF_PF_M = {False: (-0.29764, -0.71917), True: (-0.15808, -0.83732)}
COEF_PF_P = {
    False: (0.81165, 0.37920, -0.49524, -2.11289, 2.41146),
    True: (-1.63246, 1.64960, -4.45823, -4.89119, 10.33057),
}

# Exhibit 15-22: horizontal class by radius (ft, lower bound) and superelevation bin (<1, ≥1, ..., ≥10 %).
# 0 means the curve does not restrict speed (treated as a tangent).
HORIZONTAL_CLASS = [
    (0, (5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5)),
    (300, (4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4)),
    (450, (4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3)),
    (600, (3, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2)),
    (750, (2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2)),
    (900, (2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1)),
    (1050, (2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1)),
    (1200, (2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1)),
    (1350, (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0)),
    (1500, (1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0)),
    (1650, (1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0)),
    (1800, (1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0)),
    (1950, (1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0)),
    (2100, (1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0)),
    (2250, (1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0)),
    (2400, (1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)),
    (2550, (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)),
]


def vertical_class(length_mi: float, grade_pct: float) -> int:
    """Exhibit 15-11 (downgrades use the value in parentheses)."""
    g = abs(grade_pct)
    col = 0 if g <= 1 else min(math.ceil(g - 1e-9) - 1, 9)
    row = 0 if length_mi <= 0.1 else min(math.ceil(length_mi * 10 - 1e-9) - 1, 11)
    entry = VERTICAL_CLASS[row][col]
    return int(entry[1] if grade_pct < 0 else entry[0])


def horizontal_class(radius_ft: float, superelevation_pct: float) -> int:
    col = int(clamp(math.floor(superelevation_pct), 0, 10))
    cls = 0
    for lower, values in HORIZONTAL_CLASS:
        if radius_ft >= lower:
            cls = values[col]
    return cls


def passing_lane_capacity(hv_pct: float, v_class: int) -> int:
    for upper, caps in PASSING_LANE_CAPACITY:
        if hv_pct < upper:
            return caps[v_class - 1]
    return PASSING_LANE_CAPACITY[-1][1][v_class - 1]


def two_lane_free_flow_speed(bffs: float, hv: float, length: float, vo: float, v_class: int,
                             lane_width: float, shoulder_width: float, apd: float) -> Tuple[float, float, float, float]:
    """Equations 15-3 to 15-6. Returns (FFS, a, fLS, fA)."""
    a0, a1, a2, a3, a4, a5 = COEF_A[v_class]
    a = max(0.0333, a0 + a1 * bffs + a2 * length + max(0.0, a3 + a4 * bffs + a5 * length) * vo / 1000)
    f_ls = 0.6 * (12 - clamp(lane_width, 9, 12)) + 0.7 * (6 - clamp(shoulder_width, 0, 6))
    f_a = min(apd / 4, 10)
    return bffs - a * hv - f_ls - f_a, a, f_ls, f_a


def two_lane_average_speed(ffs: float, vd: float, vo: float, length: float, hv: float,
                           v_class: int, passing_lane: bool) -> Tuple[float, float, float]:
    """Equations 15-7 to 15-11. Returns (S, m, p)."""
    b0, b1, b2, b3, b4, b5 = COEF_B[passing_lane][v_class]
    if b3 is None:
        c0, c1, c2, c3 = COEF_C[passing_lane][v_class]
        b3 = c0 + c1 * math.sqrt(length) + c2 * ffs + c3 * ffs * math.sqrt(length)
    if b4 is None:
        d0, d1, d2, d3 = COEF_D[passing_lane][v_class]
        b4 = d0 + d1 * math.sqrt(hv) + d2 * ffs + d3 * ffs * math.sqrt(hv)
    m = max(b5, b0 + b1 * ffs + b2 * math.sqrt(vo / 1000) + max(0.0, b3) * math.sqrt(length)
            + max(0.0, b4) * math.sqrt(hv))
    f0, f1, f2, f3, f4, f5, f6, f7, f8 = COEF_F[passing_lane][v_class]
    p = max(f8, f0 + f1 * ffs + f2 * length + f3 * vo / 1000 + f4 * math.sqrt(vo / 1000)
            + f5 * hv + f6 * math.sqrt(hv) + f7 * length * hv)
    if vd <= 100:
        return ffs, m, p
    return ffs - m * (vd / 1000 - 0.1) ** p, m, p


def two_lane_percent_followers(ffs: float, vd: float, vo: float, length: float, hv: float, v_class: int,
                               passing_lane: bool, cap: float) -> Tuple[float, float, float, float, float]:
    """Equations 15-17 to 15-23. Returns (PF, PFcap, PF25cap, m, p)."""
    b = COEF_PF_CAP[passing_lane][v_class]
    c = COEF_PF_25[passing_lane][v_class]
    sl, sf = math.sqrt(length), math.sqrt(ffs)
    if passing_lane:
        tail_b = b[6] * math.sqrt(hv) + b[7] * ffs * hv
        tail_c = c[6] * math.sqrt(hv) + c[7] * ffs * hv
    else:
        tail_b = b[6] * ffs * vo / 1000 + b[7] * math.sqrt(vo / 1000)
        tail_c = c[6] * ffs * vo / 1000 + c[7] * math.sqrt(vo / 1000)
    pf_cap = b[0] + b[1] * length + b[2] * sl + b[3] * ffs + b[4] * sf + b[5] * hv + tail_b
    pf_25 = c[0] + c[1] * length + c[2] * sl + c[3] * ffs + c[4] * sf + c[5] * hv + tail_c
    pf_cap, pf_25 = clamp(pf_cap, 0, 100), clamp(pf_25, 0, 100)

    # ln(1 - PF/100) is undefined at 100%, so cap the fitting points just below it
    x25 = -math.log(1 - min(pf_25, 99.99) / 100) / (0.25 * cap / 1000)
    xcap = -math.log(1 - min(pf_cap, 99.99) / 100) / (cap / 1000)
    d1, d2 = COEF_PF_M[passing_lane]
    e0, e1, e2, e3, e4 = COEF_PF_P[passing_lane]
    m = d1 * x25 + d2 * xcap
    p = e0 + e1 * x25 + e2 * xcap + e3 * math.sqrt(x25) + e4 * math.sqrt(xcap)
    pf = 100 * (1 - math.exp(m * (vd / 1000) ** p))
    return pf, pf_cap, pf_25, m, p


def parse_curves(text: str) -> List[Tuple[float, float, float]]:
    """Parse 'radius, superelevation, length; ...' (ft, %, ft)."""
    curves = []
    for chunk in text.split(";"):
        if not chunk.strip():
            continue
        parts = [float(x) for x in chunk.replace(",", " ").split()]
        if len(parts) != 3:
            raise ValueError(f"Horizontal curve '{chunk.strip()}' must be: radius, superelevation, length")
        curves.append(tuple(parts))
    return curves


def fd_los(fd: float, posted_speed: float) -> str:
    for threshold, grade in FD_THRESHOLDS["high" if posted_speed >= 50 else "low"]:
        if fd <= threshold:
            return grade
    return "E"


def calculate_two_lane(inputs: Dict) -> Dict:
    seg_type = inputs["segment_type"]
    actual_length = inputs["length"]
    grade = inputs["grade"]
    posted = inputs["posted_speed"]
    phf = inputs["phf"]
    hv = inputs["hv"]

    steps = ["=== TWO-LANE HIGHWAY SEGMENT (HCM 7, Chapter 15) - STEP BY STEP ===\n"]

    # Step 3 is evaluated first because Step 2 needs the vertical class for passing lane capacity
    v_class = vertical_class(actual_length, grade)
    min_len, max_len = SEGMENT_LENGTH_LIMITS[seg_type][v_class]
    if seg_type == "Passing Lane" and actual_length < min_len:
        steps.append(f"Passing lane shorter than {min_len} mi → analyzed as a Passing Constrained segment (Step 1)")
        seg_type = "Passing Constrained"
        min_len, max_len = SEGMENT_LENGTH_LIMITS[seg_type][v_class]
    passing_lane = seg_type == "Passing Lane"

    steps.append("\n--- STEP 1: Segment ---")
    steps.append(f"Segment type: {seg_type}, length = {actual_length} mi, grade = {grade}%")

    steps.append("\n--- STEP 2: Demand Flow Rates, Capacity, d/c ---")
    vd = inputs["volume"] / phf
    steps.append(f"vd = Vd / PHF = {inputs['volume']:.0f} / {phf} = {vd:.0f} veh/h  (Eq. 15-1)")
    if seg_type == "Passing Zone":
        if "opposing_volume" not in inputs:
            raise ValueError("Opposing-direction volume is required for Passing Zone segments")
        vo = inputs["opposing_volume"] / phf
        steps.append(f"vo = Vo / PHF = {inputs['opposing_volume']:.0f} / {phf} = {vo:.0f} veh/h")
    elif passing_lane:
        vo = 0.0
        steps.append("vo = 0 veh/h for Passing Lane segments")
    else:
        vo = 1500.0
        steps.append("vo = 1,500 veh/h for Passing Constrained segments")
    if passing_lane:
        cap = passing_lane_capacity(hv, v_class)
        steps.append(f"Capacity = {cap} veh/h (Exhibit 15-5, {hv}% HV, vertical class {v_class})")
    else:
        cap = TWO_LANE_CAPACITY
        steps.append(f"Capacity = {cap} veh/h")
    dc = vd / cap
    steps.append(f"d/c = {vd:.0f} / {cap} = {dc:.3f}")

    result = {"Vertical class": v_class, "vd (veh/h)": round(vd), "Capacity (veh/h)": cap, "d/c": round(dc, 3)}
    if vd > cap:
        steps.append("Demand exceeds capacity → LOS F; the analysis stops here")
        result["LOS"] = "F"
        result["steps"] = "\n".join(steps)
        return result

    steps.append("\n--- STEP 3: Vertical Alignment Classification ---")
    direction = "downgrade" if grade < 0 else "upgrade"
    steps.append(f"|grade| = {abs(grade)}% ({direction}), length = {actual_length} mi → vertical class {v_class} (Exhibit 15-11)")
    length = clamp(actual_length, min_len, max_len)
    steps.append(f"Length limits (Exhibit 15-10): {min_len}-{max_len} mi → L used in Steps 4-9 = {length} mi")

    steps.append("\n--- STEP 4: Free-Flow Speed ---")
    bffs = 1.14 * posted
    steps.append(f"BFFS = 1.14 × {posted} = {bffs:.2f} mi/h  (Eq. 15-2)")
    est_ffs, a, f_ls, f_a = two_lane_free_flow_speed(bffs, hv, length, vo, v_class, inputs["lane_width"],
                                                     inputs["shoulder_width"], inputs["access_points"])
    if "measured_ffs" in inputs:
        ffs = inputs["measured_ffs"]
        steps.append(f"Measured FFS = {ffs:.2f} mi/h")
    else:
        ffs = est_ffs
        steps.append(f"a = {a:.4f}  (Eq. 15-4)")
        steps.append(f"fLS = 0.6 × (12 - LW) + 0.7 × (6 - SW) = {f_ls:.2f} mi/h  (Eq. 15-5)")
        steps.append(f"fA = min(APD / 4, 10) = {f_a:.2f} mi/h  (Eq. 15-6)")
        steps.append(f"FFS = {bffs:.2f} - {a:.4f} × {hv} - {f_ls:.2f} - {f_a:.2f} = {ffs:.2f} mi/h  (Eq. 15-3)")

    steps.append("\n--- STEP 5: Average Speed ---")
    speed, m_s, p_s = two_lane_average_speed(ffs, vd, vo, length, hv, v_class, passing_lane)
    steps.append(f"Slope coefficient m = {m_s:.4f}  (Eq. 15-8)")
    steps.append(f"Power coefficient p = {p_s:.4f}  (Eq. 15-11)")
    if vd <= 100:
        steps.append(f"vd ≤ 100 veh/h → S = FFS = {speed:.2f} mi/h")
    else:
        steps.append(f"S = FFS - m × (vd/1000 - 0.1)^p = {ffs:.2f} - {m_s:.4f} × ({vd/1000:.3f} - 0.1)^{p_s:.4f} = {speed:.2f} mi/h  (Eq. 15-7)")

    curves = parse_curves(inputs.get("curves", ""))
    if curves:
        steps.append("\nStep 5d: Adjust speed for horizontal alignment")
        length_ft = actual_length * 5280
        curve_length = sum(c[2] for c in curves)
        if curve_length > length_ft:
            raise ValueError("Total horizontal curve length exceeds the segment length")
        weighted = (length_ft - curve_length) * speed
        for i, (radius, superelevation, c_len) in enumerate(curves, 1):
            h_class = horizontal_class(radius, superelevation)
            if h_class == 0:
                s_hc = speed
                steps.append(f"  Curve {i}: R = {radius:.0f} ft, e = {superelevation}% → no speed restriction (tangent)")
            else:
                bffs_hc = min(bffs, 44.32 + 0.3728 * bffs - 6.868 * h_class)
                ffs_hc = bffs_hc - 0.0255 * hv
                m_hc = max(0.277, -25.8993 - 0.7756 * ffs_hc + 10.6294 * math.sqrt(ffs_hc)
                           + 2.4766 * h_class - 9.8238 * math.sqrt(h_class))
                s_hc = min(speed, ffs_hc - m_hc * math.sqrt(max(vd / 1000 - 0.1, 0.0)))
                steps.append(f"  Curve {i}: R = {radius:.0f} ft, e = {superelevation}% → horizontal class {h_class}")
                steps.append(f"    BFFS_HC = {bffs_hc:.2f}, FFS_HC = {ffs_hc:.2f}, m = {m_hc:.4f}, S_HC = {s_hc:.2f} mi/h  (Eqs. 15-12 to 15-15)")
            weighted += c_len * s_hc
        speed = weighted / length_ft
        steps.append(f"  Length-weighted segment speed S = {speed:.2f} mi/h  (Eq. 15-16)")

    steps.append("\n--- STEP 6: Percent Followers ---")
    pf, pf_cap, pf_25, m_pf, p_pf = two_lane_percent_followers(ffs, vd, vo, length, hv, v_class, passing_lane, cap)
    steps.append(f"PFcap = {pf_cap:.2f}%  (Eq. {'15-19' if passing_lane else '15-18'})")
    steps.append(f"PF25cap = {pf_25:.2f}%  (Eq. {'15-21' if passing_lane else '15-20'})")
    steps.append(f"m = {m_pf:.4f}  (Eq. 15-22),  p = {p_pf:.4f}  (Eq. 15-23)")
    steps.append(f"PF = 100 × [1 - exp(m × (vd/1000)^p)] = {pf:.2f}%  (Eq. 15-17)")

    fd = pf / 100 * vd / speed
    result.update({"FFS (mi/h)": round(ffs, 2), "Average speed (mi/h)": round(speed, 2),
                   "Percent followers (%)": round(pf, 2)})

    if passing_lane:
        steps.append("\n--- STEP 7: Passing Lane Performance at Midpoint ---")
        num_hv = vd * hv / 100
        prop_fl = 0.92183 - 0.05022 * math.log(vd) - 0.00030 * num_hv
        flow_fl = vd * prop_fl
        flow_sl = vd * (1 - prop_fl)
        hv_fl = hv * 0.4
        num_hv_sl = num_hv - flow_fl * hv_fl / 100
        hv_sl = num_hv_sl / flow_sl * 100
        steps.append(f"NumHV = {num_hv:.1f} veh, PropFlowRateFL = {prop_fl:.3f}  (Eqs. 15-24, 15-25)")
        steps.append(f"Faster lane: {flow_fl:.0f} veh/h, {hv_fl:.1f}% HV;  slower lane: {flow_sl:.0f} veh/h, {hv_sl:.1f}% HV  (Eqs. 15-26 to 15-30)")
        # Each lane is evaluated with its own HV%, which changes its FFS (Eq. 15-3) and capacity (Exhibit 15-5)
        ffs_fl = ffs - a * (hv_fl - hv)
        ffs_sl = ffs - a * (hv_sl - hv)
        cap_fl = passing_lane_capacity(hv_fl, v_class)
        cap_sl = passing_lane_capacity(hv_sl, v_class)
        steps.append(f"Lane FFS: FL = {ffs_fl:.2f}, SL = {ffs_sl:.2f} mi/h; lane capacity: FL = {cap_fl}, SL = {cap_sl} veh/h")
        s_fl, _, _ = two_lane_average_speed(ffs_fl, flow_fl, vo, length, hv_fl, v_class, True)
        s_sl, _, _ = two_lane_average_speed(ffs_sl, flow_sl, vo, length, hv_sl, v_class, True)
        diff = 2.750 + 0.00056 * vd + 3.8521 * hv / 100
        s_mid_fl = s_fl + diff / 2
        s_mid_sl = s_sl - diff / 2
        steps.append(f"Sinit_FL = {s_fl:.2f}, Sinit_SL = {s_sl:.2f} mi/h; AvgSpeedDiffAdj = {diff:.2f} mi/h  (Eq. 15-31)")
        steps.append(f"S_PLmid_FL = {s_mid_fl:.2f}, S_PLmid_SL = {s_mid_sl:.2f} mi/h  (Eqs. 15-32, 15-33)")
        pf_fl = two_lane_percent_followers(ffs_fl, flow_fl, vo, length, hv_fl, v_class, True, cap_fl)[0]
        pf_sl = two_lane_percent_followers(ffs_sl, flow_sl, vo, length, hv_sl, v_class, True, cap_sl)[0]
        steps.append(f"PF_PLmid_FL = {pf_fl:.2f}%, PF_PLmid_SL = {pf_sl:.2f}%")

        steps.append("\n--- STEP 8: Follower Density ---")
        fd_mid = (pf_fl / 100 * flow_fl / s_mid_fl + pf_sl / 100 * flow_sl / s_mid_sl) / 2
        steps.append(f"FD_PLmid = {fd_mid:.2f} followers/mi/ln  (Eq. 15-34) → used for the segment LOS")
        steps.append(f"FD at end of passing lane = PF/100 × vd/S = {fd:.2f} followers/mi/ln  (Eq. 15-35)")
        result["FD at end (followers/mi/ln)"] = round(fd, 2)
        fd = fd_mid
    else:
        steps.append("\n--- STEP 8: Follower Density ---")
        steps.append(f"FD = PF/100 × vd/S = {pf:.2f}/100 × {vd:.0f}/{speed:.2f} = {fd:.2f} followers/mi/ln  (Eq. 15-35)")

        if "pl_length" in inputs and "pl_distance" in inputs and "pl_pf_in" in inputs:
            steps.append("\n--- STEP 9: Adjustment for Upstream Passing Lane ---")
            pl_len = inputs["pl_length"]
            dist = inputs["pl_distance"]
            pf_in = inputs["pl_pf_in"]
            flow_in = inputs.get("pl_flow_in", vd)

            def improve_pf(d: float, flow: float) -> float:
                return max(0.0, 27 - 8.75 * math.log(max(0.1, d)) + 0.1 * max(0.0, pf_in - 30)
                           + 3.5 * math.log(max(0.3, pl_len)) - 0.01 * flow)

            def improve_s(d: float, flow: float) -> float:
                return max(0.0, 3 - 0.8 * d + 0.1 * max(0.0, pf_in - 30) + 0.75 * pl_len - 0.005 * flow)

            # Effective length: %ImprovePF reaches zero, or FDadj recovers to 95% of the entering FD
            # (the entering speed cancels out of that ratio)
            eff_pf = math.exp((27 + 0.1 * max(0.0, pf_in - 30) + 3.5 * math.log(max(0.3, pl_len))
                               - 0.01 * flow_in) / 8.75)
            eff_fd = eff_pf
            d = 0.01
            while d < eff_pf:
                if (1 - improve_pf(d, flow_in) / 100) / (1 + improve_s(d, flow_in) / 100) >= 0.95:
                    eff_fd = d
                    break
                d += 0.01
            eff_len = min(eff_pf, eff_fd)
            steps.append(f"Effective length of upstream passing lane = {eff_len:.2f} mi")
            if dist <= eff_len:
                i_pf = improve_pf(dist, vd)
                i_s = improve_s(dist, vd)
                fd = pf / 100 * (1 - i_pf / 100) * vd / (speed * (1 + i_s / 100))
                steps.append(f"%ImprovePF = {i_pf:.2f}%  (Eq. 15-36),  %ImproveS = {i_s:.2f}%  (Eq. 15-37)")
                steps.append(f"FDadj = {fd:.2f} followers/mi/ln  (Eq. 15-38)")
            else:
                steps.append(f"Segment ({dist} mi downstream) is beyond the effective length → no adjustment")

    steps.append("\n--- STEP 10: Determine LOS ---")
    speed_group = "higher-speed (posted ≥ 50 mi/h)" if posted >= 50 else "lower-speed (posted < 50 mi/h)"
    los = fd_los(fd, posted)
    if posted >= 50:
        steps.append("Thresholds (Exhibit 15-6): A ≤2.0, B ≤4.0, C ≤8.0, D ≤12.0, E >12.0")
    else:
        steps.append("Thresholds (Exhibit 15-6): A ≤2.5, B ≤5.0, C ≤10.0, D ≤15.0, E >15.0")
    steps.append(f"FD = {fd:.2f} followers/mi/ln on a {speed_group} highway → LOS {los}")

    result["Follower density (followers/mi/ln)"] = round(fd, 2)
    result["LOS"] = los
    result["steps"] = "\n".join(steps)
    return result
