import math
import tkinter as tk
from tkinter import ttk, messagebox, font
from typing import Dict, List, Optional, Tuple

# All procedures follow the Highway Capacity Manual, 7th Edition (HCM 7):
#   Chapter 12 - Basic Freeway and Multilane Highway Segments
#   Chapter 15 - Two-Lane Highways
# All inputs are in U.S. customary units (ft, mi, mi/h, veh/h).

# ---------- Mode constants ----------

VOLUME_MODES = ["Directional volume", "Two-way volume"]
ANALYSIS_MODES = ["Calculate LOS", "Design for Target LOS"]
TERRAIN_TYPES = ["Level", "Rolling", "Specific grade"]
SEGMENT_TYPES = ["Passing Constrained", "Passing Zone", "Passing Lane"]

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


def clamp(x: float, low: float, high: float) -> float:
    return max(low, min(x, high))


# =====================================================================
# Chapter 12: Basic Freeway and Multilane Highway Segments
# =====================================================================

# Exhibit 12-20: reduction in FFS for average lane width (ft >= threshold -> mi/h)
LANE_WIDTH_REDUCTION = [
    (12, 0.0),
    (11, 1.9),
    (0, 6.6),
]

# Exhibit 12-21: right-side lateral clearance reduction, by lanes in one direction
RIGHT_CLEARANCE_RED = {
    2: {6: 0.0, 5: 0.6, 4: 1.2, 3: 1.8, 2: 2.4, 1: 3.0, 0: 3.6},
    3: {6: 0.0, 5: 0.4, 4: 0.8, 3: 1.2, 2: 1.6, 1: 2.0, 0: 2.4},
    4: {6: 0.0, 5: 0.2, 4: 0.4, 3: 0.6, 2: 0.8, 1: 1.0, 0: 1.2},
    5: {6: 0.0, 5: 0.1, 4: 0.2, 3: 0.3, 2: 0.4, 1: 0.5, 0: 0.6},
}

# Exhibit 12-22: total lateral clearance reduction for multilane highways
TOTAL_CLEARANCE_RED = {
    "Four-lane": {12: 0.0, 10: 0.4, 8: 0.9, 6: 1.3, 4: 1.8, 2: 3.6, 0: 5.4},
    "Six-lane": {12: 0.0, 10: 0.4, 8: 0.9, 6: 1.3, 4: 1.7, 2: 2.8, 0: 3.9},
}

# Exhibit 12-23: median type reduction
MEDIAN_REDUCTION = {"Undivided": 1.6, "TWLTL": 0.0, "Divided": 0.0}

# Exhibit 12-24: access point density reduction
ACCESS_POINT_REDUCTION = {0: 0.0, 10: 2.5, 20: 5.0, 30: 7.5, 40: 10.0}

# Exhibit 12-25: PCEs for general terrain segments
PCE_GENERAL_TERRAIN = {"Level": 2.0, "Rolling": 3.0}

