"""
A couple of simple beams of different size and length:

Beam 0: unit length, 0.1 width. Construct frame of cube.
Beam 1: sqrt(3) length, 0.1 width. Construct diagonal of cube.

exec(open("main.py").read())
"""

import FreeCAD
import numpy as np
import utilities
import importlib

# Import FreeCAD Draft.py:
import sys

sys.path.append("/usr/lib/freecad-python3/lib")  # import FreeCAD
sys.path.append("/usr/share/freecad/Ext")  # import PySide shim
sys.path.append("/usr/share/freecad/Mod/Draft")  # import Draft
sys.path.append("/usr/share/freecad/Mod/Part")  # import

sys.path.append(os.path.join(FreeCAD.getResourceDir(), "Mod", "Draft"))  # for Draft.py
import Draft
import Part

importlib.reload(utilities)

utilities.close()

doc = FreeCAD.newDocument("beams")

ex = FreeCAD.Vector(1, 0, 0)
ey = FreeCAD.Vector(0, 1, 0)
ez = FreeCAD.Vector(0, 0, 1)

L0 = 1.0
L1 = np.sqrt(3) * L0
w0 = 0.2
w1 = 0.5 * w0
placement = FreeCAD.Vector(0, 0, 0)

B0 = [L0, w0, w0]
beam0 = utilities.box(doc, B0, placement, "beam0")

B1 = [L1, w1, w1]
beam1 = utilities.box(doc, B1, placement, "beam1")

# Cut out cylinder holes
r0 = 0.25 * w0
h0 = 2 * L0  # 2*w0
pnt = FreeCAD.Vector(L0 / 3, 0.5 * w0, -0.5 * L0)  # -0.25*h0)
cyl = utilities.cylinder(doc, r0, h0, pnt)
cyl2 = Draft.move([cyl], FreeCAD.Vector(L0 / 3, 0, 0), copy=True)
cyl34 = Draft.rotate(
    [cyl, cyl2], 90, FreeCAD.Vector(0, 0.5 * w0, 0.5 * w0), ex, copy=True
)
cyls = [cyl, cyl2]
cyls.extend(cyl34)

beams0_tmp = beam0
for cyl in cyls:
    beams0_tmp = utilities.cut(doc, beams0_tmp, cyl, "beams0_tmp")
beam0_w_hole = beams0_tmp

# beam0_tmp = utilities.cut(doc, beam0, cyl, "beam0_tmp")
# beam0_tmp = utilities.cut(doc, beam0_tmp, cyl2, "beam0_tmp")
# beam0_w_hole = utilities.cut(doc, beam0_tmp, cyl34, "beam0_w_hole")

r1 = 0.25 * w1
h1 = 2 * w1
pnt = FreeCAD.Vector(L1 / 3, 0.5 * w1, -0.25 * h1)
cyl = utilities.cylinder(doc, r1, h1, pnt)
vec = FreeCAD.Vector(L1 / 3, 0, 0)
cyl2 = Draft.move([cyl], vec, copy=True)
beam1_tmp = utilities.cut(doc, beam1, cyl, "beam1_tmp")
beam1_w_hole = utilities.cut(doc, beam1_tmp, cyl2, "beam1_w_hole")
doc.recompute()

# Create 12 standard beams
b0 = beam0_w_hole
b1 = Draft.move(b0, FreeCAD.Vector(0, 0, 1 - w0), copy=True)
b2 = Draft.move(b0, FreeCAD.Vector(0, 1 - w0, 0), copy=True)
b3 = Draft.move(b1, FreeCAD.Vector(0, 1 - w0, 0), copy=True)
bbase = [b0, b1, b2, b3]
brotz = Draft.rotate(bbase, 90, FreeCAD.Vector(0.5, 0.5, 0), ez, copy=True)
broty = Draft.rotate(bbase, 90, FreeCAD.Vector(0.5, 0, 0.5), ey, copy=True)
ball = []
ball.extend(bbase)
ball.extend(brotz)
ball.extend(broty)

# Export
do_save = True
if do_save:
    tag = "_3d_0"
    Part.export([beam0_w_hole], "beam0_3d_0.brep")
    Part.export([beam1_w_hole], "beam1_3d_0.brep")
    # Part.export(ball, "beams" + tag + ".brep")
    # for i,b in enumerate(ball):
    #    Part.export([b], "beam" + str(i) + tag + ".brep")

# Single mesh simplest setup
box = utilities.box(doc, [L0, L0, L0], placement, "box")
removez = utilities.box(
    doc,
    [L0 - 2 * w0, L0 - 2 * w0, 2 * L0],
    placement + FreeCAD.Vector(w0, w0, 0),
    "removez",
)
removey = utilities.box(
    doc,
    [L0 - 2 * w0, 2 * L0, L0 - 2 * w0],
    placement + FreeCAD.Vector(w0, 0, w0),
    "removey",
)
removex = utilities.box(
    doc,
    [2 * L0, L0 - 2 * w0, L0 - 2 * w0],
    placement + FreeCAD.Vector(0, w0, w0),
    "removex",
)
boxx = utilities.cut(doc, box, removex, "boxx")
boxy = utilities.cut(doc, boxx, removey, "boxy")
boxz = utilities.cut(doc, boxy, removez, "boxz")

# Create more cyls to cut out
r = r0
h = 2 * L0
p = FreeCAD.Vector(L0 / 3, 0.5 * w0, -0.5 * L0)
cyls = [
    utilities.cylinder(doc, r, h, p),
    utilities.cylinder(doc, r, h, p + FreeCAD.Vector(L0 / 3, 0, 0)),
    utilities.cylinder(doc, r, h, p + FreeCAD.Vector(0, 1 - w0, 0)),
    utilities.cylinder(doc, r, h, p + FreeCAD.Vector(L0 / 3, 1 - w0, 0)),
]
xc = FreeCAD.Vector(0.5, 0.5, 0.5) * L0
cyls.extend(Draft.rotate(cyls, 90, xc, copy=True))
cyls.extend(Draft.rotate(cyls, 90, xc, axis=ey, copy=True))

# Cut out
for cyl in cyls:
    boxz = utilities.cut(doc, boxz, cyl, "boxz")

# More cyls
cyl = Draft.rotate(cyls[0], 90, xc, axis=ex, copy=True)
cyls = [cyl, Draft.move(cyl, FreeCAD.Vector(L0 / 3, 0, 0), copy=True)]
cyls.extend(Draft.move(cyls, FreeCAD.Vector(0, 0, 1 - w0), copy=True))
cyls.extend(Draft.rotate(cyls, 90, xc, axis=ey, copy=True))

# Cut out
for cyl in cyls:
    boxz = utilities.cut(doc, boxz, cyl, "boxz")
doc.recompute()

# Save single mesh
if do_save:
    Part.export([boxz], "beam-singlemesh" + tag + ".brep")

print("volume", boxz.Shape.Volume)
print("area", boxz.Shape.Area)

# Gui.ActiveDocument = Gui.getDocument("beams")
# Gui.SendMsgToActiveView("ViewFit")
# Gui.activeDocument().activeView().viewIsometric()
# Gui.runCommand("Std_OrthographicCamera", 0)
# Gui.runCommand("Std_PerspectiveCamera", 1)

# for obj in doc.Objects:
#     obj.Visibility = False

doc.recompute()
print("done")
