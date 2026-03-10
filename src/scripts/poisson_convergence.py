#!/usr/bin/env python3

import argparse
import os
import warnings

import numpy
from dolfin import *
from ffc.quadrature.deprecation import QuadratureRepresentationDeprecationWarning

warnings.simplefilter("ignore", QuadratureRepresentationDeprecationWarning)

DEFAULT_BEAMS3D_CLSCALES = [
    "0.25",
    "0.125",
    "0.0625",
    "0.03125",
    "0.015625",
    "0.0078125",
]
BEAMS3D_EXACT_VOLUME = 0.29260180166187305
BEAMS3D_EXACT_AREA = 8.021945185788207


parser = argparse.ArgumentParser(
    description="Solve the manufactured Poisson problem on several geometries."
)
parser.add_argument(
    "--geometry",
    choices=["unitsquare", "unitcube", "beams3d"],
    default="unitsquare",
    help="geometry family to use",
)
parser.add_argument(
    "--num_parts",
    type=int,
    help="number of meshes for random unit-domain multimeshes (NB: in the paper, N = num_parts-1)",
    default=2,
)
parser.add_argument("--degree", type=int, help="polynomial degree of basis", default=1)
parser.add_argument(
    "--start",
    type=int,
    help="start refinement index; for unit domains this means Nx=2^start, for beams3d this is the clscale index",
    default=2,
)
parser.add_argument(
    "--stop",
    type=int,
    help="stop refinement index; for unit domains this means Nx=2^stop, for beams3d this is the clscale index",
    default=6,
)
parser.add_argument(
    "--plot",
    type=int,
    help="plot multimesh at this refinement index and exit (mainly useful in 2D)",
    default=-1,
)
parser.add_argument(
    "--compress_volume", help="compress volume quadrature", action="store_true"
)
parser.add_argument(
    "--compress_interface", help="compress interface quadrature", action="store_true"
)
parser.add_argument("--tag", type=str, help="extra string tag to file name", default="")
parser.add_argument("--slim", help="create active mesh", action="store_true")
parser.add_argument("--mumps", help="solve using mumps", action="store_true")
parser.add_argument(
    "--strong_bc",
    action="store_true",
    help="use strong Dirichlet boundary conditions; default is weak Nitsche BCs",
)
parser.add_argument(
    "--mesh-dir",
    type=str,
    default="./geometry/beams-3d/meshes",
    help="directory containing the beams-3d XDMF meshes",
)
parser.add_argument(
    "--quadrature-order",
    type=int,
    default=-1,
    help="override the default multimesh quadrature order 2*degree",
)
parser.add_argument(
    "--write-solutions",
    action="store_true",
    help="write single-mesh and multimesh solutions to XDMF files",
)
parser.add_argument(
    "--output-dir",
    type=str,
    default="output",
    help="directory for solution output",
)
args = parser.parse_args()


def geometry_dim():
    if args.geometry == "unitsquare":
        return 2
    return 3


def exact_polynomial_degree():
    return args.degree + 2


def quadrature_order():
    if args.quadrature_order > 0:
        return args.quadrature_order
    return 2 * args.degree


class Boundary(SubDomain):
    def inside(self, x, on_boundary):
        return on_boundary


def exactsolution():
    if geometry_dim() == 3:
        return Expression(
            "sin(pi*x[0])*sin(pi*x[1])*sin(pi*x[2])",
            degree=exact_polynomial_degree() + 1,
        )
    return Expression("sin(pi*x[0])*sin(pi*x[1])", degree=exact_polynomial_degree() + 1)


def rhs():
    if geometry_dim() == 3:
        return Expression(
            "3*pi*pi*sin(pi*x[0])*sin(pi*x[1])*sin(pi*x[2])",
            degree=exact_polynomial_degree(),
        )
    return Expression(
        "2*pi*pi*sin(pi*x[0])*sin(pi*x[1])", degree=exact_polynomial_degree()
    )


def geometry_levels():
    if args.geometry == "beams3d":
        if args.start < 0 or args.stop >= len(DEFAULT_BEAMS3D_CLSCALES):
            raise ValueError(
                "For beams3d, --start/--stop must be between 0 and {}".format(
                    len(DEFAULT_BEAMS3D_CLSCALES) - 1
                )
            )
        return DEFAULT_BEAMS3D_CLSCALES[args.start : args.stop + 1]

    powers = range(args.start, args.stop + 1)
    return list(numpy.power(2, powers))