# Exhibits 12-26 to 12-28: PCEs for specific grades.
# {truck mix: {grade %: {length mi: (PCE at each % trucks in TRUCK_PCT_COLUMNS)}}}
TRUCK_PCT_COLUMNS = [2, 4, 5, 6, 8, 10, 15, 20, 25]
PCE_SPECIFIC_GRADE = {
    "30% SUT / 70% TT": {
        -2: {
            0.125: (2.62, 2.37, 2.30, 2.24, 2.17, 2.12, 2.04, 1.99, 1.97),
            0.375: (2.62, 2.37, 2.30, 2.24, 2.17, 2.12, 2.04, 1.99, 1.97),
            0.625: (2.62, 2.37, 2.30, 2.24, 2.17, 2.12, 2.04, 1.99, 1.97),
            0.875: (2.62, 2.37, 2.30, 2.24, 2.17, 2.12, 2.04, 1.99, 1.97),
            1.25: (2.62, 2.37, 2.30, 2.24, 2.17, 2.12, 2.04, 1.99, 1.97),
            1.5: (2.62, 2.37, 2.30, 2.24, 2.17, 2.12, 2.04, 1.99, 1.97),
        },
        0: {
            0.125: (2.62, 2.37, 2.30, 2.24, 2.17, 2.12, 2.04, 1.99, 1.97),
            0.375: (2.62, 2.37, 2.30, 2.24, 2.17, 2.12, 2.04, 1.99, 1.97),
            0.625: (2.62, 2.37, 2.30, 2.24, 2.17, 2.12, 2.04, 1.99, 1.97),
            0.875: (2.62, 2.37, 2.30, 2.24, 2.17, 2.12, 2.04, 1.99, 1.97),
            1.25: (2.62, 2.37, 2.30, 2.24, 2.17, 2.12, 2.04, 1.99, 1.97),
            1.5: (2.62, 2.37, 2.30, 2.24, 2.17, 2.12, 2.04, 1.99, 1.97),
        },
        2: {
            0.125: (2.62, 2.37, 2.30, 2.24, 2.17, 2.12, 2.04, 1.99, 1.97),
            0.375: (3.76, 2.96, 2.78, 2.65, 2.48, 2.38, 2.22, 2.14, 2.09),
            0.625: (4.47, 3.33, 3.08, 2.91, 2.68, 2.54, 2.34, 2.23, 2.17),
            0.875: (4.80, 3.50, 3.22, 3.03, 2.77, 2.61, 2.39, 2.28, 2.21),
            1.25: (5.00, 3.60, 3.30, 3.09, 2.83, 2.66, 2.42, 2.30, 2.23),
            1.5: (5.04, 3.62, 3.32, 3.11, 2.84, 2.67, 2.43, 2.31, 2.23),
        },
        2.5: {
            0.125: (2.62, 2.37, 2.30, 2.24, 2.17, 2.12, 2.04, 1.99, 1.97),
            0.375: (4.11, 3.14, 2.93, 2.78, 2.58, 2.46, 2.28, 2.19, 2.13),
            0.625: (5.04, 3.62, 3.32, 3.11, 2.84, 2.67, 2.43, 2.31, 2.23),
            0.875: (5.48, 3.85, 3.51, 3.27, 2.96, 2.77, 2.50, 2.36, 2.28),
            1.25: (5.73, 3.98, 3.61, 3.36, 3.03, 2.83, 2.54, 2.40, 2.31),
            1.5: (5.80, 4.02, 3.64, 3.38, 3.05, 2.84, 2.55, 2.41, 2.32),
        },
        3.5: {
            0.125: (2.62, 2.37, 2.30, 2.24, 2.17, 2.12, 2.04, 1.99, 1.97),
            0.375: (4.88, 3.54, 3.25, 3.05, 2.80, 2.63, 2.41, 2.29, 2.22),
            0.625: (6.34, 4.30, 3.87, 3.58, 3.20, 2.97, 2.64, 2.48, 2.38),
            0.875: (7.03, 4.66, 4.16, 3.83, 3.39, 3.12, 2.76, 2.57, 2.46),
            1.25: (7.44, 4.87, 4.33, 3.97, 3.50, 3.22, 2.82, 2.62, 2.50),
            1.5: (7.53, 4.92, 4.38, 4.01, 3.53, 3.24, 2.84, 2.63, 2.51),
        },
        4.5: {
            0.125: (2.62, 2.37, 2.30, 2.24, 2.17, 2.12, 2.04, 1.99, 1.97),
            0.375: (5.80, 4.02, 3.64, 3.38, 3.05, 2.84, 2.55, 2.41, 2.32),
            0.625: (7.90, 5.11, 4.53, 4.14, 3.63, 3.32, 2.90, 2.68, 2.55),
            0.875: (8.91, 5.64, 4.96, 4.50, 3.92, 3.56, 3.07, 2.82, 2.67),
            1: (9.19, 5.78, 5.08, 4.60, 3.99, 3.62, 3.11, 2.85, 2.70),
        },
        5.5: {
            0.125: (2.62, 2.37, 2.30, 2.24, 2.17, 2.12, 2.04, 1.99, 1.97),
            0.375: (6.87, 4.58, 4.10, 3.77, 3.35, 3.09, 2.73, 2.55, 2.44),
            0.625: (9.78, 6.09, 5.33, 4.82, 4.16, 3.76, 3.21, 2.93, 2.77),
            0.875: (11.20, 6.83, 5.94, 5.33, 4.56, 4.09, 3.45, 3.12, 2.93),
            1: (11.60, 7.04, 6.11, 5.47, 4.67, 4.18, 3.51, 3.17, 2.97),
        },
        6: {
            0.125: (2.62, 2.37, 2.30, 2.24, 2.17, 2.12, 2.04, 1.99, 1.97),
            0.375: (7.48, 4.90, 4.36, 3.99, 3.52, 3.23, 2.83, 2.63, 2.51),
            0.625: (10.87, 6.66, 5.79, 5.21, 4.46, 4.01, 3.39, 3.08, 2.89),
            0.875: (12.54, 7.54, 6.51, 5.81, 4.94, 4.40, 3.67, 3.30, 3.08),
            1: (13.02, 7.78, 6.71, 5.99, 5.07, 4.51, 3.75, 3.37, 3.14),
        },
    },
    "50% SUT / 50% TT": {
        -2: {
            0.125: (2.67, 2.38, 2.31, 2.25, 2.16, 2.11, 2.02, 1.97, 1.93),
            0.375: (2.67, 2.38, 2.31, 2.25, 2.16, 2.11, 2.02, 1.97, 1.93),
            0.625: (2.67, 2.38, 2.31, 2.25, 2.16, 2.11, 2.02, 1.97, 1.93),
            0.875: (2.67, 2.38, 2.31, 2.25, 2.16, 2.11, 2.02, 1.97, 1.93),
            1.25: (2.67, 2.38, 2.31, 2.25, 2.16, 2.11, 2.02, 1.97, 1.93),
            1.5: (2.67, 2.38, 2.31, 2.25, 2.16, 2.11, 2.02, 1.97, 1.93),
        },
        0: {
            0.125: (2.67, 2.38, 2.31, 2.25, 2.16, 2.11, 2.02, 1.97, 1.93),
            0.375: (2.67, 2.38, 2.31, 2.25, 2.16, 2.11, 2.02, 1.97, 1.93),
            0.625: (2.67, 2.38, 2.31, 2.25, 2.16, 2.11, 2.02, 1.97, 1.93),
            0.875: (2.67, 2.38, 2.31, 2.25, 2.16, 2.11, 2.02, 1.97, 1.93),
            1.25: (2.67, 2.38, 2.31, 2.25, 2.16, 2.11, 2.02, 1.97, 1.93),
            1.5: (2.67, 2.38, 2.31, 2.25, 2.16, 2.11, 2.02, 1.97, 1.93),
        },
        2: {
            0.125: (2.67, 2.38, 2.31, 2.25, 2.16, 2.11, 2.02, 1.97, 1.93),
            0.375: (3.76, 2.95, 2.77, 2.64, 2.47, 2.36, 2.20, 2.11, 2.06),
            0.625: (4.32, 3.24, 3.01, 2.84, 2.63, 2.49, 2.29, 2.19, 2.12),
            0.875: (4.57, 3.37, 3.11, 2.93, 2.70, 2.55, 2.33, 2.22, 2.15),
            1.25: (4.71, 3.45, 3.17, 2.99, 2.74, 2.58, 2.36, 2.24, 2.17),
            1.5: (4.74, 3.47, 3.19, 3.00, 2.75, 2.59, 2.36, 2.24, 2.17),
        },
        2.5: {
            0.125: (2.67, 2.38, 2.31, 2.25, 2.16, 2.11, 2.02, 1.97, 1.93),
            0.375: (4.10, 3.13, 2.92, 2.77, 2.57, 2.44, 2.26, 2.16, 2.10),
            0.625: (4.84, 3.52, 3.23, 3.03, 2.77, 2.61, 2.38, 2.26, 2.18),
            0.875: (5.17, 3.69, 3.37, 3.15, 2.87, 2.69, 2.43, 2.30, 2.22),
            1.25: (5.36, 3.79, 3.45, 3.22, 2.92, 2.73, 2.47, 2.33, 2.24),
            1.5: (5.40, 3.81, 3.47, 3.24, 2.93, 2.74, 2.47, 2.33, 2.25),
        },
        3.5: {
            0.125: (2.67, 2.38, 2.31, 2.25, 2.16, 2.11, 2.02, 1.97, 1.93),
            0.375: (4.89, 3.54, 3.25, 3.05, 2.79, 2.62, 2.39, 2.26, 2.19),
            0.625: (6.05, 4.15, 3.75, 3.47, 3.11, 2.89, 2.58, 2.42, 2.32),
            0.875: (6.58, 4.43, 3.97, 3.66, 3.26, 3.01, 2.67, 2.49, 2.39),
            1.25: (6.88, 4.58, 4.10, 3.77, 3.35, 3.09, 2.72, 2.53, 2.42),
            1.5: (6.95, 4.62, 4.13, 3.80, 3.37, 3.10, 2.73, 2.54, 2.43),
        },
        4.5: {
            0.125: (2.67, 2.38, 2.31, 2.25, 2.16, 2.11, 2.02, 1.97, 1.93),
            0.375: (5.83, 4.03, 3.65, 3.39, 3.05, 2.84, 2.55, 2.39, 2.30),
            0.625: (7.53, 4.92, 4.38, 4.01, 3.53, 3.24, 2.83, 2.62, 2.50),
            0.875: (8.32, 5.34, 4.72, 4.29, 3.75, 3.42, 2.97, 2.73, 2.59),
            1: (8.53, 5.45, 4.81, 4.37, 3.81, 3.47, 3.00, 2.76, 2.62),
        },
        5.5: {
            0.125: (2.67, 2.38, 2.31, 2.25, 2.16, 2.11, 2.02, 1.97, 1.93),
            0.375: (6.97, 4.63, 4.14, 3.81, 3.38, 3.11, 2.74, 2.55, 2.43),
            0.625: (9.37, 5.89, 5.16, 4.68, 4.05, 3.67, 3.14, 2.88, 2.72),
            0.875: (10.49, 6.48, 5.65, 5.09, 4.37, 3.93, 3.34, 3.03, 2.85),
            1: (10.80, 6.64, 5.78, 5.20, 4.46, 4.01, 3.39, 3.08, 2.89),
        },
        6: {
            0.125: (2.67, 2.38, 2.31, 2.25, 2.16, 2.11, 2.02, 1.97, 1.93),
            0.375: (7.64, 4.98, 4.43, 4.05, 3.56, 3.26, 2.85, 2.64, 2.51),
            0.625: (10.45, 6.45, 5.63, 5.07, 4.36, 3.92, 3.33, 3.03, 2.85),
            0.875: (11.78, 7.16, 6.20, 5.56, 4.74, 4.24, 3.56, 3.22, 3.01),
            1: (12.15, 7.35, 6.36, 5.69, 4.85, 4.33, 3.62, 3.27, 3.05),
        },
    },
    "70% SUT / 30% TT": {
        -2: {
            0.125: (2.39, 2.18, 2.12, 2.07, 2.01, 1.96, 1.89, 1.85, 1.83),
            0.375: (2.39, 2.18, 2.12, 2.07, 2.01, 1.96, 1.89, 1.85, 1.83),
            0.625: (2.39, 2.18, 2.12, 2.07, 2.01, 1.96, 1.89, 1.85, 1.83),
            0.875: (2.39, 2.18, 2.12, 2.07, 2.01, 1.96, 1.89, 1.85, 1.83),
            1.25: (2.39, 2.18, 2.12, 2.07, 2.01, 1.96, 1.89, 1.85, 1.83),
            1.5: (2.39, 2.18, 2.12, 2.07, 2.01, 1.96, 1.89, 1.85, 1.83),
        },
        0: {
            0.125: (2.39, 2.18, 2.12, 2.07, 2.01, 1.96, 1.89, 1.85, 1.83),
            0.375: (2.39, 2.18, 2.12, 2.07, 2.01, 1.96, 1.89, 1.85, 1.83),
            0.625: (2.39, 2.18, 2.12, 2.07, 2.01, 1.96, 1.89, 1.85, 1.83),
            0.875: (2.39, 2.18, 2.12, 2.07, 2.01, 1.96, 1.89, 1.85, 1.83),
            1.25: (2.39, 2.18, 2.12, 2.07, 2.01, 1.96, 1.89, 1.85, 1.83),
            1.5: (2.39, 2.18, 2.12, 2.07, 2.01, 1.96, 1.89, 1.85, 1.83),
        },
        2: {
            0.125: (2.67, 2.32, 2.23, 2.17, 2.08, 2.03, 1.94, 1.89, 1.86),
            0.375: (3.63, 2.82, 2.64, 2.52, 2.35, 2.25, 2.10, 2.02, 1.97),
            0.625: (4.12, 3.08, 2.85, 2.69, 2.49, 2.36, 2.18, 2.08, 2.02),
            0.875: (4.37, 3.21, 2.96, 2.78, 2.56, 2.42, 2.22, 2.11, 2.05),
            1.25: (4.53, 3.29, 3.02, 2.84, 2.60, 2.45, 2.24, 2.13, 2.07),
            1.5: (4.58, 3.31, 3.04, 2.86, 2.61, 2.46, 2.25, 2.14, 2.07),
        },
        2.5: {
            0.125: (2.75, 2.36, 2.27, 2.20, 2.11, 2.04, 1.95, 1.90, 1.87),
            0.375: (4.01, 3.02, 2.80, 2.65, 2.46, 2.33, 2.16, 2.06, 2.01),
            0.625: (4.66, 3.35, 3.08, 2.88, 2.64, 2.48, 2.26, 2.15, 2.08),
            0.875: (4.99, 3.52, 3.21, 3.00, 2.73, 2.56, 2.32, 2.19, 2.12),
            1.25: (5.20, 3.64, 3.30, 3.08, 2.79, 2.60, 2.35, 2.22, 2.14),
            1.5: (5.26, 3.67, 3.33, 3.10, 2.80, 2.62, 2.36, 2.23, 2.15),
        },
        3.5: {
            0.125: (2.93, 2.45, 2.34, 2.26, 2.16, 2.09, 1.98, 1.92, 1.89),
            0.375: (4.86, 3.46, 3.16, 2.96, 2.69, 2.53, 2.30, 2.18, 2.10),
            0.625: (5.88, 3.99, 3.59, 3.32, 2.98, 2.76, 2.46, 2.31, 2.22),
            0.875: (6.40, 4.26, 3.81, 3.51, 3.12, 2.88, 2.55, 2.38, 2.28),
            1.25: (6.74, 4.43, 3.96, 3.63, 3.21, 2.96, 2.60, 2.42, 2.32),
            1.5: (6.83, 4.48, 3.99, 3.66, 3.24, 2.98, 2.62, 2.44, 2.33),
        },
        4.5: {
            0.125: (3.13, 2.56, 2.43, 2.34, 2.21, 2.13, 2.01, 1.95, 1.91),
            0.375: (5.88, 3.99, 3.59, 3.32, 2.98, 2.76, 2.46, 2.31, 2.22),
            0.625: (7.35, 4.75, 4.22, 3.85, 3.39, 3.10, 2.71, 2.51, 2.39),
            0.875: (8.11, 5.15, 4.54, 4.13, 3.60, 3.27, 2.83, 2.61, 2.47),
            1: (8.33, 5.27, 4.63, 4.21, 3.66, 3.33, 2.87, 2.64, 2.50),
        },
        5.5: {
            0.125: (3.37, 2.69, 2.53, 2.42, 2.28, 2.19, 2.05, 1.98, 1.94),
            0.375: (7.09, 4.62, 4.11, 3.76, 3.31, 3.04, 2.66, 2.47, 2.36),
            0.625: (9.13, 5.68, 4.97, 4.49, 3.88, 3.51, 3.00, 2.74, 2.59),
            0.875: (10.21, 6.24, 5.43, 4.88, 4.18, 3.76, 3.18, 2.89, 2.71),
            1: (10.52, 6.41, 5.57, 5.00, 4.27, 3.83, 3.24, 2.93, 2.75),
        },
        6: {
            0.125: (3.51, 2.76, 2.59, 2.47, 2.32, 2.22, 2.08, 2.00, 1.95),
            0.375: (7.78, 4.98, 4.40, 4.01, 3.51, 3.20, 2.78, 2.56, 2.44),
            0.625: (10.17, 6.23, 5.42, 4.87, 4.17, 3.75, 3.18, 2.88, 2.71),
            0.875: (11.43, 6.88, 5.95, 5.32, 4.53, 4.04, 3.39, 3.06, 2.86),
            1: (11.81, 7.08, 6.11, 5.46, 4.64, 4.13, 3.45, 3.11, 2.90),
        },
    },
}

