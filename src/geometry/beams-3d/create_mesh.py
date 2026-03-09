'''
Mesh each part
gmsh 4.5.6 python api obtained using apt
meshio using pip 4.0.15

Update 2021222
Run outside container with python3-meshio 4.3.5, gmsh 4.6 (all from apt)
'''

import meshio
import gmsh
import os
import numpy
os.makedirs("./meshes", exist_ok=True)

def filename(lcar=0, i=0, name='', filetype="brep", tag=""):
    if lcar == 0:
        # input
        s = name + tag + "." + filetype
        print("read", s)
    else:
        # output
        #s = "meshes/beam_" + str(lcar) + "_" + str(i) + "_" + tag + "." + filetype
        s = "meshes/" + name + "_" + str(lcar) + tag + "." + filetype
        print("write", s)
    return s

element = "tetra"
#co_element = "triangle"

num_lcar = 7
nn = numpy.linspace(2,num_lcar,num_lcar-2+1)
lcars = 2**-nn
#num_beams = 12
#basename = "beam"
names = ["beam0", "beam1", "beam-singlemesh"]
tag = "_3d_0"


for lcar in lcars:
    print("lcar", lcar)
    #for i in range(num_beams):
    for i,name in enumerate(names):
        #name = basename + str(i)
        #name = "beam-singlemesh"
        print("name", name)

        gmsh.initialize()
        gmsh.merge(filename(0, i, name, "brep", tag))
        gmsh.model.mesh.setSize(gmsh.model.getEntities(0), lcar)
        gmsh.model.mesh.generate(3)
        gmsh.write(filename(lcar, i, name, "msh", tag))
        gmsh.write(filename(lcar, i, name, "mesh", tag))
        gmsh.finalize()

        # Read mesh (meshio doesn't read cell data properly?)
        mesh = meshio.read(filename(lcar, i, name, "mesh", tag))

        print(name, filename(lcar, i, name, "mesh", tag), len(mesh.points))
        #import ipdb; ipdb.set_trace()

        # Write for fenics
        meshio.write(filename(lcar, i, name, "xdmf", tag),
                     meshio.Mesh(points=mesh.points,
                                 cells={element: mesh.get_cells_type(element)}))
        # meshio.write(filename(lcar, i, name, "xdmf", tag + "_mvc"),
        #              meshio.Mesh(points=mesh.points,
        #                          cells={co_element: mesh.get_cells_type(co_element)},
        #                          cell_data={"name_to_read": [mesh.cell_data_dict["medit:ref"][co_element]]}))
        # if i==0:
        #     meshio.write(filename(lcar, i, name, "xml", tag),
        #                  meshio.Mesh(points=mesh.points,
        #                              cells={element: mesh.get_cells_type(element)}))
