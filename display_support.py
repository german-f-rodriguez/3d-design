# -*- coding: utf-8 -*-
"""Soporte para display de 7" montado sobre la cara bottom de una PCB.

Genera base, marco y separadores, y los guarda como .FCStd y .stl.

Uso:
    freecadcmd display_support.py

Sistema de coordenadas: la PCB vista desde su cara bottom (la azul).
    Origen  esquina inferior izquierda de la PCB
    +X      hacia la derecha (la muesca de la PCB queda en X = 0)
    +Y      hacia arriba
    +Z      hacia quien mira el display (la cara bottom de la PCB está en Z = 0)

Medidas en mm.
"""
import json
import os

import FreeCAD as App
import Mesh
import MeshPart
import Part
from FreeCAD import Vector as V

# ---------------------------------------------------------------- PCB (plano)
PCB_X = 124.0
PCB_Y = 165.05
PCB_T = 1.6                 # SUPUESTO: espesor habitual, solo para el conjunto
HOLE_SPACING_X = 113.0
HOLE_SPACING_Y = 147.5
HOLE_Y0 = 9.5
HOLE_X0 = (PCB_X - HOLE_SPACING_X) / 2.0   # 5.5, medido sobre la imagen
NOTCH_Y0 = 71.78
NOTCH_Y1 = 98.28
NOTCH_DEPTH = 2.0           # medido sobre la imagen

# Diámetros medidos sobre la imagen (sin cota en el plano)
PCB_HOLE_LARGE = 5.5
PCB_HOLE_SMALL = 4.2
PAD_DIAMETER = 10.0         # anillo sin cobre expuesto alrededor de cada agujero

# Agujero chico: arriba a la izquierda en la cara top, arriba a la derecha aquí
PCB_HOLES = [
    (HOLE_X0, HOLE_Y0, PCB_HOLE_LARGE),
    (HOLE_X0 + HOLE_SPACING_X, HOLE_Y0, PCB_HOLE_LARGE),
    (HOLE_X0, HOLE_Y0 + HOLE_SPACING_Y, PCB_HOLE_LARGE),
    (HOLE_X0 + HOLE_SPACING_X, HOLE_Y0 + HOLE_SPACING_Y, PCB_HOLE_SMALL),
]

# ------------------------------------------------------------ Display (plano)
DISPLAY_X = 100.0
DISPLAY_Y = 165.0
DISPLAY_T = 5.0
BEZEL_LEFT = 9.0            # lado del flex
BEZEL_RIGHT = 5.0
BEZEL_TOP = 4.0
BEZEL_BOTTOM = 5.0
FLEX_WIDTH = 30.0           # estimado de la foto del montaje actual

# ------------------------------------------------------------ Diseño (ajustable)
LAMINA_H = 5.0              # láminas EMC de la PCB, sin comprimir (aprox.)
LAMINA_COMPRESSION = 0.5    # SUPUESTO: compresión de las láminas contra el display
LEDGE_T = 1.5               # reborde de apoyo del display
LEDGE_W = 3.0               # SUPUESTO: ancho del reborde; la ventana lo deja pasante
DISPLAY_X0 = 9.5            # corrido hacia el flex para librar el componente
WALL_Y = 2.2                # pared del alojamiento en los lados superior e inferior
FRAME_T = 3.0
DISPLAY_CLEARANCE = 0.3     # holgura del display por lado
WINDOW_MARGIN = 0.5         # la ventana excede el área activa por lado
HOLE_D = 4.0                # agujero de base, marco y separadores (tornillo M3)
CSK_D = 6.4                 # avellanado del marco para cabeza plana M3 a 90 grados
SCREW_L = 20.0               # longitud comercial, con la cabeza incluida
FLEX_SLOT_Y0 = 62.0         # cubre la muesca de la PCB y el flex estimado
FLEX_SLOT_Y1 = 103.0
CORNER_R = 3.0

# Componente alto de la cara bottom (aprox.). La posición en Y se estimó de la
# foto del montaje actual. El recorte de la base deja margen en Y.
COMPONENT_X0 = 110.0
COMPONENT_Y0 = 57.0
COMPONENT_Y = 40.0
COMPONENT_H = 6.0
COMPONENT_CUT_Y0 = 50.0
COMPONENT_CUT_Y1 = 105.0