FREEWAY_BFFS = 75.4           # default base FFS for basic freeway segments (mi/h)
DENSITY_AT_CAPACITY = 45.0    # Dc (pc/mi/ln)
MULTILANE_BREAKPOINT = 1400   # BP (pc/h/ln)

# Exhibit 12-15: LOS criteria (density, pc/mi/ln)
LOS_THRESHOLDS = [
    (11, "A"),
    (18, "B"),
    (26, "C"),
    (35, "D"),
    (45, "E"),
]


def lane_width_adjustment(width_ft: float) -> float:
    for threshold, value in LANE_WIDTH_REDUCTION:
        if width_ft >= threshold:
            return value
    return LANE_WIDTH_REDUCTION[-1][1]


def right_clearance_adjustment(clearance_ft: float, lanes: int) -> float:
    table = RIGHT_CLEARANCE_RED[int(clamp(lanes, 2, 5))]
    return linear_interpolate(clamp(clearance_ft, 0, 6), table)


def total_clearance_adjustment(tlc_ft: float, lanes: int) -> float:
    table = TOTAL_CLEARANCE_RED["Four-lane" if lanes <= 2 else "Six-lane"]
    return linear_interpolate(clamp(tlc_ft, 0, 12), table)


def specific_grade_pce(grade: float, length: float, truck_pct: float, mix: str) -> float:
    """Trilinear interpolation in Exhibits 12-26 to 12-28 (interpolation is permitted)."""
    table = PCE_SPECIFIC_GRADE[mix]
    truck_points = lambda row: dict(zip(TRUCK_PCT_COLUMNS, row))

    def at_grade(g: float) -> float:
        rows = table[g]
        by_length = {L: linear_interpolate(truck_pct, truck_points(vals)) for L, vals in rows.items()}
        return linear_interpolate(length, by_length)

    grades = sorted(table.keys())
    grade = clamp(grade, grades[0], grades[-1])
    for g0, g1 in zip(grades, grades[1:]):
        if g0 <= grade <= g1:
            e0, e1 = at_grade(g0), at_grade(g1)
            return e0 + (grade - g0) / (g1 - g0) * (e1 - e0)
    return at_grade(grades[-1])


