"""Shared numeric helpers."""
from typing import Dict


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