def level_tag(level):
    return str(level)


def load_xdmf_mesh(filename):
    if not os.path.isfile(filename):
        raise FileNotFoundError("Mesh file not found: {}".format(filename))
    mesh = Mesh()
    XDMFFile(filename).read(mesh)
    return mesh


def beams3d_part_filename(clscale):
    return os.path.join(args.mesh_dir, "beam0_{}_3d_0.xdmf".format(clscale))


def beams3d_singlemesh_filename(clscale):
    return os.path.join(args.mesh_dir, "beam-singlemesh_{}_3d_0.xdmf".format(clscale))


def activate_uncut_cut_slim(multimesh):
    print("activate_uncut_cut_slim")

    multimesh_new = MultiMesh()
    multimesh_new.parameters["compress_volume_quadrature"] = args.compress_volume
    multimesh_new.parameters["compress_interface_quadrature"] = args.compress_interface

    for p in range(multimesh.num_parts()):
        print(
            "create new part (old part had numcells)", p, multimesh.part(p).num_cells()
        )
        mesh = multimesh.part(p)
        active_cells = MeshFunction("size_t", mesh, mesh.topology().dim())
        active_cells.set_all(0)
        for c in multimesh.uncut_cells(p):
            cell = Cell(mesh, c)
            active_cells[cell] = 1
        for c in multimesh.cut_cells(p):
            points, weights = multimesh.quadrature_rules_cut_cells(p, c)
            if sum(weights) > 100 * DOLFIN_EPS:
                cell = Cell(mesh, c)
                active_cells[cell] = 1
            else:
                print("  small qr volume", p, c, sum(weights))
        active_mesh = SubMesh(mesh, active_cells, 1)
        print("  part, active cells", p, active_mesh.num_cells())
        if active_mesh.num_cells() > 0:
            multimesh_new.add(active_mesh)

    multimesh_new.build(quadrature_order())
    return multimesh_new


def build_unitsquare_multimesh(Nx):
    multimesh = MultiMesh()
    multimesh.parameters["compress_volume_quadrature"] = args.compress_volume
    multimesh.parameters["compress_interface_quadrature"] = args.compress_interface

    mesh = UnitSquareMesh(Nx, Nx)
    multimesh.add(mesh)
    exact_volume = 1.0
    exact_area = 4.0

    numpy.random.seed(multimesh.num_parts())
    while multimesh.num_parts() < args.num_parts:
        x0, x1 = numpy.sort(numpy.random.rand(2))
        y0, y1 = numpy.sort(numpy.random.rand(2))
        if abs(x1 - x0) < DOLFIN_EPS:
            x1 += DOLFIN_EPS
        if abs(y1 - y0) < DOLFIN_EPS:
            y1 += DOLFIN_EPS
        Nx_part = int(max(abs(x1 - x0) * Nx, 1))
        Ny_part = int(max(abs(y1 - y0) * Nx, 1))

        mesh = RectangleMesh(Point(x0, y0), Point(x1, y1), Nx_part, Ny_part)
        phi = numpy.random.rand() * 180
        mesh.rotate(phi)

        coords = mesh.coordinates()
        is_interior = not numpy.any(coords < 0) and not numpy.any(coords > 1.0)
        if is_interior:
            print(
                "// Add new rectangle mesh ({:.3f}, {:.3f}) x ({:.3f}, {:.3f}). Rotation {:.1f} degrees.".format(
                    x0, y0, x1, y1, phi
                )
            )
            multimesh.add(mesh)
        else:
            print("not inside")

    multimesh.build(quadrature_order())
    return multimesh, exact_volume, exact_area