def los_from_density(density: float) -> str:
    for threshold, grade in LOS_THRESHOLDS:
        if density <= threshold:
            return grade
    return "F"


def heavy_vehicle_factor(inputs: Dict, steps: List[str]) -> Tuple[float, float]:
    """Equation 12-10 with PCEs from Exhibit 12-25 or Exhibits 12-26 to 12-28."""
    hv_pct = inputs["trucks"]
    terrain = inputs["terrain"]
    steps.append(f"Heavy vehicles (SUTs + TTs; buses and RVs count as SUTs): {hv_pct}%")
    if terrain in PCE_GENERAL_TERRAIN:
        et = PCE_GENERAL_TERRAIN[terrain]
        steps.append(f"General terrain: {terrain} → ET = {et} (Exhibit 12-25)")
    else:
        grade = inputs["grade"]
        length = inputs["grade_length"]
        mix = inputs["truck_mix"]
        et = specific_grade_pce(grade, length, hv_pct, mix)
        steps.append(f"Specific grade: {grade}% over {length} mi, truck mix {mix}")
        if grade < -2:
            steps.append("  Downgrades steeper than 2% use the -2% PCE values")
        if grade > 3.5 and length > 1:
            steps.append("  Grades above 3.5% are tabulated up to 1 mi; 1 mi values used")
        if grade > 6:
            steps.append("  Note: grade exceeds the 6% table limit; 6% values used")
        steps.append(f"  ET = {et:.2f} (interpolated from Exhibits 12-26 to 12-28)")
    pt = hv_pct / 100.0
    f_hv = 1.0 / (1.0 + pt * (et - 1.0))
    steps.append(f"fHV = 1 / [1 + {pt:.3f} × ({et:.2f} - 1)] = {f_hv:.3f}  (Eq. 12-10)")
    return et, f_hv