# ------------------------------------------------------------------ Derivados
CONTACT_GAP = LAMINA_H - LAMINA_COMPRESSION   # dorso del display sobre la PCB
SPACER_H = CONTACT_GAP - LEDGE_T
DISPLAY_Y0 = (PCB_Y - DISPLAY_Y) / 2.0
POCKET_X0 = DISPLAY_X0 - DISPLAY_CLEARANCE
POCKET_Y0 = DISPLAY_Y0 - DISPLAY_CLEARANCE
POCKET_X = DISPLAY_X + 2 * DISPLAY_CLEARANCE
POCKET_Y = DISPLAY_Y + 2 * DISPLAY_CLEARANCE
OUTER_Y0 = POCKET_Y0 - WALL_Y
OUTER_Y = POCKET_Y + 2 * WALL_Y
BASE_T = LEDGE_T + DISPLAY_T
ACTIVE_X = DISPLAY_X - BEZEL_LEFT - BEZEL_RIGHT
ACTIVE_Y = DISPLAY_Y - BEZEL_TOP - BEZEL_BOTTOM
ACTIVE_X0 = DISPLAY_X0 + BEZEL_LEFT
ACTIVE_Y0 = DISPLAY_Y0 + BEZEL_BOTTOM

try:
    OUT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    OUT_DIR = os.getcwd()


def box(x0, y0, z0, dx, dy, dz):
    return Part.makeBox(dx, dy, dz, V(x0, y0, z0))


def rounded_plate(z0, thickness):
    plate = box(0, OUTER_Y0, z0, PCB_X, OUTER_Y, thickness)
    vertical = [e for e in plate.Edges
                if abs(e.Vertexes[0].Z - e.Vertexes[1].Z) > 1e-6]
    return plate.makeFillet(CORNER_R, vertical)


def cut_holes(shape, z0, height):
    for x, y, _ in PCB_HOLES:
        hole = Part.makeCylinder(HOLE_D / 2.0, height + 2, V(x, y, z0 - 1))
        shape = shape.cut(hole)
    return shape


def cut_countersinks(shape, top_z):
    depth = (CSK_D - HOLE_D) / 2.0
    for x, y, _ in PCB_HOLES:
        cone = Part.makeCone(HOLE_D / 2.0, CSK_D / 2.0, depth, V(x, y, top_z - depth))
        relief = Part.makeCylinder(CSK_D / 2.0, 1, V(x, y, top_z))
        shape = shape.cut(cone.fuse(relief))
    return shape


def make_base():
    shape = rounded_plate(0, BASE_T)
    shape = shape.cut(box(POCKET_X0, POCKET_Y0, LEDGE_T,
                          POCKET_X, POCKET_Y, DISPLAY_T + 1))
    # Ventana pasante: las láminas de la PCB tocan el dorso del display
    shape = shape.cut(box(POCKET_X0 + LEDGE_W, POCKET_Y0 + LEDGE_W, -1,
                          POCKET_X - 2 * LEDGE_W, POCKET_Y - 2 * LEDGE_W, BASE_T + 2))
    # Salida del flex hacia la muesca de la PCB; el reborde queda continuo
    shape = shape.cut(box(-1, FLEX_SLOT_Y0, -1, POCKET_X0 + 1,
                          FLEX_SLOT_Y1 - FLEX_SLOT_Y0, BASE_T + 2))
    # Recorte pasante para el componente alto; el reborde también queda continuo
    pocket_x1 = POCKET_X0 + POCKET_X
    shape = shape.cut(box(pocket_x1, COMPONENT_CUT_Y0, -1, PCB_X - pocket_x1 + 1,
                          COMPONENT_CUT_Y1 - COMPONENT_CUT_Y0, BASE_T + 2))
    return cut_holes(shape, 0, BASE_T).removeSplitter()


def make_frame():
    shape = rounded_plate(0, FRAME_T)
    shape = shape.cut(box(ACTIVE_X0 - WINDOW_MARGIN, ACTIVE_Y0 - WINDOW_MARGIN, -1,
                          ACTIVE_X + 2 * WINDOW_MARGIN, ACTIVE_Y + 2 * WINDOW_MARGIN,
                          FRAME_T + 2))
    shape = cut_holes(shape, 0, FRAME_T)
    return cut_countersinks(shape, FRAME_T).removeSplitter()


