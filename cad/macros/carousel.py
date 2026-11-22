"""FreeCAD macro: parametric carousel (3 levels) inside the fridge envelope.

Run headless:   freecadcmd cad/macros/carousel.py
Run in GUI:     Macro -> Macros... -> carousel.py   (set VENDING_REPO if __file__ is unavailable)
Output:         cad/out/carousel.FCStd, cad/out/carousel.step, cad/out/carousel_cutlist.txt

All dimensions come from cad/params/params.json via cad/lib/geometry.py – no hard-coded sizes.
Coordinate system: origin = carousel axis on the fridge floor, +Y = towards the door, +Z = up.
⚠️ Not yet executed: FreeCAD is not installed on the dev Pi (see docs/milestones.md).
"""

import math
import os
import sys

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
    REPO = os.path.abspath(os.path.join(_HERE, "..", ".."))
except NameError:  # FreeCAD GUI macro execution may not define __file__
    REPO = os.environ.get("VENDING_REPO", os.getcwd())

sys.path.insert(0, os.path.join(REPO, "cad", "lib"))

import FreeCAD as App  # noqa: E402
import Part  # noqa: E402
import geometry  # noqa: E402

V = App.Vector


def ring(r_out, r_in, h, z):
    outer = Part.makeCylinder(r_out, h, V(0, 0, z))
    inner = Part.makeCylinder(r_in, h, V(0, 0, z))
    return outer.cut(inner)


def divider(r_in, r_out, wall, h, z, angle_deg):
    """Radial wall centred on the ray at `angle_deg` (0° = +Y, i.e. the door direction)."""
    box = Part.makeBox(r_out - r_in, wall, h, V(r_in, -wall / 2, z))
    box.rotate(V(0, 0, 0), V(0, 0, 1), 90 + angle_deg)
    return box


def build(doc, p):
    L = geometry.layout(p)
    c = p["carousel"]
    R = L.diameter / 2
    wall = c["divider_wall"]
    floor_t = c["floor_thickness"]
    hub_r = c["hub_diameter"] / 2
    shaft_r = c["shaft_diameter"] / 2
    n = L.sectors_per_level
    # sector centres sit at k*angle; dividers half a sector off, so sector 0 faces the door (+Y)
    half = L.sector_angle_deg / 2

    parts = {}
    z0 = c["bottom_space"]
    for lvl in range(L.levels):
        z = z0 + lvl * L.level_pitch
        floor = Part.makeCylinder(R, floor_t, V(0, 0, z)).cut(Part.makeCylinder(shaft_r + 0.5, floor_t, V(0, 0, z)))
        parts[f"L{lvl}_floor"] = floor
        h_div = L.level_pitch - floor_t
        divs = [divider(hub_r, R, wall, h_div, z + floor_t, k * L.sector_angle_deg + half) for k in range(n)]
        d = divs[0]
        for other in divs[1:]:
            d = d.fuse(other)
        parts[f"L{lvl}_dividers"] = d
        parts[f"L{lvl}_hub"] = ring(hub_r, shaft_r + 0.5, h_div, z + floor_t)
        parts[f"L{lvl}_rim_lip"] = ring(R, R - c["rim_margin"], 12, z + floor_t)

    top_z = z0 + L.levels * L.level_pitch
    parts["top_cover"] = Part.makeCylinder(R, floor_t, V(0, 0, top_z))
    parts["shaft"] = Part.makeCylinder(shaft_r, top_z + floor_t + 30 - 20, V(0, 0, 20))

    # index magnets (one per sector, under level 0 floor) – reference geometry
    r_mag = R - p["carousel"]["index_magnet_radius_offset"]
    mags = None
    for k in range(n):
        a = math.radians(90 + k * L.sector_angle_deg)
        m = Part.makeCylinder(5, 3, V(r_mag * math.cos(a), r_mag * math.sin(a), z0 - 3))
        mags = m if mags is None else mags.fuse(m)
    parts["index_magnets"] = mags

    # door windows (reference, at the door plane) – one per level, in front of sector 0
    f = p["fridge_inner"]
    door_y = R + f["door_clearance"]
    for lvl in range(L.levels):
        z = z0 + lvl * L.level_pitch + floor_t
        parts[f"window_L{lvl}"] = Part.makeBox(L.window_width, 2, L.window_height,
                                               V(-L.window_width / 2, door_y, z))

    # fridge inner envelope (reference)
    env = Part.makeBox(f["width"], f["depth"], f["height"],
                       V(-f["width"] / 2, door_y - f["depth"], 0))
    parts["fridge_envelope"] = env

    for name, shape in parts.items():
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
    return L, parts


def cutlist(p, L):
    c = p["carousel"]
    lines = [
        f"Karussell Ø{L.diameter:.0f} mm, {L.levels} Ebenen × {L.sectors_per_level} Sektoren "
        f"({L.sector_angle_deg:.1f}°), Ebenenteilung {L.level_pitch:.0f} mm",
        f"Böden + Deckel: {L.levels + 1} × Ronde Ø{L.diameter:.0f} × {c['floor_thickness']} mm (HDPE/PP), "
        f"Bohrung Ø{c['shaft_diameter'] + 1}",
        f"Trennwände: {L.levels * L.sectors_per_level} × "
        f"{L.diameter / 2 - c['hub_diameter'] / 2:.0f} × {L.level_pitch - c['floor_thickness']:.0f} × "
        f"{c['divider_wall']} mm",
        f"Welle: Ø{c['shaft_diameter']} × ca. {c['bottom_space'] + L.levels * L.level_pitch + 40:.0f} mm Edelstahl",
        f"Klappenfenster (Tür): {L.levels} × {L.window_width:.0f} × {L.window_height:.0f} mm",
    ]
    return "\n".join(lines)


def main():
    p = geometry.load_params(os.path.join(REPO, "cad", "params", "params.json"))
    out = os.path.join(REPO, "cad", "out")
    os.makedirs(out, exist_ok=True)
    doc = App.newDocument("carousel")
    L, parts = build(doc, p)
    doc.recompute()
    if App.GuiUp:
        import FreeCADGui as Gui

        for name in ("fridge_envelope",) + tuple(k for k in parts if k.startswith("window_")):
            doc.getObject(name).ViewObject.Transparency = 80
        Gui.SendMsgToActiveView("ViewFit")
    doc.saveAs(os.path.join(out, "carousel.FCStd"))
    solid = [s for k, s in parts.items() if k != "fridge_envelope" and not k.startswith("window_")]
    Part.makeCompound(solid).exportStep(os.path.join(out, "carousel.step"))
    with open(os.path.join(out, "carousel_cutlist.txt"), "w", encoding="utf-8") as fh:
        fh.write(cutlist(p, L) + "\n")
    App.Console.PrintMessage(cutlist(p, L) + "\n")


main()