def directional_volume(inputs: Dict, steps: List[str]) -> float:
    volume = inputs["volume"]
    if inputs.get("is_two_way", False):
        split = inputs.get("directional_split", 50.0) / 100.0
        steps.append(f"Two-way volume: {volume:.0f} veh/h, split toward analysis direction: {split*100:.1f}%")
        volume = volume * split
    steps.append(f"Directional demand volume V = {volume:.0f} veh/h")
    return volume


def speed_flow(vp: float, ffs: float, cap: float, bp: float, a: float) -> float:
    """Equation 12-1."""
    if vp <= bp or cap <= bp:
        return ffs
    return ffs - (ffs - cap / DENSITY_AT_CAPACITY) * (vp - bp) ** a / (cap - bp) ** a


def finish_uninterrupted(steps: List[str], vp: float, ffs: float, cap: float, bp: float, a: float,
                         result: Dict) -> Dict:
    """Steps 4 (LOS F check), 5 and 6 shared by freeways and multilane highways."""
    vc = vp / cap
    result["v/c"] = round(vc, 3)
    steps.append(f"\nCheck for LOS F: v/c = {vp:.0f} / {cap:.0f} = {vc:.3f}")
    if vp > cap:
        steps.append("Demand exceeds capacity → LOS F (analyze with Chapter 10 for queue impacts)")
        result.update({"Speed (mi/h)": "N/A", "Density (pc/mi/ln)": "N/A", "LOS": "F"})
        result["steps"] = "\n".join(steps)
        return result

    steps.append("\n--- STEP 5: Estimate Speed and Density ---")
    steps.append(f"Breakpoint BP = {bp:.0f} pc/h/ln, exponent a = {a}")
    speed = speed_flow(vp, ffs, cap, bp, a)
    if vp <= bp:
        steps.append(f"vp ({vp:.0f}) ≤ BP ({bp:.0f}) → S = FFS = {speed:.2f} mi/h")
    else:
        steps.append(f"vp ({vp:.0f}) > BP ({bp:.0f}) → Eq. 12-1:")
        steps.append(f"S = {ffs:.2f} - ({ffs:.2f} - {cap:.0f}/45) × ({vp:.0f} - {bp:.0f})^{a} / ({cap:.0f} - {bp:.0f})^{a}")
        steps.append(f"S = {speed:.2f} mi/h")
    density = vp / speed
    steps.append(f"D = vp / S = {vp:.0f} / {speed:.2f} = {density:.2f} pc/mi/ln  (Eq. 12-11)")

    steps.append("\n--- STEP 6: Determine LOS ---")
    los = los_from_density(density)
    steps.append("LOS thresholds (Exhibit 12-15): A ≤11, B ≤18, C ≤26, D ≤35, E ≤45, F >45 or v/c > 1")
    steps.append(f"Level of Service: {los}")
    result.update({"Speed (mi/h)": round(speed, 2), "Density (pc/mi/ln)": round(density, 2), "LOS": los})
    result["steps"] = "\n".join(steps)
    return result


