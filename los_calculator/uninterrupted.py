"""HCM 7 Chapter 12: Basic Freeway and Multilane Highway Segments."""
from typing import Dict, List, Tuple

from .common import clamp, linear_interpolate


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