def build_unitcube_multimesh(Nx):
    multimesh = MultiMesh()
    multimesh.parameters["compress_volume_quadrature"] = args.compress_volume
    multimesh.parameters["compress_interface_quadrature"] = args.compress_interface

    mesh = UnitCubeMesh(Nx, Nx, Nx)
    multimesh.add(mesh)
    exact_volume = 1.0
    exact_area = 6.0

    numpy.random.seed(multimesh.num_parts())
    while multimesh.num_parts() < args.num_parts:
        x0, x1 = numpy.sort(numpy.random.rand(2))
        y0, y1 = numpy.sort(numpy.random.rand(2))
        z0, z1 = numpy.sort(numpy.random.rand(2))
        if abs(x1 - x0) < DOLFIN_EPS:
            x1 += DOLFIN_EPS
        if abs(y1 - y0) < DOLFIN_EPS:
            y1 += DOLFIN_EPS
        if abs(z1 - z0) < DOLFIN_EPS:
            z1 += DOLFIN_EPS
        Nx_part = int(max(abs(x1 - x0) * Nx, 1))
        Ny_part = int(max(abs(y1 - y0) * Nx, 1))
        Nz_part = int(max(abs(z1 - z0) * Nx, 1))

        mesh = BoxMesh(Point(x0, y0, z0), Point(x1, y1, z1), Nx_part, Ny_part, Nz_part)
        phi = numpy.random.rand() * 180
        mesh.rotate(phi)

        coords = mesh.coordinates()
        is_interior = not numpy.any(coords < 0) and not numpy.any(coords > 1.0)
        if is_interior:
            print(
                "// Add new box mesh ({:.3f}, {:.3f}, {:.3f}) x ({:.3f}, {:.3f}, {:.3f}). Rotation {:.1f} degrees.".format(
                    x0, y0, z0, x1, y1, z1, phi
                )
            )
            multimesh.add(mesh)
        else:
            print("not inside")

    multimesh.build(quadrature_order())
    return multimesh, exact_volume, exact_area


def build_beams3d_multimesh(clscale):
    print("build_beams3d_multimesh", clscale)
    multimesh = MultiMesh()
    multimesh.parameters["compress_volume_quadrature"] = args.compress_volume
    multimesh.parameters["compress_interface_quadrature"] = args.compress_interface

    filename = beams3d_part_filename(clscale)
    length = 1.0
    width = 0.2
    center = Point(0.5, 0.5, 0.5) * length

    meshes = [load_xdmf_mesh(filename) for _ in range(12)]

    for i in range(1, 4):
        meshes[i].rotate(i * 90, 2, center)

    top_translation = Point(0.0, 0.0, 1.0 - width)
    for i in range(4, 8):
        meshes[i].rotate((i - 4) * 90, 2, center)
        meshes[i].translate(top_translation)

    for i in range(8, 12):
        meshes[i].rotate(90, 1, center)
    x_translation = Point(-1.0 + width, 0.0, 0.0)
    y_translation = Point(0.0, 1.0 - width, 0.0)
    meshes[9].translate(x_translation)
    meshes[10].translate(y_translation)
    meshes[11].translate(x_translation + y_translation)

    for i, mesh in enumerate(meshes):
        print("add multimesh part", i, mesh.num_cells())
        multimesh.add(mesh)

    multimesh.build(quadrature_order())
    return multimesh, BEAMS3D_EXACT_VOLUME, BEAMS3D_EXACT_AREA


def build_single_mesh(level):
    if args.geometry == "unitsquare":
        return UnitSquareMesh(level, level), 1.0, 4.0
    if args.geometry == "unitcube":
        return UnitCubeMesh(level, level, level), 1.0, 6.0
    if args.geometry == "beams3d":
        mesh = load_xdmf_mesh(beams3d_singlemesh_filename(level))
        return mesh, BEAMS3D_EXACT_VOLUME, BEAMS3D_EXACT_AREA
    raise ValueError("Unknown geometry {}".format(args.geometry))


def build_multimesh(level):
    if args.geometry == "unitsquare":
        multimesh, exact_volume, exact_area = build_unitsquare_multimesh(level)
    elif args.geometry == "unitcube":
        multimesh, exact_volume, exact_area = build_unitcube_multimesh(level)
    elif args.geometry == "beams3d":
        multimesh, exact_volume, exact_area = build_beams3d_multimesh(level)
    else:
        raise ValueError("Unknown geometry {}".format(args.geometry))

    num_hidden = 0
    for i in range(multimesh.num_parts()):
        if len(multimesh.cut_cells(i)) == 0 and len(multimesh.uncut_cells(i)) == 0:
            num_hidden += 1
            print("hidden part", i)
    if num_hidden == 0:
        print("no hidden parts")
    else:
        print("total number of hidden parts", num_hidden)

    if args.slim:
        multimesh = activate_uncut_cut_slim(multimesh)

    return multimesh, exact_volume, exact_area


def setup_solver():
    solver = KrylovSolver("cg", "amg")
    solver.parameters["relative_tolerance"] = 1e-10
    solver.parameters["maximum_iterations"] = 10000
    solver.parameters["monitor_convergence"] = False
    return solver