def make_spacer():
    tube = Part.makeCylinder(PAD_DIAMETER / 2.0, SPACER_H)
    return tube.cut(Part.makeCylinder(HOLE_D / 2.0, SPACER_H + 2, V(0, 0, -1)))


def make_pcb_reference():
    pcb = box(0, 0, -PCB_T, PCB_X, PCB_Y, PCB_T)
    pcb = pcb.cut(box(-1, NOTCH_Y0, -PCB_T - 1, NOTCH_DEPTH + 1,
                      NOTCH_Y1 - NOTCH_Y0, PCB_T + 2))
    for x, y, d in PCB_HOLES:
        pcb = pcb.cut(Part.makeCylinder(d / 2.0, PCB_T + 2, V(x, y, -PCB_T - 1)))
    return pcb


def add(doc, name, shape, color=None, transparency=None):
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    view = getattr(obj, "ViewObject", None)
    if view:
        if color:
            view.ShapeColor = color
        if transparency is not None:
            view.Transparency = transparency
    return obj


def export_stl(shape, name):
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.05,
                                  AngularDeflection=0.2, Relative=False)
    mesh.write(os.path.join(OUT_DIR, name))
    return mesh


def assert_clear(a, b, label):
    volume = a.common(b).Volume
    print("  %-34s interferencia = %.4f mm3" % (label, volume))
    if volume > 1e-6:
        raise RuntimeError("Interferencia: " + label)


