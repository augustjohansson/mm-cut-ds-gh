august@mly mm-cut-ds-gh (main)$ cat plotter.py
from dolfin import *
from utils.dolfin_simplex_tools import *
import numpy


def multimesh():
    mesh_0 = RectangleMesh(Point(0, 0), Point(1, 1), 20, 20)
    mesh_1 = RectangleMesh(
        Point(numpy.pi / 10, numpy.pi / 9), Point(numpy.pi / 8, numpy.pi / 7), 5
, 8
    )
    multimesh = MultiMesh()
    multimesh.add(mesh_0)
    multimesh.add(mesh_1)
    multimesh.build()
    return multimesh


mm = multimesh()

dolfin_write_medit("test1", mm)
august@mly mm-cut-ds-gh (main)$ 






