def solve_linear_system(A, x, b):
    if args.mumps:
        solve(A, x, b, "mumps")
    else:
        solver = setup_solver()
        solver.solve(A, x, b)


def mesh_hmax(mesh_like):
    if isinstance(mesh_like, cpp.mesh.MultiMesh):
        return max(mesh_like.part(i).hmax() for i in range(mesh_like.num_parts()))
    return mesh_like.hmax()


def measure_error(value, exact_value, tag):
    error = abs(value - exact_value)
    print(tag, "error", error)
    if error > 1e-10:
        print("   WARNING: large", tag, "error")


def check_geometry(mesh_like, exact_volume, exact_area):
    if isinstance(mesh_like, cpp.mesh.MultiMesh):
        volume = mesh_like.compute_volume()
        area = mesh_like.compute_area()
    else:
        volume = assemble(1.0 * dx(domain=mesh_like))
        area = assemble(1.0 * ds(domain=mesh_like))

    measure_error(volume, exact_volume, "volume")
    measure_error(area, exact_area, "area")


def maybe_write_single_solution(uh, level):
    if not args.write_solutions:
        return
    os.makedirs(args.output_dir, exist_ok=True)
    filename = os.path.join(
        args.output_dir,
        "u_single_{}_{}.xdmf".format(args.geometry, level_tag(level)),
    )
    XDMFFile(filename).write(uh)


def maybe_write_multimesh_solution(uh, multimesh, level):
    if not args.write_solutions:
        return
    os.makedirs(args.output_dir, exist_ok=True)
    for p in range(multimesh.num_parts()):
        filename = os.path.join(
            args.output_dir,
            "u_multimesh_{}_{}_part{}.xdmf".format(args.geometry, level_tag(level), p),
        )
        XDMFFile(filename).write(uh.part(p))


def solve_single_poisson(level):
    print("single mesh solver")
    timer = Timer()

    mesh, exact_volume, exact_area = build_single_mesh(level)
    check_geometry(mesh, exact_volume, exact_area)

    V = FunctionSpace(mesh, "Lagrange", args.degree)
    u = TrialFunction(V)
    v = TestFunction(V)
    f = rhs()
    a = inner(grad(u), grad(v)) * dx
    L = f * v * dx

    if not args.strong_bc:
        beta_N = 10.0 * args.degree * args.degree
        n = FacetNormal(mesh)
        h = 2.0 * Circumradius(mesh)
        a += (
            -dot(dot(n, grad(u)), v) * ds
            - dot(u, dot(n, grad(v))) * ds
            + beta_N / h * dot(u, v) * ds
        )
        L += (
            -dot(exactsolution(), dot(n, grad(v))) * ds
            + beta_N / h * dot(exactsolution(), v) * ds
        )

    timer.start()
    A = assemble(a)
    b = assemble(L)
    print("single mesh assembly took", timer.elapsed()[0])

    if args.strong_bc:
        bc = DirichletBC(V, exactsolution(), Boundary())
        bc.apply(A, b)

    uh = Function(V)
    timer.start()
    solve_linear_system(A, uh.vector(), b)
    print("single mesh solve took", timer.elapsed()[0])

    L2error = errornorm(exactsolution(), uh, "L2", degree_rise=2)
    H10error = errornorm(exactsolution(), uh, "H10", degree_rise=2)
    h = mesh_hmax(mesh)

    maybe_write_single_solution(uh, level)
    print(level_tag(level), h, L2error, H10error)
    return h, L2error, H10error