def main():
    base = make_base()
    frame = make_frame()
    spacer_shape = make_spacer()

    z_base = SPACER_H
    z_display = z_base + LEDGE_T
    z_frame = z_base + BASE_T

    base_placed = base.copy()
    base_placed.translate(V(0, 0, z_base))
    frame_placed = frame.copy()
    frame_placed.translate(V(0, 0, z_frame))
    spacers = []
    for x, y, _ in PCB_HOLES:
        spacer = spacer_shape.copy()
        spacer.translate(V(x, y, 0))
        spacers.append(spacer)
    spacers_placed = Part.makeCompound(spacers)
    pcb = make_pcb_reference()
    display = box(DISPLAY_X0, DISPLAY_Y0, z_display, DISPLAY_X, DISPLAY_Y, DISPLAY_T)
    flex_y0 = DISPLAY_Y0 + (DISPLAY_Y - FLEX_WIDTH) / 2.0
    flex = box(0, flex_y0, z_display + 2.0, DISPLAY_X0, FLEX_WIDTH, 0.2)
    component = box(COMPONENT_X0, COMPONENT_Y0, 0, PCB_X - COMPONENT_X0,
                    COMPONENT_Y, COMPONENT_H)

    doc = App.newDocument("DisplaySupport")
    add(doc, "Base", base_placed, (0.20, 0.45, 0.75))
    add(doc, "Marco", frame_placed, (0.15, 0.15, 0.15))
    add(doc, "Separadores", spacers_placed, (0.85, 0.65, 0.15))
    add(doc, "Ref_PCB", pcb, (0.05, 0.10, 0.70), 50)
    add(doc, "Ref_Display", display, (0.55, 0.75, 0.85), 40)
    add(doc, "Ref_Flex", flex, (0.85, 0.45, 0.10))
    add(doc, "Ref_Componente", component, (0.75, 0.20, 0.20), 40)
    doc.recompute()
    doc.saveAs(os.path.join(OUT_DIR, "DisplaySupport.FCStd"))

    print("Mallas STL:")
    for filename, shape in (("base.stl", base), ("marco.stl", frame),
                            ("separador_x4.stl", spacer_shape)):
        mesh = export_stl(shape, filename)
        print("  %-24s %6d triángulos, sólida=%s" % (filename, mesh.CountFacets, mesh.isSolid()))

    print("Validación:")
    for label, shape in (("Base", base), ("Marco", frame),
                         ("Separador", spacer_shape)):
        bb = shape.BoundBox
        print("  %-18s válida=%s sólidos=%d vol=%8.0f mm3 caja=%.2f x %.2f x %.2f" % (
            label, shape.isValid(), len(shape.Solids), shape.Volume,
            bb.XLength, bb.YLength, bb.ZLength))
        if not shape.isValid() or len(shape.Solids) != 1:
            raise RuntimeError("Sólido inválido: " + label)

    print("Interferencias:")
    assert_clear(display, base_placed, "display / base")
    assert_clear(display, frame_placed, "display / marco")
    assert_clear(flex, base_placed, "flex / base")
    assert_clear(flex, frame_placed, "flex / marco")
    assert_clear(pcb, base_placed, "PCB / base")
    assert_clear(spacers_placed, base_placed, "separadores / base")
    assert_clear(component, display, "componente / display")
    assert_clear(component, base_placed, "componente / base")
    assert_clear(component, frame_placed, "componente / marco")
    assert_clear(component, spacers_placed, "componente / separadores")

    print("Agujeros (centro X, Y y diámetro en la base y el marco):")
    for name, shape in (("Base", base), ("Marco", frame)):
        found = sorted((round(f.Surface.Center.x, 3), round(f.Surface.Center.y, 3),
                        round(f.Surface.Radius * 2, 3))
                       for f in shape.Faces
                       if isinstance(f.Surface, Part.Cylinder)
                       and f.Surface.Radius < 2.5)
        print("  ", name, found)

    print("Paredes mínimas:")
    for x, y, _ in PCB_HOLES:
        radius = HOLE_D / 2.0
        to_pocket = (POCKET_X0 - x if x < PCB_X / 2 else x - (POCKET_X0 + POCKET_X)) - radius
        print("   agujero (%.1f, %.1f): %.2f mm al alojamiento" % (x, y, to_pocket))
    window_x0 = ACTIVE_X0 - WINDOW_MARGIN
    window_x1 = ACTIVE_X0 + ACTIVE_X + WINDOW_MARGIN
    window_y0 = ACTIVE_Y0 - WINDOW_MARGIN
    window_y1 = ACTIVE_Y0 + ACTIVE_Y + WINDOW_MARGIN
    print("   ventana X %.3f..%.3f, Y %.3f..%.3f; apoyo sobre el bisel: izq %.1f der %.1f sup %.1f inf %.1f" % (
        window_x0, window_x1, window_y0, window_y1,
        BEZEL_LEFT - WINDOW_MARGIN, BEZEL_RIGHT - WINDOW_MARGIN,
        BEZEL_TOP - WINDOW_MARGIN, BEZEL_BOTTOM - WINDOW_MARGIN))
    print("   altura total sobre la PCB: %.1f mm" % (SPACER_H + BASE_T + FRAME_T))
    stack = SPACER_H + BASE_T + FRAME_T + PCB_T
    print("   apilado %.1f mm: tornillo de %.1f mm deja %.1f mm de rosca" % (
        stack, SCREW_L, SCREW_L - stack))
    print("   dorso del display a %.1f mm de la PCB, separadores de %.1f mm" % (
        CONTACT_GAP, SPACER_H))
    print("   display X %.1f..%.1f, ventana de la base X %.1f..%.1f, Y %.3f..%.3f" % (
        DISPLAY_X0, DISPLAY_X0 + DISPLAY_X, POCKET_X0 + LEDGE_W,
        POCKET_X0 + POCKET_X - LEDGE_W, POCKET_Y0 + LEDGE_W,
        POCKET_Y0 + POCKET_Y - LEDGE_W))

    # Cortes reales de la geometría para revisar las piezas sin abrir la GUI
    preview = os.environ.get("DISPLAY_SUPPORT_PREVIEW")
    if preview:
        data = {}
        for label, shape, z in (("base_reborde", base, LEDGE_T / 2),
                                ("base_paredes", base, LEDGE_T + DISPLAY_T / 2),
                                ("marco", frame, FRAME_T / 2)):
            loops = []
            for wire in shape.slice(V(0, 0, 1), z):
                loops.append([[p.x, p.y] for p in wire.discretize(Deflection=0.05)])
            data[label] = loops
        with open(preview, "w") as handle:
            json.dump(data, handle)


main()
