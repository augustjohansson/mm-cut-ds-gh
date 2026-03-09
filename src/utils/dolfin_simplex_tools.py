from pathlib import Path


def dolfin_write_medit(filename, mm, t=0):
    """
    Write a DOLFIN MultiMesh to Medit .mesh and .bb files.

    Parameters
    ----------
    filename : str
        Base output filename, without extension.
    mm : dolfin.MultiMesh
        The multimesh object.
    t : int, optional
        Output index, so files become filename.<t>.mesh and filename.<t>.bb
    """
    if mm.num_parts() <= 0:
        raise ValueError("MultiMesh must contain at least one part")

    tdim = mm.part(0).topology().dim()
    gdim = mm.part(0).geometry().dim()
    nne = tdim + 1

    mesh_path = Path(f"{filename}.{t}.mesh")
    bb_path = Path(f"{filename}.{t}.bb")

    n_vertices = sum(mm.part(i).num_vertices() for i in range(mm.num_parts()))
    n_cells = sum(mm.part(i).num_cells() for i in range(mm.num_parts()))

    # Write .mesh file
    with mesh_path.open("w") as f:
        f.write("MeshVersionFormatted 1\n")
        f.write(f"Dimension\n{gdim}\n")
        f.write(f"Vertices\n{n_vertices}\n")

        # Vertices
        for i in range(mm.num_parts()):
            coords = mm.part(i).coordinates()
            for row in coords:
                f.write(" ".join(f"{row[d]:.13g}" for d in range(gdim)))
                f.write(f" {i + 1}\n")

        # Connectivity
        if tdim == 2:
            f.write("Triangles\n")
        elif tdim == 3:
            f.write("Tetrahedra\n")
        else:
            raise ValueError(f"Unsupported topological dimension: {tdim}")

        f.write(f"{n_cells}\n")

        offset = 0
        for i in range(mm.num_parts()):
            cells = mm.part(i).cells()
            for cell in cells:
                f.write(" ".join(str(int(v) + offset + 1) for v in cell[:nne]))
                f.write(f" {i + 1}\n")
            offset += mm.part(i).num_vertices()

    # Write .bb file
    with bb_path.open("w") as f:
        f.write(f"3 1 {n_cells} 1\n")
        for i in range(mm.num_parts()):
            for _ in range(mm.part(i).num_cells()):
                f.write(f"{i + 1}\n")