def calculate_freeway(inputs: Dict) -> Dict:
    lanes = int(inputs["lanes"])
    saf = inputs.get("saf", 1.0)
    caf = inputs.get("caf", 1.0)

    steps = ["=== BASIC FREEWAY SEGMENT (HCM 7, Chapter 12) - STEP BY STEP ===\n"]

    steps.append("\n--- STEP 2: Estimate and Adjust FFS ---")
    if "measured_ffs" in inputs:
        ffs = inputs["measured_ffs"]
        steps.append(f"Measured FFS = {ffs:.2f} mi/h (no adjustments applied)")
    else:
        lane_adj = lane_width_adjustment(inputs["lane_width"])
        clearance_adj = right_clearance_adjustment(inputs["lateral_clearance"], lanes)
        trd = inputs["ramp_density"]
        ramp_adj = 3.22 * trd ** 0.84
        ffs = FREEWAY_BFFS - lane_adj - clearance_adj - ramp_adj
        steps.append(f"BFFS = {FREEWAY_BFFS} mi/h")
        steps.append(f"Lane width {inputs['lane_width']:.1f} ft → fLW = {lane_adj} mi/h (Exhibit 12-20)")
        if inputs["lane_width"] < 10:
            steps.append("  Note: lane widths below 10 ft are outside the HCM range")
        steps.append(f"Right clearance {inputs['lateral_clearance']:.1f} ft, {lanes} lanes → fRLC = {clearance_adj:.2f} mi/h (Exhibit 12-21)")
        steps.append(f"Ramp term = 3.22 × TRD^0.84 = 3.22 × {trd:.2f}^0.84 = {ramp_adj:.2f} mi/h")
        steps.append(f"FFS = {FREEWAY_BFFS} - {lane_adj} - {clearance_adj:.2f} - {ramp_adj:.2f} = {ffs:.2f} mi/h  (Eq. 12-2)")
    if not 55 <= ffs <= 75:
        steps.append("  Note: the method covers freeway FFS of 55-75 mi/h")
    ffs_adj = ffs * saf
    steps.append(f"FFSadj = FFS × SAF = {ffs:.2f} × {saf} = {ffs_adj:.2f} mi/h  (Eq. 12-5)")

    steps.append("\n--- STEP 3: Estimate and Adjust Capacity ---")
    # Capacity follows the adjusted FFS (HCM 7 Example Problem 6), with FFS capped at 75 mi/h
    ffs_cap = min(ffs_adj, 75)
    cap = min(2200 + 10 * (ffs_cap - 50), 2400)
    cap_adj = cap * caf
    steps.append(f"c = 2,200 + 10 × (FFSadj - 50) = 2,200 + 10 × ({ffs_cap:.2f} - 50) = {cap:.0f} pc/h/ln (≤ 2,400)  (Eq. 12-6)")
    steps.append(f"cadj = c × CAF = {cap:.0f} × {caf} = {cap_adj:.0f} pc/h/ln  (Eq. 12-8)")

    steps.append("\n--- STEP 4: Adjust Demand Volume ---")
    volume = directional_volume(inputs, steps)
    et, f_hv = heavy_vehicle_factor(inputs, steps)
    phf = inputs["phf"]
    vp = volume / (phf * lanes * f_hv)
    steps.append(f"vp = V / (PHF × N × fHV) = {volume:.0f} / ({phf} × {lanes} × {f_hv:.3f}) = {vp:.2f} pc/h/ln  (Eq. 12-9)")

    bp = (1000 + 40 * (75 - ffs_adj)) * caf ** 2
    result = {
        "FFS (mi/h)": round(ffs, 2),
        "FFSadj (mi/h)": round(ffs_adj, 2),
        "Capacity (pc/h/ln)": round(cap_adj),
        "ET": round(et, 2),
        "fHV": round(f_hv, 3),
        "vp (pc/h/ln)": round(vp, 2),
    }
    steps.append(f"BPadj = [1,000 + 40 × (75 - {ffs_adj:.2f})] × {caf}² = {bp:.0f} pc/h/ln")
    return finish_uninterrupted(steps, vp, ffs_adj, cap_adj, bp, 2.0, result)


def calculate_multilane(inputs: Dict) -> Dict:
    lanes = int(inputs["lanes"])
    median = inputs["median"]

    steps = ["=== MULTILANE HIGHWAY SEGMENT (HCM 7, Chapter 12) - STEP BY STEP ===\n"]

    steps.append("\n--- STEP 2: Estimate FFS ---")
    if "measured_ffs" in inputs:
        ffs = inputs["measured_ffs"]
        steps.append(f"Measured FFS = {ffs:.2f} mi/h (no adjustments applied)")
    else:
        bffs = inputs["bffs"]
        lane_adj = lane_width_adjustment(inputs["lane_width"])
        lc_right = min(inputs["right_clearance"], 6.0)
        lc_left = 6.0 if median in ("Undivided", "TWLTL") else min(inputs["left_clearance"], 6.0)
        tlc = lc_right + lc_left
        clearance_adj = total_clearance_adjustment(tlc, lanes)
        median_adj = MEDIAN_REDUCTION[median]
        access_adj = linear_interpolate(inputs["access_points"], ACCESS_POINT_REDUCTION)
        ffs = bffs - lane_adj - clearance_adj - median_adj - access_adj
        steps.append(f"BFFS = {bffs} mi/h")
        steps.append(f"Lane width {inputs['lane_width']:.1f} ft → fLW = {lane_adj} mi/h (Exhibit 12-20)")
        if median in ("Undivided", "TWLTL"):
            steps.append(f"{median} median → left clearance taken as 6 ft")
        steps.append(f"TLC = LCR + LCL = {lc_right:.1f} + {lc_left:.1f} = {tlc:.1f} ft  (Eq. 12-4)")
        table_name = "four-lane" if lanes <= 2 else "six-lane"
        steps.append(f"fTLC = {clearance_adj:.2f} mi/h (Exhibit 12-22, {table_name} highway)")
        steps.append(f"Median: {median} → fM = {median_adj} mi/h (Exhibit 12-23)")
        steps.append(f"Access points {inputs['access_points']:.1f}/mi → fA = {access_adj:.2f} mi/h (Exhibit 12-24)")
        steps.append(f"FFS = {bffs} - {lane_adj} - {clearance_adj:.2f} - {median_adj} - {access_adj:.2f} = {ffs:.2f} mi/h  (Eq. 12-3)")
    if not 45 <= ffs <= 70:
        steps.append("  Note: the method covers multilane FFS of 45-70 mi/h")

    steps.append("\n--- STEP 3: Estimate Capacity ---")
    ffs_cap = min(ffs, 70)
    cap = min(1900 + 20 * (ffs_cap - 45), 2300)
    steps.append(f"c = 1,900 + 20 × ({ffs_cap:.2f} - 45) = {cap:.0f} pc/h/ln (≤ 2,300)  (Eq. 12-7)")
    steps.append("(No SAF/CAF adjustments exist for multilane highways)")

    steps.append("\n--- STEP 4: Adjust Demand Volume ---")
    volume = directional_volume(inputs, steps)
    et, f_hv = heavy_vehicle_factor(inputs, steps)
    phf = inputs["phf"]
    vp = volume / (phf * lanes * f_hv)
    steps.append(f"vp = V / (PHF × N × fHV) = {volume:.0f} / ({phf} × {lanes} × {f_hv:.3f}) = {vp:.2f} pc/h/ln  (Eq. 12-9)")

    result = {
        "FFS (mi/h)": round(ffs, 2),
        "Capacity (pc/h/ln)": round(cap),
        "ET": round(et, 2),
        "fHV": round(f_hv, 3),
        "vp (pc/h/ln)": round(vp, 2),
    }
    return finish_uninterrupted(steps, vp, ffs, cap, MULTILANE_BREAKPOINT, 1.31, result)


