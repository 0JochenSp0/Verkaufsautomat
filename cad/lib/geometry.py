"""Carousel sector geometry – pure Python, no FreeCAD dependency.

Model (top view): carousel of outer radius R, divided into N equal wedge-shaped
sectors by radial divider walls of thickness `wall`. An item must fit inside a
wedge keeping `clearance` to each divider face, to the rim stop and to the hub.

All lengths in mm, angles in degrees unless suffixed `_rad`.
Used by: cad/macros/*.py (FreeCAD) and software (sector count / step math).
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PARAMS = Path(__file__).resolve().parents[1] / "params" / "params.json"


@dataclass(frozen=True)
class Allowances:
    wall: float = 4.0          # divider wall thickness
    clearance: float = 5.0     # free play around the item on every side
    rim_margin: float = 6.0    # rim lip / stop at the outer edge
    hub_radius: float = 30.0   # no item may extend inside this radius


@dataclass(frozen=True)
class Rect:
    """Rectangular item (egg carton). width = tangential, depth = radial."""
    width: float
    depth: float
    height: float = 0.0


@dataclass(frozen=True)
class Circle:
    """Round item (jar), placed upright."""
    diameter: float
    height: float = 0.0


def _min_half_angle_rect(R: float, w: float, d: float, a: Allowances) -> float | None:
    """Smallest wedge half-angle (rad) that holds rectangle w x d, or None if impossible."""
    r_eff = R - a.rim_margin - a.clearance          # outer edge of the item may reach this radius
    half_w = w / 2
    if half_w >= r_eff:
        return None
    x_out = math.sqrt(r_eff**2 - half_w**2)          # outer corners on the circle r_eff
    x_in = x_out - d                                 # inner edge distance from centre
    if x_in < a.hub_radius + a.clearance:
        return None
    # Inner corner (x_in, half_w) must be at distance >= t from the wedge edge line at angle alpha:
    #   x_in*sin(alpha) - half_w*cos(alpha) >= t
    t = a.wall / 2 + a.clearance
    rho = math.hypot(x_in, half_w)
    if t > rho:
        return None
    return math.atan2(half_w, x_in) + math.asin(t / rho)


def _min_half_angle_circle(R: float, dia: float, a: Allowances) -> float | None:
    r = dia / 2
    c = R - a.rim_margin - a.clearance - r           # centre distance of the jar
    if c - r < a.hub_radius + a.clearance or c <= 0:
        return None
    t = a.wall / 2 + a.clearance
    s = (r + t) / c                                  # c*sin(alpha) >= r + t
    if s >= 1:
        return None
    return math.asin(s)


def _n_from_half_angle(alpha: float | None) -> int:
    if alpha is None:
        return 0
    # tiny epsilon so exact fits are not lost to float rounding
    return int(math.floor(math.pi / alpha + 1e-9))


def sectors_for_rect(R: float, item: Rect, a: Allowances, allow_rotated: bool = True) -> int:
    n = _n_from_half_angle(_min_half_angle_rect(R, item.width, item.depth, a))
    if allow_rotated:
        n = max(n, _n_from_half_angle(_min_half_angle_rect(R, item.depth, item.width, a)))
    return n


def sectors_for_circle(R: float, item: Circle, a: Allowances) -> int:
    return _n_from_half_angle(_min_half_angle_circle(R, item.diameter, a))


def best_rect_orientation(R: float, item: Rect, a: Allowances, allow_rotated: bool = True) -> Rect:
    """Return the orientation (as Rect with width=tangential) that yields more sectors."""
    if not allow_rotated:
        return item
    rot = Rect(item.depth, item.width, item.height)
    return rot if sectors_for_rect(R, rot, a, False) > sectors_for_rect(R, item, a, False) else item


def chord(R: float, angle_deg: float) -> float:
    return 2 * R * math.sin(math.radians(angle_deg) / 2)


@dataclass(frozen=True)
class CarouselLayout:
    diameter: float
    levels: int
    sectors_per_level: int
    sectors_egg: int
    sectors_jar: int
    sector_angle_deg: float
    level_pitch: float
    total_height: float
    fits_height: bool
    window_width: float
    window_height: float
    window_ok: bool
    egg_boxes_stackable: int

    @property
    def total_positions(self) -> int:
        return self.levels * self.sectors_per_level


def carousel_diameter(p: dict) -> float:
    f = p["fridge_inner"]
    by_width = f["width"] - 2 * f["side_clearance"]
    by_depth = f["depth"] - f["rear_clearance"] - f["door_clearance"]
    return float(min(by_width, by_depth))


def allowances_from(p: dict) -> Allowances:
    c = p["carousel"]
    return Allowances(
        wall=c["divider_wall"],
        clearance=c["item_clearance"],
        rim_margin=c["rim_margin"],
        hub_radius=c["hub_diameter"] / 2,
    )


def layout(p: dict, diameter: float | None = None) -> CarouselLayout:
    """Compute the universal carousel layout from a params dict."""
    a = allowances_from(p)
    c = p["carousel"]
    D = diameter if diameter is not None else carousel_diameter(p)
    R = D / 2
    eb = p["products"]["egg_box"]
    hj = p["products"]["honey_jar"]
    egg = Rect(eb["width"], eb["depth"], eb["height"])
    jar = Circle(hj["diameter"], hj["height"])

    n_egg = sectors_for_rect(R, egg, a, eb.get("allow_rotated", True))
    n_jar = sectors_for_circle(R, jar, a)
    n_auto = min(n_egg, n_jar)
    spl = c.get("sectors_per_level", "auto")
    n = n_auto if spl in (None, "auto") else int(spl)
    if n > n_auto:
        raise ValueError(f"sectors_per_level={n} exceeds geometric maximum {n_auto}")

    item_h = max(egg.height, jar.height)
    pitch = item_h + c["level_headroom"] + c["floor_thickness"]
    total_h = c["bottom_space"] + c["levels"] * pitch + c["top_space"]
    fits_h = total_h <= p["fridge_inner"]["height"]

    sector_angle = 360.0 / n if n else 0.0
    eo = best_rect_orientation(R, egg, a, eb.get("allow_rotated", True))
    widest = max(eo.width, jar.diameter)
    win_w = widest + 2 * a.clearance + p["door"]["window_extra"]
    win_h = item_h + c["level_headroom"] / 2
    # The window must not expose more than one sector: it has to stay narrower than the
    # free chord of a sector at the rim (chord minus one divider wall).
    window_ok = bool(n) and win_w <= chord(R, sector_angle) - a.wall

    stack = int((jar.height + c["level_headroom"] - a.clearance) // egg.height) if egg.height else 1

    return CarouselLayout(
        diameter=D, levels=c["levels"], sectors_per_level=n,
        sectors_egg=n_egg, sectors_jar=n_jar, sector_angle_deg=sector_angle,
        level_pitch=pitch, total_height=total_h, fits_height=fits_h,
        window_width=win_w, window_height=win_h, window_ok=window_ok,
        egg_boxes_stackable=max(stack, 1),
    )


def load_params(path: str | Path = DEFAULT_PARAMS) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _report(p: dict) -> str:
    L = layout(p)
    lines = [
        f"Karussell-Durchmesser      : {L.diameter:.0f} mm (aus Innenmaßen)",
        f"Sektoren/Ebene (universal) : {L.sectors_per_level}  [Eier: {L.sectors_egg}, Glas: {L.sectors_jar}]",
        f"Positionen gesamt          : {L.total_positions} ({L.levels} Ebenen)",
        f"Sektorwinkel               : {L.sector_angle_deg:.1f}°",
        f"Ebenenteilung / Höhe       : {L.level_pitch:.0f} mm / {L.total_height:.0f} mm "
        f"({'passt' if L.fits_height else 'ZU HOCH'})",
        f"Klappenfenster B×H         : {L.window_width:.0f} × {L.window_height:.0f} mm "
        f"({'ok' if L.window_ok else 'ZU BREIT – legt Nachbarsektor frei'})",
        f"Eierschachteln stapelbar   : {L.egg_boxes_stackable} je Sektor (Höhe durch Glas vorgegeben)",
        "",
        "Sweep Durchmesser → Sektoren/Ebene (universal):",
    ]
    for D in range(360, 621, 30):
        s = layout(p, diameter=D)
        lines.append(f"  Ø{D:4d} mm: {s.sectors_per_level:2d}/Ebene = {s.total_positions:2d} gesamt "
                     f"(Eier {s.sectors_egg}, Glas {s.sectors_jar})")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Carousel sector calculator")
    ap.add_argument("--params", default=str(DEFAULT_PARAMS))
    args = ap.parse_args(argv)
    print(_report(load_params(args.params)))


if __name__ == "__main__":
    main()