def solve_multimesh_poisson(level, do_plot):
    print("multimesh solver with geometry", args.geometry)
    timer = Timer()

    timer.start()
    multimesh, exact_volume, exact_area = build_multimesh(level)
    print("multimesh construction took", timer.elapsed()[0])
    if do_plot:
        if geometry_dim() != 2:
            raise RuntimeError("--plot is only supported here for 2D geometries")
        print(multimesh.plot_matplotlib(0.0, "mm.pdf"))
        raise SystemExit(0)

    check_geometry(multimesh, exact_volume, exact_area)

    V = MultiMeshFunctionSpace(multimesh, "Lagrange", args.degree)
    u = TrialFunction(V)
    v = TestFunction(V)
    f = rhs()

    n = FacetNormal(multimesh)
    h = 2.0 * Circumradius(multimesh)

    beta_N = 10.0 * args.degree * args.degree
    beta_s = 10.0

    a = (
        dot(grad(u), grad(v)) * dX
        - dot(avg(grad(u)), jump(v, n)) * dI
        - dot(avg(grad(v)), jump(u, n)) * dI
        + beta_N / avg(h) * jump(u) * jump(v) * dI
    )
    a += beta_s * dot(jump(grad(u)), jump(grad(v))) * dO
    L = f * v * dX

    if not args.strong_bc:
        a += (
            -dot(u, dot(n, grad(v))) * dsC
            - dot(dot(n, grad(u)), v) * dsC
            + beta_N / h * dot(u, v) * dsC
        )
        L += (
            -dot(exactsolution(), dot(n, grad(v))) * dsC
            + beta_N / h * dot(exactsolution(), v) * dsC
        )

    parameters["linear_algebra_backend"] = "PETSc"
    timer.start()
    print("assemble a")
    A = assemble_multimesh(a)
    print("assemble L")
    b = assemble_multimesh(L)
    print("multimesh assembly took", timer.elapsed()[0])

    if args.strong_bc:
        bc = MultiMeshDirichletBC(V, exactsolution(), Boundary())
        bc.apply(A, b)

    V.lock_inactive_dofs(A, b)

    uh = MultiMeshFunction(V)
    timer.start()
    solve_linear_system(A, uh.vector(), b)
    print("multimesh solve took", timer.elapsed()[0])

    L2error = errornorm(exactsolution(), uh, "L2", degree_rise=1)
    H10error = errornorm(exactsolution(), uh, "H10", degree_rise=1)
    hmax = mesh_hmax(multimesh)

    maybe_write_multimesh_solution(uh, multimesh, level)
    print(level_tag(level), hmax, L2error, H10error)
    return hmax, L2error, H10error


def rates(err, h):
    err = numpy.asarray(err, dtype=float)
    h = numpy.asarray(h, dtype=float)
    if len(err) <= 1:
        return numpy.array([numpy.nan] * len(err))
    r = numpy.log(err[1:] / err[:-1]) / numpy.log(h[1:] / h[:-1])
    return numpy.append(r, numpy.nan)


def default_table_filename():
    filename = "table_{}".format(args.geometry)
    for arg in sorted(vars(args)):
        if arg in ("output_dir", "write_solutions", "mesh_dir"):
            continue
        filename += "_{}_{}".format(arg, getattr(args, arg))
    if args.tag:
        filename += "_{}".format(args.tag)
    return filename + ".txt"


def save_table():
    levels = geometry_levels()
    print("levels =", levels)

    hm = numpy.zeros(len(levels))
    hs = numpy.zeros(len(levels))
    L2errorm = numpy.zeros(len(levels))
    H10errorm = numpy.zeros(len(levels))
    L2errors = numpy.zeros(len(levels))
    H10errors = numpy.zeros(len(levels))

    for i, level in enumerate(levels):
        print("")
        print("index", i, "level", level_tag(level))
        print("polynomial degree", args.degree)
        print("quadrature order", quadrature_order())
        hs[i], L2errors[i], H10errors[i] = solve_single_poisson(level)
        hm[i], L2errorm[i], H10errorm[i] = solve_multimesh_poisson(
            level, i == args.plot
        )

    L2rates = rates(L2errors, hs)
    L2ratem = rates(L2errorm, hm)
    H10rates = rates(H10errors, hs)
    H10ratem = rates(H10errorm, hm)

    filename = default_table_filename()
    with open(filename, "w") as f:
        header = "Single mesh\t\t\t\t\t\t MultiMesh " + str(args)
        print(header)
        f.write(header + "\n")
        for i, level in enumerate(levels):
            line = (
                "%s  %.5e  %.12e  %.12e  %.3f  %.3f"
                "    %.5e  %.12e  %.12e  %.3f  %.3f"
            ) % (
                level_tag(level),
                hs[i],
                L2errors[i],
                H10errors[i],
                L2rates[i],
                H10rates[i],
                hm[i],
                L2errorm[i],
                H10errorm[i],
                L2ratem[i],
                H10ratem[i],
            )
            print(line)
            f.write(line + "\n")

    print("wrote", filename)


if __name__ == "__main__":
    for arg in sorted(vars(args)):
        print(arg, getattr(args, arg))
    save_table()