def design_for_target_los(inputs: Dict, facility_type: str, target_los: str) -> Dict:
    """Find the minimum number of directional lanes that achieves the target LOS."""
    max_lanes = 8
    for lanes in range(2, max_lanes + 1):
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


# =====================================================================
# Chapter 15: Two-Lane Highways
# =====================================================================

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


# ---------- UI ----------

STRING_KEYS = ["volume_mode", "terrain", "median", "target_los", "truck_mix", "segment_type", "curves"]
OPTIONAL_KEYS = ["measured_ffs", "opposing_volume", "pl_length", "pl_distance", "pl_pf_in", "pl_flow_in",
                 "grade", "grade_length"]


class LOSCalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Highway Level of Service Calculator - HCM 7th Edition")
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

        self.canvas_window = self.canvas.create_window((0, 0), window=self.form_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.form_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.canvas_window, width=e.width))

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
                                 text="Based on: Highway Capacity Manual, 7th Edition (TRB, 2022) - Chapters 12 and 15",
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

    def add_combo(self, parent, label, key, values, default):
        tk.Label(parent, text=label, font=self.label_font, bg="white").pack(anchor="w", pady=(5, 2))
        box = ttk.Combobox(parent, values=values, state="readonly", font=self.entry_font)
        box.set(default)
        box.pack(fill="x", pady=(0, 5))
        self.widgets[key] = box

    def add_note(self, parent, text):
        tk.Label(parent, text=text, font=self.entry_font, bg="white", fg="#7f8c8d",
                 anchor="w", justify="left", wraplength=420).pack(fill="x", pady=(0, 5))

    def add_volume_and_traffic(self, mode, volume, phf, lanes, trucks):
        self.add_section_header(self.form_frame, "Volume Configuration")
        self.add_combo(self.form_frame, "Volume input type:", "volume_mode", VOLUME_MODES, VOLUME_MODES[0])
        self.add_field(self.form_frame, "Directional split toward analysis (%):", "directional_split", "50")

        self.add_section_header(self.form_frame, "Traffic Data")
        self.add_field(self.form_frame, "Demand volume (veh/h):", "volume", volume)
        self.add_field(self.form_frame, "Peak hour factor (PHF):", "phf", phf)

        if mode == ANALYSIS_MODES[1]:  # Design mode
            self.add_combo(self.form_frame, "Target Level of Service:", "target_los", ["A", "B", "C", "D", "E"], "C")
        else:
            self.add_field(self.form_frame, "Number of lanes (directional):", "lanes", lanes)

        self.add_field(self.form_frame, "% Heavy vehicles (SUTs + TTs, incl. buses and RVs):", "trucks", trucks)

    def add_terrain_fields(self):
        self.add_section_header(self.form_frame, "Terrain / Grade")
        self.add_combo(self.form_frame, "Terrain:", "terrain", TERRAIN_TYPES, "Level")
        self.add_note(self.form_frame, "Mountainous terrain has no PCE in HCM 7; use a specific grade instead.")
        self.add_field(self.form_frame, "Specific grade (%) (negative = downgrade):", "grade", "3")
        self.add_field(self.form_frame, "Grade length (mi):", "grade_length", "1.0")
        self.add_combo(self.form_frame, "Truck mix (specific grade):", "truck_mix",
                       list(PCE_SPECIFIC_GRADE.keys()), list(PCE_SPECIFIC_GRADE.keys())[0])

    def add_calculate_button(self, command):
        btn_frame = tk.Frame(self.form_frame, bg="white")
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Calculate", command=command).pack()

    def build_freeway_form(self, mode):
        self.widgets = {}
        self.add_volume_and_traffic(mode, "4000", "0.92", "3", "5")

        self.add_section_header(self.form_frame, "Geometric Data")
        self.add_field(self.form_frame, "Measured FFS (mi/h) - leave blank to estimate:", "measured_ffs", "")
        self.add_field(self.form_frame, "Lane width (ft):", "lane_width", "12")
        self.add_field(self.form_frame, "Right lateral clearance (ft):", "lateral_clearance", "6")
        self.add_field(self.form_frame, "Total ramp density (ramps/mi):", "ramp_density", "1.0")
        self.add_terrain_fields()

        self.add_section_header(self.form_frame, "Adjustment Factors")
        self.add_field(self.form_frame, "Speed adjustment factor (SAF):", "saf", "1.0")
        self.add_field(self.form_frame, "Capacity adjustment factor (CAF):", "caf", "1.0")
        self.add_note(self.form_frame, "SAF/CAF = 1.0 for base conditions; use Chapter 11 values for weather, "
                                       "work zones, incidents or unfamiliar drivers.")
        self.add_calculate_button(self.handle_freeway)

    def build_multilane_form(self, mode):
        self.widgets = {}
        self.add_volume_and_traffic(mode, "1900", "0.90", "2", "13")

        self.add_section_header(self.form_frame, "Geometric Data")
        self.add_field(self.form_frame, "Measured FFS (mi/h) - leave blank to estimate:", "measured_ffs", "")
        self.add_field(self.form_frame, "Base FFS (mi/h):", "bffs", "55")
        self.add_note(self.form_frame, "If unknown: posted speed + 5 mi/h (limits ≥ 50 mi/h) or + 7 mi/h (limits < 50 mi/h).")
        self.add_field(self.form_frame, "Lane width (ft):", "lane_width", "11")
        self.add_field(self.form_frame, "Right lateral clearance (ft):", "right_clearance", "4")
        self.add_field(self.form_frame, "Left lateral clearance (ft):", "left_clearance", "2")
        self.add_field(self.form_frame, "Access points per mile:", "access_points", "12")
        self.add_combo(self.form_frame, "Median type:", "median", list(MEDIAN_REDUCTION.keys()), "Undivided")
        self.add_terrain_fields()
        self.add_calculate_button(self.handle_multilane)

    def build_two_lane_form(self, mode):
        self.widgets = {}

        if mode == ANALYSIS_MODES[1]:
            messagebox.showinfo("Info", "Design mode is not available for Two-Lane Highways.\nSwitching to Calculate LOS mode.")
            self.analysis_mode_var.set(ANALYSIS_MODES[0])

        self.add_section_header(self.form_frame, "Traffic Data")
        self.add_field(self.form_frame, "Analysis-direction volume (veh/h):", "volume", "752")
        self.add_field(self.form_frame, "Opposing-direction volume (veh/h) - Passing Zone only:", "opposing_volume", "")
        self.add_field(self.form_frame, "Peak hour factor (PHF):", "phf", "0.94")
        self.add_field(self.form_frame, "% Heavy vehicles:", "hv", "5")

        self.add_section_header(self.form_frame, "Segment Data")
        self.add_combo(self.form_frame, "Segment type:", "segment_type", SEGMENT_TYPES, SEGMENT_TYPES[0])
        self.add_field(self.form_frame, "Segment length (mi):", "length", "0.75")
        self.add_field(self.form_frame, "Percent grade (%) (negative = downgrade):", "grade", "0")
        self.add_field(self.form_frame, "Posted speed limit (mi/h):", "posted_speed", "50")
        self.add_field(self.form_frame, "Measured FFS (mi/h) - leave blank to estimate:", "measured_ffs", "")
        self.add_field(self.form_frame, "Lane width (ft):", "lane_width", "12")
        self.add_field(self.form_frame, "Shoulder width (ft):", "shoulder_width", "6")
        self.add_field(self.form_frame, "Access points per mile:", "access_points", "0")

        self.add_section_header(self.form_frame, "Horizontal Curves (optional)")
        self.add_field(self.form_frame, "Curves: radius ft, superelevation %, length ft; ...", "curves", "")
        self.add_note(self.form_frame, "Example: 450, 3, 432; 300, 2, 366.5. Leave blank for a straight segment.")

        self.add_section_header(self.form_frame, "Upstream Passing Lane (optional)")
        self.add_field(self.form_frame, "Passing lane length (mi):", "pl_length", "")
        self.add_field(self.form_frame, "Distance from start of passing lane to end of this segment (mi):", "pl_distance", "")
        self.add_field(self.form_frame, "Percent followers entering the passing lane (%):", "pl_pf_in", "")
        self.add_field(self.form_frame, "Flow rate entering the passing lane (veh/h):", "pl_flow_in", "")
        self.add_calculate_button(self.handle_two_lane)

    def gather_inputs(self) -> Dict:
        inputs = {}
        # All inputs are in U.S. customary units - no conversion needed

        for key, widget in self.widgets.items():
            value = widget.get().strip()
            if key in STRING_KEYS:
                inputs[key] = value
            elif value == "" and key in OPTIONAL_KEYS:
                continue
            else:
                try:
                    inputs[key] = float(value)
                except ValueError:
                    raise ValueError(f"Please enter a valid number for '{key}' (got '{value}')")

        if "volume_mode" in inputs:
            inputs["is_two_way"] = (inputs["volume_mode"] == VOLUME_MODES[1])
        if inputs.get("terrain") == "Specific grade" and ("grade" not in inputs or "grade_length" not in inputs):
            raise ValueError("Grade (%) and grade length (mi) are required for a specific grade")

        return inputs

    def show_result(self, title, result):
        self.output.delete("1.0", "end")
        self.output.insert("1.0", f"=== {title} ===\n\n")
        for key, value in result.items():
            if key != "steps":
                self.output.insert("end", f"{key}: {value}\n")

        # Show detailed calculations button
        if "steps" in result:
            self.output.insert("end", "\n")
            btn = tk.Button(self.output, text="View Step-by-Step Calculations",
                           command=lambda: self.show_steps_window(result["steps"]))
            self.output.window_create("end", window=btn)

    def handle_design(self, inputs, facility_type):
        target_los = inputs.get("target_los", "C")
        result = design_for_target_los(inputs, facility_type, target_los)
        self.output.delete("1.0", "end")
        if "error" in result:
            self.output.insert("1.0", f"Error: {result['error']}")
            return
        self.output.insert("1.0", f"=== DESIGN RESULTS ===\n\n")
        self.output.insert("end", f"Target LOS: {target_los}\n")
        self.output.insert("end", f"Lanes Required: {result['lanes_required']}\n\n")
        self.output.insert("end", "Performance with designed lanes:\n")
        for k, v in result['result'].items():
            if k != "steps":
                self.output.insert("end", f"  {k}: {v}\n")

    def handle_freeway(self):
        try:
            inputs = self.gather_inputs()
            if self.analysis_mode_var.get() == ANALYSIS_MODES[1]:
                self.handle_design(inputs, "Freeway")
            else:
                self.show_result("BASIC FREEWAY SEGMENT RESULTS", calculate_freeway(inputs))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def handle_multilane(self):
        try:
            inputs = self.gather_inputs()
            if self.analysis_mode_var.get() == ANALYSIS_MODES[1]:
                self.handle_design(inputs, "Multilane")
            else:
                self.show_result("MULTILANE HIGHWAY RESULTS", calculate_multilane(inputs))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def handle_two_lane(self):
        try:
            inputs = self.gather_inputs()
            self.show_result("TWO-LANE HIGHWAY RESULTS", calculate_two_lane(inputs))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_steps_window(self, steps_text):
        """Display step-by-step calculations in a new window."""
        steps_window = tk.Toplevel(self)
        steps_window.title("Step-by-Step Calculations")
        steps_window.geometry("800x600")
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
