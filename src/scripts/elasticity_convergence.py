import argparse
from dolfin import *
import numpy
import os
from slepc4py import SLEPc
import warnings
from ffc.quadrature.deprecation import QuadratureRepresentationDeprecationWarning

warnings.simplefilter("ignore", QuadratureRepresentationDeprecationWarning)
from ufl import replace

# set_log_level(10)

# from custom_norms import custom_errornorm

# This program solves both the single mesh and multimesh case of a manifactured
# elasticity equation and saves the convergence-rate to the file table1.tex

parser = argparse.ArgumentParser()
parser.add_argument(
    "--num_parts",
    type=int,
    help="number of meshes (NB: in the paper, N=num_parts-1)",
    default=2,
    required=False,
)
parser.add_argument(
    "--degree", type=int, help="polynomial degree of basis", default=2, required=False
)
parser.add_argument(
    "--start", type=int, help="start mesh size range", default=0, required=False
)
parser.add_argument(
    "--stop", type=int, help="stop mesh size range", default=7, required=False
)
# parser.add_argument('--plot', type=int, help='plot at mesh range', default=-1, required=False)
# parser.add_argument('--compress_volume', help='compress volume quadrature', action='store_true')
# parser.add_argument('--compress_interface', help='compress interface quadrature', action='store_true')
parser.add_argument(
    "--tag", type=str, help="extra string tag to file name", default="", required=False
)
# parser.add_argument('--slim', help='create active mesh', action='store_true')
# parser.add_argument('--amg', help='solve using custom_solver', action='store_true')
parser.add_argument("--strong_bc", action="store_true")
parser.add_argument("--beta_N", type=float, default=10.0)
parser.add_argument("--beta_s", type=float, default=10.0)
# parser.add_argument('--avg', type=int, help="average is 1, -1 or something else", default=0)
# parser.add_argument('--slimfactor', type=int, help='tolerance multiple for effectively zero qr', default=1, required=False)
parser.add_argument(
    "--only_geometry",
    action="store_true",
    help="don't solve the pde, only do the geometry stuff",
)
parser.add_argument("--quadrature_order", type=int, default=-1)
parser.add_argument("--dim3", action="store_true")
parser.add_argument("--dont_compute_errors", action="store_true")
parser.add_argument("--eps", type=float, default=-0.1)
parser.add_argument("--volfile", type=str, default="./output/volfile.txt")
args = parser.parse_args()
# Don't include any of these in the table file
args_to_skip = [
    "dim3",
    "only_geometry",
    "quadrature_order",
    "dont_compute_errors",
    "eps",
    "bottom_bc",
    "volfile",
]

E = 200e9
nu = 0.3
mu_fcn = lambda E, nu: E / (2.0 * (1.0 + nu))  # G
mu = mu_fcn(E, nu)
lmbda_fcn = lambda E, nu: E * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
lmbda = lmbda_fcn(E, nu)
print("E", E, "nu", nu)
print("mu", mu, "lmbda", lmbda)


# E = lambda mu, lmbda: mu*(3*lmbda + 2*mu) / (mu + lmbda) # Young
# nu = lambda mu, lmbda: lmbda / (2*(lmbda + mu)) # Poisson ratio
def tensor_jump(v, n):
    return outer(v("+"), n("+")) + outer(v("-"), n("-"))


def epsilon(v):
    return sym(grad(v))  # ~1


def sigma(v):
    return 2.0 * mu * epsilon(v) + lmbda * tr(epsilon(v)) * Identity(
        len(v)
    )  # ~N/m^(d-1) = kg m / s^2 / m^(d-1) = kg / s^2 / m^(2-d)


def exact_polynomial_degree():  # polynomial_degree for "exact" solution
    return args.degree + 2


def quadrature_order():  # (po): # po is polynomial degree
    if args.quadrature_order <= 0:
        return 2 * args.degree
    else:
        return args.quadrature_order


def exactsolution(LX, LY):
    if args.dim3:
        u = ("x[1]+x[0]*x[1]*x[2]", "x[2]+x[0]*x[1]*x[2]", "x[0]+x[0]*x[1]*x[2]")
    else:
        u = (
            "cos((pi*x[1])/LY)*sin((pi*x[0])/LX)",
            "sin((pi*x[0])/LX)*sin((pi*x[1])/LY)",
        )
    return Expression(
        u, mu=mu, lmbda=lmbda, LX=LX, LY=LY, degree=exact_polynomial_degree()
    )


"""
"""


def rhs(LX, LY):
    if args.dim3:
        f = (
            "-(lmbda+mu)*(x[1]+x[2])",
            "-(lmbda+mu)*(x[0]+x[2])",
            "-(lmbda+mu)*(x[0]+x[1])",
        )
    else:
        f = (
            "1.0/(LX*LX)*1.0/(LY*LY)*(pi*pi)*cos((pi*x[1])/LY)*((LY*LY)*lmbda*sin((pi*x[0])/LX)+(LX*LX)*mu*sin((pi*x[0])/LX)+(LY*LY)*mu*sin((pi*x[0])/LX)*2.0-LX*LY*lmbda*cos((pi*x[0])/LX)-LX*LY*mu*cos((pi*x[0])/LX))",
            "1.0/(LX*LX)*1.0/(LY*LY)*(pi*pi)*sin((pi*x[1])/LY)*((LX*LX)*lmbda*sin((pi*x[0])/LX)+(LX*LX)*mu*sin((pi*x[0])/LX)*2.0+(LY*LY)*mu*sin((pi*x[0])/LX)+LX*LY*lmbda*cos((pi*x[0])/LX)+LX*LY*mu*cos((pi*x[0])/LX))",
        )
    return Expression(
        f, mu=mu, lmbda=lmbda, LX=LX, LY=LY, degree=exact_polynomial_degree()
    )


def exact_strain_energy(LX, LY):
    # return 1.3321587821e+16 # propeller single mesh degree 3
    # return 2.3532326186e+13 # propeller single mesh degree 3 strong bc
    # return 5.9345253386e+15  # propeller single mesh 7 degree 2
    # return 2.2368158104e+13 # deg 2 single mesh assemble(sigma(u),epsilon(u))
    # return 1.1184079052e+13 # deg 2 strain energy 0.5*lmbda*trace...
    return 5.9345253386e15  # deg 2 energy directly from form


def exact_vm(LX, LY):
    vm = "sqrt(pow(lmbda*((pi*cos((pi*x[0])/LX)*cos((pi*x[1])/LY))/LX+(pi*cos((pi*x[1])/LY)*sin((pi*x[0])/LX))/LY)*(1.0/3.0)-(pi*mu*cos((pi*x[0])/LX)*cos((pi*x[1])/LY)*(2.0/3.0))/LX+(pi*mu*cos((pi*x[1])/LY)*sin((pi*x[0])/LX)*(4.0/3.0))/LY,2.0)*(3.0/2.0)+pow(lmbda*((pi*cos((pi*x[0])/LX)*cos((pi*x[1])/LY))/LX+(pi*cos((pi*x[1])/LY)*sin((pi*x[0])/LX))/LY)*(1.0/3.0)+(pi*mu*cos((pi*x[0])/LX)*cos((pi*x[1])/LY)*(4.0/3.0))/LX-(pi*mu*cos((pi*x[1])/LY)*sin((pi*x[0])/LX)*(2.0/3.0))/LY,2.0)*(3.0/2.0)+1.0/(LX*LX)*1.0/(LY*LY)*(pi*pi)*(mu*mu)*pow(sin((pi*x[1])/LY),2.0)*pow(LY*cos((pi*x[0])/LX)-LX*sin((pi*x[0])/LX),2.0)*3.0)"
    import ipdb

    ipdb.set_trace()
    return Expression(
        vm, mu=mu, lmbda=lmbda, LX=LX, LY=LY, degree=exact_polynomial_degree()
    )


def exact_sxx(LX, LY):
    if args.dim3:
        sxx = "pi*lmbda*cos(pi*x[2]*0.5)*0.5"
        import ipdb

        ipdb.set_trace()
    else:
        sxx = "lmbda*((pi*cos((pi*x[0])/LX)*cos((pi*x[1])/LY))/LX+(pi*cos((pi*x[1])/LY)*sin((pi*x[0])/LX))/LY)+(pi*mu*cos((pi*x[0])/LX)*cos((pi*x[1])/LY)*2.0)/LX"
    return Expression(
        sxx, mu=mu, lmbda=lmbda, LX=LX, LY=LY, degree=exact_polynomial_degree()
    )


def exact_sxy(LX, LY):
    if args.dim3:
        sxy = "pi*mu*(cos(pi*(x[0]-0.5)*0.5)-cos(pi*(x[1]-0.5)*0.5))*0.5"
        import ipdb

        ipdb.set_trace()
    else:
        sxy = "(pi*mu*sin((pi*x[1])/LY)*(LY*cos((pi*x[0])/LX)-LX*sin((pi*x[0])/LX)))/(LX*LY)"
    return Expression(
        sxy, mu=mu, lmbda=lmbda, LX=LX, LY=LY, degree=exact_polynomial_degree()
    )


def exact_syy(LX, LY):
    if args.dim3:
        syy = "pi*lmbda*cos(pi*x[2]*0.5)*0.5"
        import ipdb

        ipdb.set_trace()
    else:
        syy = "lmbda*((pi*cos((pi*x[0])/LX)*cos((pi*x[1])/LY))/LX+(pi*cos((pi*x[1])/LY)*sin((pi*x[0])/LX))/LY)+(pi*mu*cos((pi*x[1])/LY)*sin((pi*x[0])/LX)*2.0)/LY"
    return Expression(
        syy, mu=mu, lmbda=lmbda, LX=LX, LY=LY, degree=exact_polynomial_degree()
    )


def exact_sxz():
    return Constant(0.0)


def exact_syz():
    return Constant(0.0)


def exact_szz():
    szz = "pi*lmbda*cos(pi*x[2]*0.5)*0.5+pi*mu*cos(pi*x[2]*0.5)"
    import ipdb

    ipdb.set_trace()
    return Expression(szz, mu=mu, lmbda=lmbda, degree=exact_polynomial_degree())


def compute_strain_energy_error(A, uh, form, u, v):
    # Au = A*uh.vector()
    # uAu = Au.inner(uh.vector())

    # uAu = assemble(inner(sigma(uh), epsilon(uh))*dx)

    # U = \lambda/2 (tr(\epsilon))^2 + mu tr(\epsilon^2)

    # eu = epsilon(uh)
    # treu = tr(eu)
    # treu2 = tr(eu*eu)
    # V = uh.function_space()
    # if isinstance(V, MultiMeshFunctionSpace):
    #     uAu = assemble_multimesh((0.5*lmbda*treu**2 + mu*treu2)*dX)
    # else:
    #     uAu = assemble((0.5*lmbda*treu**2 + mu*treu2)*dx)

    form2 = replace(form, {u: uh, v: uh})
    V = uh.function_space()
    if isinstance(V, MultiMeshFunctionSpace):
        uAu = assemble_multimesh(form2)
    else:
        uAu = assemble(form2)

    print(f"approximate squared energy {uAu:1.10e}")
    error = sqrt(abs(uAu - exact_strain_energy(LX, LY)))
    return error


def generic_projection(uh, functional, mtx=None):
    V = uh.function_space()
    deg = args.degree - 1
    if deg == 0:
        element = "DG"
    else:
        element = "Lagrange"
    if isinstance(V, MultiMeshFunctionSpace):
        Q = MultiMeshFunctionSpace(V.multimesh(), element, deg)
    else:
        Q = FunctionSpace(V.mesh(), element, deg)
    Pf = project(functional, Q, solver_type="mumps")
    return Pf


def von_mises(uh):
    sig = sigma(uh)
    s = sig - 1.0 / 3.0 * tr(sig) * Identity(len(uh))  # deviatoric stress
    vm = sqrt(3.0 / 2.0 * inner(s, s))
    # #sxx = 2/3*sig[0,0] - 1/3*sig[1,1]
    # #syy = -1/3*sig[0,0] + 2/3*sig[1,1]
    # #vm = sqrt(3/2*(sxx**2 + syy**2) + 3*(sig[0,1]**2))
    # #vm = sqrt((3*(sig[0,0]/3 - (2*sig[1,1])/3)**2)/2 + (3*((2*sig[0,0])/3 - sig[1,1]/3)**2)/2 + 3*sig[0,1]**2)
    return generic_projection(uh, vm)


def von_mises_squared(uh):
    sig = sigma(uh)
    s = sig - 1.0 / 3.0 * tr(sig) * Identity(len(uh))  # deviatoric stress
    vm = 3.0 / 2.0 * inner(s, s)  # NB squared
    return generic_projection(uh, vm)


def von_mises_error(uh, LX, LY):
    vm = exact_vm(LX, LY)
    vm_h = von_mises(uh)
    print("von mises error")
    vm_error = errornorm(vm, vm_h, "L2", degree_rise=2)

    # e2 = (vm-vm_h)**2
    # if isinstance(uh.function_space(), FunctionSpace):
    #     vm_error = assemble(e2*dx)
    # else:
    #     vm_error = assemble_multimesh(e2*dX)

    # vm = exact_vm(LX, LY)
    # vm_h_2 = von_mises(uh)
    # vm_error = custom_errornorm(vm, vm_h_2, "L2", degree_rise=2)

    return vm_error


def stress_component_error(uh, LX, LY, component):
    return 0.0

    sig = sigma(uh)
    if component == 0:
        sij = exact_sxx(LX, LY)
        sh = sig[0, 0]
    elif component == 1:
        sij = exact_sxy(LX, LY)
        sh = sig[1, 0]
    elif component == 2:
        sij = exact_syy(LX, LY)
        sh = sig[1, 1]
    else:
        import ipdb

        ipdb.set_trace()
    Psh = generic_projection(uh, sh)
    if isinstance(uh.function_space(), MultiMeshFunctionSpace):
        mesh = uh.function_space().multimesh()
    else:
        mesh = uh.function_space().mesh()
    print("Stress component error", component)
    s_error = errornorm(sij, Psh, "L2", degree_rise=2) / norm(sij, "L2", mesh)
    return s_error


def compute_stresses(uh):
    s = sigma(uh)
    V = uh.function_space()
    deg = args.degree - 1
    if deg == 0:
        element = "DG"
    else:
        element = "Lagrange"
    gdim = 2
    if args.dim3:
        gdim = 3
    if isinstance(V, MultiMeshFunctionSpace):
        Q = MultiMeshFunctionSpace(V.multimesh(), element, deg)
        assembler = assemble_multimesh
        measure = dX
        Func = MultiMeshFunction
    else:
        Q = FunctionSpace(V.mesh(), element, deg)
        assembler = assemble
        measure = dx
        Func = Function
    stresses = [[Func(Q)] * gdim for i in range(gdim)]
    return stresses

    v = TestFunction(Q)
    Pv = TrialFunction(Q)
    a = inner(Pv, v) * measure
    A = PETScMatrix()
    assembler(a, tensor=A)
    for i in range(gdim):
        for j in range(i, gdim):
            print("compute_stresses", i, j)
            L = inner(s[i, j], v) * measure
            b = PETScVector()
            assembler(L, tensor=b)
            if isinstance(Q, MultiMeshFunctionSpace):
                Q.lock_inactive_dofs(A, b)
            solve(A, stresses[i][j].vector(), b, "mumps")
    return stresses


def mesh_cpp(i, x0, x1, y0, y1, phi, Nx, Ny):
    s = "points[{:3d}] = {{ Point({:1.16e}, {:1.16e}), Point({:1.16e}, {:1.16e}) }};\n".format(
        i, x0, y0, x1, y1
    )
    s += "angles[{:3d}] = {:1.16e};\n".format(i, phi)
    s += "mesh_sizes[{:3d}] = {{ {:3d}, {:3d} }};\n".format(i, Nx, Ny)
    return s


def append_mesh(meshes, name):
    mesh = Mesh()
    XDMFFile(name).read(mesh)
    meshes.append(mesh)


# def activate_uncut_cut_slim(multimesh):
#     print("activate_uncut_cut_slim")

#     multimesh_new = MultiMesh()
#     #multimesh.parameters["compress_volume_quadrature"] = args.compress_volume
#     #multimesh.parameters["compress_interface_quadrature"] = args.compress_interface

#     for p in range(multimesh.num_parts()):
#         print("create new part (old part had numcells)", p, multimesh.part(p).num_cells())
#         mesh = multimesh.part(p)
#         active_cells = MeshFunction("size_t", mesh, mesh.topology().dim())
#         active_cells.set_all(0)
#         for c in multimesh.uncut_cells(p):
#             cell = Cell(mesh, c)
#             active_cells[cell] = 1
#         for c in multimesh.cut_cells(p):
#             points, weights = multimesh.quadrature_rules_cut_cells(p, c)
#             wsum = sum(weights)
#             #if wsum > args.slimfactor*DOLFIN_EPS:
#             if wsum > 100*DOLFIN_EPS:
#                 cell = Cell(mesh, c)
#                 active_cells[cell] = 1
#             else:
#                 print("  small qr volume", p, c, wsum)
#         active_mesh = SubMesh(mesh, active_cells, 1)
#         print("  part, active cells", p, active_mesh.num_cells())
#         if active_mesh.num_cells() > 0:
#             multimesh_new.add(active_mesh)

#     multimesh_new.build(quadrature_order())

#     return multimesh_new


def build_propeller_mesh(clscale, create_multimesh):

    # Exact vol and area from reference mesh:
    refmesh = Mesh()
    XDMFFile("../../../propeller/meshes/propeller_0.00097656.xdmf").read(refmesh)
    # XDMFFile("../../../propeller/meshes/propeller_0.0078125.xdmf").read(refmesh)
    exact_volume = assemble(1.0 * dx(domain=refmesh))
    exact_area = assemble(1.0 * ds(domain=refmesh))

    if create_multimesh:
        print("build_propeller_mesh clscale =", clscale)
        multimesh = MultiMesh()
        multimesh.label = clscale

        # # Add center first (swap variant)
        # mesh = Mesh()
        # XDMFFile("../../../propeller/meshes/center_" + clscale + ".xdmf").read(mesh)
        # multimesh.add(mesh)

        num_blades = int(args.tag)
        alpha = [i * 360 / num_blades for i in range(num_blades)]
        for i in range(num_blades):
            mesh = Mesh()
            XDMFFile("../../../propeller/meshes/blade_" + clscale + ".xdmf").read(mesh)
            # Hard code rotation center
            mesh.rotate(alpha[i], 2, Point(128, 720))
            multimesh.add(mesh)

        # Add center last as in the model
        mesh = Mesh()
        XDMFFile("../../../propeller/meshes/center_" + clscale + ".xdmf").read(mesh)
        multimesh.add(mesh)

        multimesh.build(quadrature_order())

        # # Reference (same or different resolution)
        # reference_mesh = Mesh()
        # XDMFFile("../../../propeller/meshes/propeller_" + clscale + ".xdmf").read(reference_mesh)
        # exact_volume = assemble(Constant(1.0)*dx(reference_mesh))
        # exact_area = assemble(Constant(1.0)*ds(reference_mesh))

        return multimesh, exact_volume, exact_area

    else:
        mesh = Mesh()
        XDMFFile("../../../propeller/meshes/propeller_" + clscale + ".xdmf").read(mesh)
        # XDMFFile("../../../propeller/propeller_0.0039062.xdmf").read(mesh)
        return mesh, exact_volume, exact_area


def build_propeller_2_mesh(clscale, create_multimesh):

    # Exact vol and area from freecad propeller2/propeller.py
    exact_volume = 7495.825123403876
    exact_area = 612.95003484977

    if create_multimesh:
        print("build_propeller_mesh clscale =", clscale)
        multimesh = MultiMesh()
        multimesh.label = clscale

        # # Add center first (swap variant)
        # mesh = Mesh()
        # XDMFFile("../../../propeller/meshes/center_" + clscale + ".xdmf").read(mesh)
        # multimesh.add(mesh)

        num_blades = int(args.tag)
        alpha = [i * 360 / num_blades for i in range(num_blades)]
        for i in range(num_blades):
            mesh = Mesh()
            XDMFFile("../../../propeller2/meshes/blade2_" + clscale + ".xdmf").read(
                mesh
            )
            # Hard code rotation center
            mesh.rotate(alpha[i], 2, Point(128, 720))
            multimesh.add(mesh)

        # Add center last as in the model
        mesh = Mesh()
        XDMFFile("../../../propeller2/meshes/circle2_" + clscale + ".xdmf").read(mesh)
        multimesh.add(mesh)
        multimesh.build(quadrature_order())

        return multimesh, exact_volume, exact_area

    else:
        mesh = Mesh()
        XDMFFile("../../../propeller2/meshes/propeller_" + clscale + ".xdmf").read(mesh)
        return mesh, exact_volume, exact_area


def build_separating_blocks_mesh(tmp, create_multimesh):
    """
        See e.g. separating_blocks_plot for generating appropriate call. It will look like
    parallel -j1 python3 -u elasticity_convergence.py --tag {1} --strong_bc ::: "1.776356839400250e-15" "1.776356839400250e-15" "3.552713678800501e-15" "3.552713678800501e-15" "7.105427357601002e-15" "7.105427357601002e-15" "1.421085471520200e-14" "1.421085471520200e-14" "2.842170943040401e-14" "2.842170943040401e-14" "5.684341886080801e-14" "5.684341886080801e-14" "1.136868377216160e-13" "1.136868377216160e-13" "2.273736754432321e-13" "2.273736754432321e-13" "4.547473508864641e-13" "4.547473508864641e-13" "9.094947017729282e-13" "9.094947017729282e-13" "1.818989403545856e-12" "1.818989403545856e-12" "3.637978807091713e-12" "3.637978807091713e-12" "7.275957614183426e-12" "7.275957614183426e-12" "1.455191522836685e-11" "1.455191522836685e-11" "2.910383045673370e-11" "2.910383045673370e-11" "5.820766091346741e-11" "5.820766091346741e-11" "1.164153218269348e-10" "1.164153218269348e-10" "2.328306436538696e-10" "2.328306436538696e-10" "4.656612873077393e-10" "4.656612873077393e-10" "9.313225746154785e-10" "9.313225746154785e-10" "1.862645149230957e-09" "1.862645149230957e-09" "3.725290298461914e-09" "3.725290298461914e-09" "7.450580596923828e-09" "7.450580596923828e-09" "1.490116119384766e-08" "1.490116119384766e-08" "2.980232238769531e-08" "2.980232238769531e-08" "5.960464477539062e-08" "5.960464477539062e-08" "1.192092895507812e-07" "1.192092895507812e-07" "2.384185791015625e-07" "2.384185791015625e-07" "4.768371582031250e-07" "4.768371582031250e-07" "9.536743164062500e-07" "9.536743164062500e-07" "1.907348632812500e-06" "1.907348632812500e-06" "3.814697265625000e-06" "3.814697265625000e-06" "7.629394531250000e-06" "7.629394531250000e-06" "1.525878906250000e-05" "1.525878906250000e-05" "3.051757812500000e-05" "3.051757812500000e-05" "6.103515625000000e-05" "6.103515625000000e-05" "1.220703125000000e-04" "1.220703125000000e-04" "2.441406250000000e-04" "2.441406250000000e-04" "4.882812500000000e-04" "4.882812500000000e-04" "9.765625000000000e-04" "9.765625000000000e-04" "1.953125000000000e-03" "1.953125000000000e-03" "3.906250000000000e-03" "3.906250000000000e-03" "7.812500000000000e-03" "7.812500000000000e-03" "1.562500000000000e-02" "1.562500000000000e-02" "3.125000000000000e-02" "3.125000000000000e-02" "6.250000000000000e-02" "6.250000000000000e-02" | tee aa.txt
    """

    Nx = 20
    h = 1 / Nx
    # offset = Point(1e-15, 1e-15)
    offset = Point(0.0, 0.0)
    clscale = h
    clscale_str = str(h)

    if create_multimesh:
        print("build_separating_blocks_mesh clscale =", clscale)
        multimesh = MultiMesh()
        multimesh.label = clscale_str

        mesh = UnitSquareMesh(Nx, Nx)
        multimesh.add(mesh)
        exact_volume = 1
        exact_area = 4

        # Add top mesh
        dx = 0.65
        Nx2 = int(round(dx / h))
        # p0 = Point((1-dx)/2, 1-0.15) + offset
        p0 = Point((1 - dx) / 2, 1) + offset
        mesh = RectangleMesh(p0, p0 + Point(dx, dx), Nx2, Nx2)

        y = float(args.tag)
        mesh.translate(Point(0.0, -y))
        multimesh.add(mesh)

        # dy is the length in y outside the unit square
        # dy = p0.y() + dx - 1 + y
        dy = dx - y
        exact_volume += dx * dy
        exact_area += 2 * dy

        # Add another mesh to the right that only sticks out distance x
        p0 = Point(1 - dx, (1 - dx) / 2) + offset
        mesh = RectangleMesh(p0, p0 + Point(dx, dx), Nx2, Nx2)
        x = float(args.tag)
        mesh.translate(Point(x, 0.0))
        exact_volume += dx * x
        exact_area += 2 * x
        multimesh.add(mesh)

        # # Test without translate for numerical stability if tag is small
        # #offset = Point(1e-10,1e-10)
        # dx = 0.65
        # delta = float(args.tag)
        # p0 = Point((1-dx)/2, 1-2*h+delta)
        # mesh = RectangleMesh(p0, p0 + Point(dx, dx+delta), Nx, Nx)
        # multimesh.add(mesh)

        # # dy is the length in y outside the unit square
        # dy = p0.y() + dx - 1
        # exact_volume = 1 + dx*dy
        # exact_area = 4 + 2*dy

        # # Add another mesh to the right that only sticks out distance x
        # p0 = Point(1-dx+delta, (1-dx)/2)
        # mesh = RectangleMesh(p0, p0 + Point(dx+delta, dx), Nx, Nx)
        # exact_volume += dx*delta
        # exact_area += 2*delta
        # multimesh.add(mesh)

        multimesh.build(quadrature_order())
        return multimesh, exact_volume, exact_area

    else:
        # Nonsense
        mesh = UnitSquareMesh(10, 10)
        return mesh, 999, 999


def build_separating_blocks_repair_mesh(tmp, create_multimesh):

    Nx = 20
    h = 1 / Nx
    # offset = Point(1e-15, 1e-15)
    offset = Point(0.0, 0.0)
    clscale = h
    clscale_str = str(h)

    if create_multimesh:
        print("build_separating_blocks_repair_mesh clscale =", clscale)
        multimesh = MultiMesh()
        multimesh.label = clscale_str

        meshes = []
        append_mesh(meshes, "../../../cad-defects/square1.xdmf")
        exact_volume = 1
        exact_area = 4

        append_mesh(meshes, "../../../cad-defects/square2.xdmf")
        dx = 0.65
        delta = 2**-5
        dy = dx - delta
        exact_volume += dx * dy
        exact_area += 2 * dy

        for mesh in meshes:
            multimesh.add(mesh)

        # Add another mesh to the right that only sticks out distance x
        Nx2 = int(round(dx / h))
        p0 = Point(1 - dx, (1 - dx) / 2) + offset
        mesh = RectangleMesh(p0, p0 + Point(dx, dx), Nx2, Nx2)
        x = delta
        mesh.translate(Point(x, 0.0))
        exact_volume += dx * x
        exact_area += 2 * x
        multimesh.add(mesh)

        # Repairs
        p0 = Point(0.9, 0.1)
        w = Point(0.1 - 1e-14, 0.1 - 1e-14)
        # w = Point(0.1, 0.1) # Slower but works
        Nx = int(round(2 * 0.1 / h))
        mesh = RectangleMesh(p0 - w, p0 + w, Nx, Nx)
        multimesh.add(mesh)

        p0 = Point((1 - dx) / 2 + 0.05, 1 - delta)
        p1 = p0 + Point(0.15, 0.15)
        Nx = int(round((p1 - p0).norm() / h))
        mesh = RectangleMesh(p0, p1, Nx, Nx)
        multimesh.add(mesh)

        # Circle
        meshes = []
        append_mesh(meshes, "../../../cad-defects/circle.xdmf")
        multimesh.add(meshes[0])

        multimesh.build(quadrature_order())
        return multimesh, exact_volume, exact_area

    else:
        # Nonsense
        mesh = UnitSquareMesh(10, 10)
        return mesh, 999, 999


def build_separating_diamonds_mesh(tmp, create_multimesh):
    """
       See e.g. separating_diamonds_plot for generating appropriate call. It will look like
    parallel -j1 python3 -u elasticity_convergence.py --tag {1} --strong_bc ::: "1.0e-02" "1.0e-03" "1.0e-04" "1.0e-05" "1.0e-06" "1.0e-07" "1.0e-08" "1.0e-09" "1.0e-10" "1.0e-11" "1.0e-12" "1.0e-13" "1.0e-14" | tee aa.txt
    """

    Nx = 19
    h = 1 / Nx
    offset = Point(1e-15, 1e-15)
    # offset = Point(0.,0.)
    clscale = h
    clscale_str = str(h)

    if create_multimesh:
        s = float(args.tag)
        print("build_separating_diamonds_mesh clscale =", clscale, "tag s =", s)
        multimesh = MultiMesh()
        multimesh.label = clscale_str

        mesh = UnitSquareMesh(Nx, Nx)
        multimesh.add(mesh)
        exact_volume = 1
        exact_area = 4

        # Add top mesh
        dx = 0.65
        Nx2 = int(round(dx / h))
        p0 = Point((1 - dx) / 2, 1 - dx / 2 + dx * 2**-0.5)
        mesh = RectangleMesh(p0, p0 + Point(dx, dx), Nx2, Nx2)
        mesh.rotate(45)
        mesh.translate(Point(0.0, -s))
        multimesh.add(mesh)

        # p0 = Point(1-dx/2*2**0.5-dx/2, (1-dx)/2) + offset
        # mesh = RectangleMesh(p0, p0 + Point(dx, dx), Nx2, Nx2)
        # mesh.rotate(45)
        # mesh.translate(Point(s, 0.0))
        # multimesh.add(mesh)

        # exact area and circumference is independent of s
        exact_volume = 1 + dx * dx
        exact_area = 4 - 2 * (2 * s) + dx * 4

        multimesh.build(quadrature_order())
        return multimesh, exact_volume, exact_area

    else:
        # Nonsense
        mesh = UnitSquareMesh(10, 10)
        return mesh, 999, 999


def build_bracket_mesh(clscale, create_multimesh):

    if create_multimesh:
        print("build_bracket_mesh", clscale)
        multimesh = MultiMesh()
        multimesh.label = clscale
        # Load all components (with desired mesh size) made by the main.cpp file. Results are typically put in meshes-from-src.
        meshes = []
        files = [
            "inner_mesh",
            "circle_mesh",
            "upper_diagonal_mesh",
            "lower_diagonal_mesh",
        ]
        print("outer_bend_mesh parts: ", end="")

        for f in files:
            append_mesh(
                meshes, "../../../bracket-cad/meshes-from-src/" + f + clscale + ".xdmf"
            )

        for p in range(0, 9999999):
            filename = (
                "../../../bracket-cad/meshes-from-src/outer_bend_mesh"
                + clscale
                + "_"
                + str(p)
                + ".xdmf"
            )
            if os.path.isfile(filename):
                print(p, end=" ")
                append_mesh(meshes, filename)
            else:
                break
        print("")
        for mesh in meshes:
            multimesh.add(mesh)
        multimesh.build(quadrature_order())

        # Reference (same or different resolution)
        filename = "../../../bracket-cad/geometry/flange2_" + clscale + ".xml"
        reference_mesh = Mesh(filename)
        exact_volume = assemble(Constant(1.0) * dx(reference_mesh))
        exact_area = assemble(Constant(1.0) * ds(reference_mesh))

        return multimesh, exact_volume, exact_area

    else:
        # Single mesh
        filename = "../../../bracket-cad/geometry/flange2_" + clscale + ".xml"
        print("load file", filename)
        mesh = Mesh(filename)
        print("single mesh nno, nel", mesh.num_vertices(), mesh.num_cells())
        return mesh


def build_bracket_2_mesh(clscale, create_multimesh):
    # This is with one piece outer bend
    # From bracket-cad-2/main.py:
    exact_area = 159.54086984556778
    exact_volume = 1186.8364544002325

    if create_multimesh:
        print("build_bracket_2_mesh", clscale)
        multimesh = MultiMesh()
        multimesh.label = clscale
        meshes = []

        for i in range(6):
            tag = ""
            if i == 2:
                # Choose triangle or circle hole
                # tag = "_triangle"
                tag = "_circle"
            filename = (
                "../../../bracket-cad-2/meshes/part_mesh_"
                + clscale
                + "_"
                + str(i)
                + tag
                + ".xdmf"
            )
            append_mesh(meshes, filename)

        for mesh in meshes:
            multimesh.add(mesh)
        multimesh.build(quadrature_order())
        return multimesh, exact_volume, exact_area

    else:
        # Single mesh
        filename = "../../../bracket-cad/geometry/flange2_" + clscale + ".xml"
        print("load file", filename)
        mesh = Mesh(filename)
        print("single mesh nno, nel", mesh.num_vertices(), mesh.num_cells())
        return mesh, exact_volume, exact_area


def build_bracket_3d_mesh(clscale, create_multimesh):
    """
    From the 2d plot we have
    circum = 159.54086984556778
    area = 1186.8364544002325
    Thus the 3d volume is
    exact_volume = area*1 = 1186.8364544002325
    exact_area = 2*area + circum*1 = 2533.213778646033
    """
    exact_area = 2533.213778646033
    exact_volume = 1186.8364544002325
    filedir = "../../../bracket-3d/meshes/"

    if create_multimesh:
        print("build_bracket_3d_mesh clscale =", clscale)
        multimesh = MultiMesh()
        multimesh.label = clscale
        meshes = []

        for i in range(7):
            tag = "__3d_0"
            # Choose triangle or circle hole
            # hole_type = "_triangle"
            hole_type = "_circle"
            if i == 2:
                if hole_type == "_circle":
                    filename = (
                        filedir
                        + "part_mesh_"
                        + clscale
                        + "_"
                        + str(i)
                        + hole_type
                        + tag
                        + ".xdmf"
                    )
                else:
                    continue
            elif i == 3:
                if hole_type == "_triangle":
                    import ipdb

                    ipdb.set_trace()
                    # triangle
                    filename = (
                        filedir
                        + "part_mesh_"
                        + clscale
                        + "_"
                        + str(i)
                        + hole_type
                        + tag
                        + ".xdmf"
                    )
                else:
                    continue
            else:
                filename = (
                    filedir + "part_mesh_" + clscale + "_" + str(i) + tag + ".xdmf"
                )

            append_mesh(meshes, filename)

        for j, mesh in enumerate(meshes):
            print("add multimesh part", j, mesh.num_cells())
            multimesh.add(mesh)

        multimesh.build(quadrature_order())
        return multimesh, exact_volume, exact_area

    else:
        # Single mesh: only dummy
        filename = filedir + "part_mesh_" + clscale + "_0__3d_0.xml"
        print("load file", filename)
        mesh = Mesh(filename)
        print("single mesh nno, nel", mesh.num_vertices(), mesh.num_cells())
        return mesh, exact_volume, exact_area


def build_beams3d_mesh(clscale, create_multimesh):
    # This is with one piece outer bend
    # From bracket-cad-2/main.py:
    exact_volume = 0.29260180166187305
    exact_area = 8.021945185788207

    if create_multimesh:
        print("build_beams3d_mesh", clscale)
        multimesh = MultiMesh()
        multimesh.label = clscale
        meshes = []

        # Load the primal beam mesh
        tag = "_3d_0"
        filename = "../geometry/beams-3d/meshes/beam0_" + clscale + tag + ".xdmf"
        L0 = 1
        w0 = 0.2
        meshes = []
        for i in range(12):
            mesh = Mesh()
            XDMFFile(filename).read(mesh)
            meshes.append(mesh)
        # 0, ..., 3 form the lower xy plane
        center = Point(0.5, 0.5, 0.5) * L0
        for i in range(1, 4):
            meshes[i].rotate(i * 90, 2, center)
        # 4, ..., 7 form the top xy plane
        tr = Point(0, 0, 1 - w0)
        for i in range(4, 8):
            meshes[i].rotate((i - 4) * 90, 2, center)
            meshes[i].translate(tr)
        # 8, ..., 12 form the vertical beams
        for i in range(8, 12):
            meshes[i].rotate(90, 1, center)
        tr9 = Point(-1 + w0, 0, 0)
        meshes[9].translate(tr9)
        tr10 = Point(0, 1 - w0, 0)
        meshes[10].translate(tr10)
        meshes[11].translate(tr9 + tr10)

        # # Perturb
        # eps = 1e-3
        # for i in range(12):
        #     d = i % 3
        #     pt = Point(0,0,0)
        #     pt[d] = i*eps
        #     meshes[i].translate(pt)

        for j, mesh in enumerate(meshes):
            print("add multimesh part", j, mesh.num_cells())
            XDMFFile("output/temp_mesh_part" + str(j) + "_" + clscale + ".xdmf").write(
                mesh
            )
            multimesh.add(mesh)

        multimesh.build(quadrature_order())
        return multimesh, exact_volume, exact_area

    else:
        # Single mesh
        filename = "../../../beams-3d/meshes/beam-singlemesh_" + clscale + "_3d_0.xdmf"
        print("load file", filename)
        # mesh = Mesh(filename)
        mesh = Mesh()
        XDMFFile(filename).read(mesh)
        print("single mesh nno, nel", mesh.num_vertices(), mesh.num_cells())
        return mesh, exact_volume, exact_area


def build_unitsquare_mesh(Nx, create_multimesh):

    if create_multimesh:
        multimesh = MultiMesh()
        multimesh.label = str(Nx)
        # multimesh.parameters["compress_volume_quadrature"] = args.compress_volume
        # multimesh.parameters["compress_interface_quadrature"] = args.compress_interface

        # Add background mesh
        mesh = UnitSquareMesh(Nx, Nx)
        multimesh.add(mesh)
        exact_volume = 1
        exact_area = 4

        # assert(args.num_parts <= 2)
        # if args.num_parts == 2:
        #     print("multimesh without random")
        #     x0, x1 = 0.3, 0.7
        #     y0, y1 = 0.4, 0.7
        #     Nx_part = int(max(abs(x1 - x0)*Nx, 1))
        #     Ny_part = int(max(abs(y1 - y0)*Nx, 1))
        #     mesh = RectangleMesh(Point(x0, y0), Point(x1, y1), Nx_part, Ny_part)

        #     phi = 29
        #     mesh.rotate(phi)

        #     coords = mesh.coordinates()
        #     is_interior = not numpy.any(coords < 0) and not numpy.any(coords > 1.)
        #     assert(is_interior)
        #     multimesh.add(mesh)

        # Set seed (use something that is the same for all Nx, for example
        # multimesh.num_parts())
        numpy.random.seed(multimesh.num_parts())

        # Add num_parts-1 random sized and rotated rectangular meshes
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

            s = "// Add new rectangle mesh ({:.3f}, {:.3f}) x ({:.3f}, {:.3f}).".format(
                x0, y0, x1, y1
            )
            s += " Rotation {:.1f} degrees.".format(phi)

            if is_interior:
                print(s)
                multimesh.add(mesh)

        multimesh.build(quadrature_order())

        # Check how many of the meshes are hidden
        num_hidden = 0
        for i in range(multimesh.num_parts()):
            if len(multimesh.cut_cells(i)) == 0 and len(multimesh.uncut_cells(i)) == 0:
                num_hidden = num_hidden + 1
                print("hidden part", i)
        if num_hidden == 0:
            print("no hidden parts")
        else:
            print("total number of hidden parts", num_hidden)

        # Remove hidden elements or use lock_inactive_dofs
        # if args.slim:
        #    multimesh = activate_uncut_cut_slim(multimesh)

        return multimesh, exact_volume, exact_area

    else:
        # Create single mesh
        mesh = UnitSquareMesh(Nx, Nx)
        return mesh


def setup_solver():
    solver = KrylovSolver("cg", "amg")
    solver.parameters["relative_tolerance"] = 1e-10
    solver.parameters["maximum_iterations"] = 10000
    solver.parameters["monitor_convergence"] = False
    return solver


def dump(filename, A):
    f = open(filename, "w")
    for r in range(A.size(0)):
        cols, vals = A.getrow(r)
        for i in range(len(cols)):
            s = str(r + 1) + " " + str(cols[i] + 1) + " " + str(vals[i]) + "\n"
            f.write(s)
    f.close()
    print(f"A=load('{filename}');A=sparse(A(:,1),A(:,2),A(:,3));condest(A)")


def condition_number_svd(A):
    print("condition_number_svd")
    # Exact, slow

    # Write dense matrix
    # numpy.savetxt("stiffnessmatrix"+tag+".txt", A.array())

    # # Write sparse matrix
    # filename = "output/A_" + str(A.size(0)) + "_" + args.tag + ".txt"
    # print("write to file", filename)
    # dump(filename, A)
    # return 0.0

    # Condition number using singular values
    timer = Timer()
    A_mat = A.mat()

    SVD = SLEPc.SVD()
    SVD.create()
    SVD.setOperator(A_mat)
    SVD.setType("trlanczos")
    nconv2 = -1
    svd_ncv = min(1024, A.size(0))
    tol = 1e-1  # This was sufficient! No big change from 1e-12
    nit = 1000
    SVD.setTolerances(tol=tol, max_it=nit)
    SVD.setFromOptions()

    # slepc4py use integers http://slepc.upv.es/slepc4py-current/docs/apiref/slepc4py.SLEPc.SVD.Which-class.html
    SVD_SMALLEST = 1
    SVD_LARGEST = 0

    while nconv2 <= 0:
        print("SLEPc try basis size", svd_ncv)
        SVD.setDimensions(nsv=1, ncv=svd_ncv)

        # Solve the svd problem for the smallest singular value
        SVD.setWhichSingularTriplets(SVD_SMALLEST)
        SVD.solve()
        nconv2 = SVD.getConverged()
        if nconv2 > 0:
            sigma_n = SVD.getSingularTriplet(0)
            print(
                "SLEPc number of converged eigenvalues and basis size", nconv2, svd_ncv
            )
        else:
            svd_ncv *= 2

    # Find largest
    SVD.setWhichSingularTriplets(SVD_LARGEST)
    SVD.solve()
    nconv1 = SVD.getConverged()
    if nconv1 > 0:
        sigma_1 = SVD.getSingularTriplet(0)
    else:
        print("error:  Unable to compute large singular value!")
        exit(1)

    condno = sigma_1 / sigma_n
    print("singular values", sigma_n, sigma_1, condno)
    print("computing singular values took", timer.elapsed()[0])
    return condno


def condition_number_eigenvalues(A):
    # At least ~5 error in condno with tolerance = 1e-1, but slow
    print("Compute condition number with A", A.size(0), "x", A.size(1))
    dump("output/A_" + str(A.size(0)) + ".txt", A)
    timer = Timer()
    eigensolver = SLEPcEigenSolver(A)
    eigensolver.parameters["spectrum"] = "smallest magnitude"
    eigensolver.parameters["tolerance"] = 1e-1  # Seems to be enough
    n = min(A.size(0), 5)
    eigensolver.solve(n)
    for i in range(n):
        r, c = eigensolver.get_eigenvalue(i)
        print(r, c, end="; ")
        if abs(c) > 1e-15 or r <= 0.0:
            print("unexpected small eigenvalue")
            import ipdb

            ipdb.set_trace()
        if i == 0:
            emin = r
    print()
    eigensolver.parameters["spectrum"] = "largest magnitude"
    eigensolver.solve(1)
    emax, c = eigensolver.get_eigenvalue(0)
    if abs(c) > 1e-15:
        print("unexpected large eigenvalue")
        import ipdb

        ipdb.set_trace()
    condno = emax / emin
    print("condition number slepc eigenvalues took", timer.elapsed()[0])
    print("condno", condno)
    return condno


def condition_number_amg(A):
    """Only works for small matrices, since A.array() is dense
    But: Be careful with tolerances.

    Eg. running the separating blocks example and A_6724_0.00+e00.txt
    written by condition_number_svd gives:
    >> condest(A)
    ans =
         6.630059376145282e+13

    Full matrix:
    >> cond(full(A))
    ans =
         3.974900286942120e+13

    By default, pyamg uses maxiter=25 which gives condno 0.00e+00 7634.93973747.
    NB: tol is not used!
    With maxiter=2500: 2.6e16
    With maxiter=25000: 1.9e16
    With maxiter=250000: 1.8e16

    Using pyamg.util.linalg.cond: cond=3.97120114172e+13 which matches matlab (takes 157 s).
    """
    print("condition_number_amg")
    from pyamg.util.linalg import condest

    timer = Timer()
    # condno = condest(A.array(), tol=1e-2, maxiter=2500)
    # ai, aj, av = A.getValuesCSR()
    # Asp = scipy.sparse.csr_matrix((av, aj, ai))
    mat = as_backend_type(A).mat()
    from scipy.sparse import csr_matrix

    Asp = csr_matrix(mat.getValuesCSR()[::-1], shape=mat.size)
    print("matrix size", A.size(0))
    condno = condest(Asp, maxiter=25)
    print("condest amg took", timer.elapsed()[0])
    print("condest condno", args.tag, condno)

    from pyamg.util.linalg import cond

    timer = Timer()
    condno = cond(Asp)
    print("full cond amg took", timer.elapsed()[0])
    print("full condno", args.tag, condno)
    return condno


def solve_single_elasticity(mesh, Nx, LX, LY, boundary):
    print("single mesh solver")
    timer_tot = Timer()
    timer_tot.start()
    timer = Timer()
    V = VectorFunctionSpace(mesh, "Lagrange", args.degree)
    print("single_mesh_dofs", V.dim())
    u = TrialFunction(V)
    v = TestFunction(V)
    f = rhs(LX, LY)
    F = inner(sigma(u), epsilon(v)) * dx - inner(f, v) * dx
    if not args.strong_bc:
        # Weak bc
        beta_N = Constant(args.beta_N * args.degree * args.degree)
        n = FacetNormal(mesh)
        h = 2.0 * Circumradius(mesh)
        F += (
            -inner(dot(sigma(u), n), v) * ds
            - inner(dot(sigma(v), n), u - exactsolution(LX, LY)) * ds
            + beta_N / h * 2 * mu * inner(u - exactsolution(LX, LY), v) * ds
            + beta_N / h * lmbda * inner(u - exactsolution(LX, LY), v) * ds
        )

    timer.start()
    A = PETScMatrix()
    b = PETScVector()
    a, L = system(F)
    assemble(a, tensor=A)
    assemble(L, tensor=b)
    print("single mesh assembly took", timer.elapsed()[0])
    if args.strong_bc:
        bc = DirichletBC(V, boundary[1], boundary[0])
        # condno = condition_number_amg(A)f
        # print("condno before", condno, A.size(0), b.sum(), A.norm("l1"))
        bc.apply(A, b)

    # Condition number
    # condno = condition_number_amg(A)
    condno = 0.0
    # print("condno after", condno, A.size(0), b.sum(), A.norm("l1"))
    # import ipdb; ipdb.set_trace()

    uh = Function(V, name="uh")
    timer.start()
    # if args.amg:
    #     # Define solver using setup_solver
    #     solver = setup_solver()
    #     solver.solve(A, uh.vector(), b)
    # else:
    #     solve(A, uh.vector(), b, "mumps")
    ##solve(A, uh.vector(), b, "mumps")
    print("single mesh solve took", timer.elapsed()[0])

    xdmffile = XDMFFile("output/uh_singlemesh_" + str(Nx) + ".xdmf")
    xdmffile.write(uh)

    # vm = von_mises(uh)
    # xdmffile = XDMFFile("output/von_mises_" + str(Nx) + ".xdmf")
    # xdmffile.write(vm)

    if args.dont_compute_errors:
        L2error = 0
        H10error = 0
        energy_error = 0
        vm_error = 0.0
        sxx_error = 0
        sxy_error = 0
        syy_error = 0
    else:
        stresses = compute_stresses(uh)
        for i in range(len(stresses)):
            for j in range(i, len(stresses[i])):
                xdmffile = XDMFFile("output/sigma_" + str(i) + str(j) + ".xdmf")
                xdmffile.write(stresses[i][j])

        # Single mesh errors
        L2error = errornorm(exactsolution(LX, LY), uh, "L2", degree_rise=2)
        H10error = errornorm(exactsolution(LX, LY), uh, "H10", degree_rise=2)
        energy_error = 0  # compute_strain_energy_error(A, uh, lhs(F), u, v)
        vm_error = 0  # von_mises_error(uh, LX, LY)
        sxx_error = 0  # stress_component_error(uh, LX, LY, 0)
        sxy_error = 0  # stress_component_error(uh, LX, LY, 1)
        syy_error = 0  # stress_component_error(uh, LX, LY, 2)

    sd = dict(
        dofs=V.dim(),
        L2_error=L2error,
        H10_error=H10error,
        energy_error=energy_error,
        vm_error=vm_error,
        sxx_error=sxx_error,
        sxy_error=sxy_error,
        syy_error=syy_error,
        condno=condno,
    )
    print("total single mesh solve took", timer_tot.elapsed()[0])
    return sd


def solve_multimesh_elasticity(multimesh, LX, LY, boundary):
    print("multimesh solver with num_parts", multimesh.num_parts())
    timer_tot = Timer()
    timer_tot.start()
    timer = Timer()

    # Define function space, trial and test functions and right-hand side
    V = MultiMeshVectorFunctionSpace(multimesh, "Lagrange", args.degree)

    # Count inactive dofs
    inactive_dofs = 0
    for p in range(multimesh.num_parts()):
        inactive_dofs += len(V.dofmap().inactive_dofs(multimesh, p))
    dofs = V.dim() - inactive_dofs
    print("multimesh_dofs", multimesh.num_parts(), args.stop, dofs)

    u = TrialFunction(V)
    v = TestFunction(V)

    # Define facet normal and mesh size
    n = FacetNormal(multimesh)
    h = 2.0 * Circumradius(multimesh)

    # Set parameters
    beta_N = Constant(args.beta_N * args.degree * args.degree)
    beta_N_bdry = beta_N  # Constant(10*args.degree*args.degree)
    beta_N_0 = beta_N
    beta_N_1 = beta_N
    beta_N_2 = beta_N
    beta_s = Constant(args.beta_s)

    f = rhs(LX, LY)
    F = -inner(f, v) * dX

    # if args.dim3: # Currently only for bracket3d
    #     # Traction
    #     # t = Constant((0, -1e6, 0))

    #     # # Part 2 is the circle
    #     # mesh_circle = multimesh.part(2)
    #     # surfdim = mesh_circle.topology().dim()-1
    #     # meshfcn = MeshFunction("size_t", mesh_circle, surfdim)
    #     # meshfcn.set_all(0)
    #     # class CircleBoundary(SubDomain):
    #     #     def inside(self, x, on_boundary):
    #     #         dx = x[0]-27
    #     #         dy = x[1]-24
    #     #         r = 3.0
    #     #         is_inside = on_boundary and x[1] < 24 and (dx**2 + dy**2 < 1.25*r*r)
    #     #         if is_inside:
    #     #             print(x[0], x[1], x[2])
    #     #         return is_inside
    #     # cb = CircleBoundary()
    #     # cb.mark(meshfcn, 1)
    #     #dsCC = Measure('dsC', domain=mesh_circle, subdomain_data=meshfcn)
    #     #F += -inner(t, v) * dsCC(1)
    #     '''File "/home/fenics/local/lib/python3.6/site-packages/dolfin/fem/form.py", line 23, in __init__
    #     self.subdomains, = list(sd.values())  # Assuming single domain
    #     ValueError: too many values to unpack (expected 1)'''

    #     '''
    #     - ds and dsC works: they force the traction on all of the boundary

    #     Other ideas:
    #     1. Add correct values to raw b vector instead
    #     2. Set up traction that is global, but more or less zero
    #     outside the domain of interest?
    #     3. Similar to 2 but use a dx integral with force term mostly zero.

    #     '''

    #     '''
    #     Same as above:
    #     self.subdomains, = list(sd.values())  # Assuming single domain
    #     ValueError: too many values to unpack (expected 1)

    #     dss = Measure('ds', domain=mesh_circle, subdomain_data=meshfcn)
    #     F += -inner(t, v) * dss(1)

    #     '''

    #     # Set up body force as load in circle
    #     class Delta(UserExpression):
    #         def __init__(self, eps, x0, **kwargs):
    #             self.eps = eps
    #             self.x0 = x0
    #             UserExpression.__init__(self, **kwargs)
    #         def eval(self, values, x):
    #             eps = self.eps
    #             values[0] = 0
    #             values[1] = eps/pi/(numpy.linalg.norm(x-self.x0)**2 + eps**2)
    #             values[2] = 0

    #             # r = 3.0
    #             # dx = x[0]-27
    #             # dy = x[1]-24+r
    #             # if abs(dx) < 1.5*r and abs(dy) < r:
    #             #     values[1] = -1

    #         def value_shape(self): return (3, )

    #     x0 = numpy.array([27, 24-3, 0.5])
    #     ff = Delta(eps=args.eps, x0=x0, degree=4)
    #     F += -inner(Constant(1e7)*ff, v)*dx

    F += (
        inner(sigma(u), epsilon(v)) * dX
        - inner(avg(sigma(u)), tensor_jump(v, n)) * dI
        - inner(avg(sigma(v)), tensor_jump(u, n)) * dI
        + beta_N / avg(h) * 2 * mu * inner(jump(u), jump(v)) * dI
        + beta_N / avg(h) * lmbda * inner(tensor_jump(u, n), tensor_jump(v, n)) * dI
    )

    # Stab std
    F += beta_s * inner(jump(sigma(u)), jump(grad(v))) * dO

    if not args.strong_bc:
        # Weak bc
        F += (
            -inner(dot(sigma(u), n), v) * dsC
            - inner(dot(sigma(v), n), u - exactsolution(LX, LY)) * dsC
            + beta_N / h * 2 * mu * inner(u - exactsolution(LX, LY), v) * dsC
            + beta_N / h * lmbda * inner(u - exactsolution(LX, LY), v) * dsC
        )

    # Ghost penalty
    # F += beta_N_2 * lmbda / avg(h) * inner(tensor_jump(u, n), tensor_jump(v, n))*dS

    # Assemble linear system
    parameters["linear_algebra_backend"] = "PETSc"
    A = PETScMatrix()
    b = PETScVector()
    a, L = system(F)
    print("start multimesh assembly")
    timer.start()
    assemble_multimesh(a, tensor=A)
    assemble_multimesh(L, tensor=b)
    print("multimesh assembly took", timer.elapsed()[0])

    print("b vector \in", b.min(), b.max())
    assert b.max() - b.min() > 0.0

    # Lock inactive dofs
    V.lock_inactive_dofs(A, b)

    if args.strong_bc:
        bc = MultiMeshDirichletBC(V, boundary[1], boundary[0])
        bc.apply(A, b)

    # Condition number
    # condno = condition_number_amg(A)
    # condno = condition_number_svd(A)

    # Since condition_number_amg is not accurate nor fast and svd is
    # slow, use matlab condest (takes 0.2 s with 6278 elements)
    condno = 0.0
    filename = (
        "output/A_"
        + str(A.size(0))
        + "_"
        + args.tag
        + "_"
        + str(float(args.beta_N))
        + ".txt"
    )
    print("write to file", filename)
    dump(filename, A)

    # Solve linear system
    uh = MultiMeshFunction(V)
    timer.start()
    ##solve(A, uh.vector(), b, "mumps")
    print("multimesh solve took", timer.elapsed()[0])
    print("uh \in", uh.vector().min(), uh.vector().max())

    # Generic file name
    def filename(basename, p, tag=""):
        ss = (
            "output"
            + "/"
            + basename
            + "_"
            + str(multimesh.num_parts())
            + "_"
            + multimesh.label
        )
        if tag != "":
            ss += "_" + tag
        ss += "_" + str(p) + ".xdmf"
        return ss

    # Write solution to file
    for p in range(multimesh.num_parts()):
        ufile = XDMFFile(filename("u", p, args.tag))
        ufile.write(uh.part(p))

    if args.dont_compute_errors:
        L2error = 0
        H10error = 0
        energy_error = 0
        vm_error = 0.0
        sxx_error = 0
        sxy_error = 0
        syy_error = 0
    else:

        # # Write stress
        # stresses = compute_stresses(uh)
        # for i in range(len(stresses)):
        #     for j in range(i, len(stresses[i])):
        #         for p in range(multimesh.num_parts()):
        #             xdmffile = XDMFFile(filename("sigma_" + str(i) + str(j), p, args.tag))
        #             xdmffile.write(stresses[i][j].part(p))

        L2error = errornorm(exactsolution(LX, LY), uh, "L2", degree_rise=3)
        H10error = errornorm(exactsolution(LX, LY), uh, "H10", degree_rise=2)
        energy_error = compute_strain_energy_error(A, uh, lhs(F), u, v)
        vm_error = 0.0  # von_mises_error(uh, LX, LY)
        sxx_error = stress_component_error(uh, LX, LY, 0)
        sxy_error = stress_component_error(uh, LX, LY, 1)
        syy_error = stress_component_error(uh, LX, LY, 2)

    # # Plot gradient
    # multimesh = uh.function_space().multimesh()
    # element = VectorElement('P', triangle, 1)
    # V = MultiMeshFunctionSpace(multimesh, element)
    # E = TrialFunction(V)
    # v = TestFunction(V)
    # a = dot(E, v)*dX \
    #     + beta_N / avg(h) * dot(jump(E), jump(v))*dI \
    #     + beta_s / avg(h)**2 * dot(jump(E), jump(v))*dO
    # A = assemble_multimesh(a)
    # Pgradu = list()
    # for d in range(len(n)):
    #     L = dot(-grad(uh[d]), v)*dX
    #     b = assemble_multimesh(L)
    #     V.lock_inactive_dofs(A, b)
    #     Pgradu.append(MultiMeshFunction(V))
    #     solve(A, Pgradu[d].vector(), b)
    # for p in range(multimesh.num_parts()):
    #     for d in range(len(n)):
    #         gradufile = XDMFFile(filename("gradu", p))
    #         gradufile.write(Pgradu[d].part(p))

    # # Plot error
    # eu = project(uh-exactsolution(), V)
    # for p in range(multimesh.num_parts()):
    #     efile = XDMFFile(filename("e", p))
    #     efile.write(eu.part(p))

    # # Plot gradient error
    # Pgrade = list() # For each dimension
    # for d in range(len(n)):
    #     Pgrade.append(project(Pgradu[d] - exactgradient(d), V))

    # FE = VectorElement("Lagrange", triangle, args.degree)
    # for d in range(len(n)):
    #     grade = MultiMeshFunction(V)
    #     for p in range(multimesh.num_parts()):
    #         graduh_p = Pgradu[d].part(p)
    #         mesh_p = multimesh.part(p)
    #         Vp = FunctionSpace(mesh_p, FE)
    #         graduh_p_interp = interpolate(graduh_p, Vp)
    #         gradu_exact = interpolate(exactgradient(d), Vp)
    #         graddiff = Function(Vp)
    #         graddiff.vector()[:] = graduh_p_interp.vector() - gradu_exact.vector()
    #         if d == 0 and p == 1:
    #             print(gradu_exact.vector().get_local())
    #             print(graduh_p_interp.vector().get_local())
    #             print(graddiff.vector().get_local())

    #         gradexact = Function(Vp)
    #         gradexact.vector()[:] = gradu_exact.vector()
    #         gradu = Function(Vp)
    #         gradu.vector()[:] = graduh_p_interp.vector()

    #         #diff.vector()[:] = gradu_exact.vector()
    #         #diff.vector()[:] = graduh_p_interp.vector()
    #         grade.assign_part(p, graddiff)
    #         gradefile = XDMFFile(filename("grade", p))
    #         gradefile.write(grade.part(p))

    #         ff = XDMFFile("output/graddiff"+str(p)+"_"+str(d)+".xdmf")
    #         ff.write(graddiff)
    #         ff = XDMFFile("output/gradexact"+str(p)+"_"+str(d)+".xdmf")
    #         ff.write(gradexact)
    #         ff = XDMFFile("output/gradu"+str(p)+"_"+str(d)+".xdmf")
    #         ff.write(gradu)

    # exact_gradu = exactgradient()
    # Pgrade = project(Pgradu - exact_gradu, V)
    # for p in range(multimesh.num_parts()):
    #     for d in range(len(n)):
    #         gradefile = XDMFFile(filename("grade", p))
    #         gradefile.write(Pgrade[d].part(p))

    # # Debug: Check convergence of individual terms
    # u = uh
    # v = uh
    # F = [inner(sigma(u), epsilon(v))*dX,
    #      - inner(avg(dot(sigma(u), n)), jump(v))*dI,
    #      - inner(avg(dot(sigma(v), n)), jump(u))*dI,
    #      beta_N_0 * (2*mu + lmbda) / avg(h) * inner(jump(u), jump(v))*dI,
    #      beta_N_1 * 2*mu / avg(h) * inner(jump(u), jump(v))*dI,
    #      beta_N_2 * lmbda / avg(h) * inner(jump(u, n), jump(v, n))*dI,
    #      beta_s * inner(jump(sigma(u)), jump(epsilon(v)))*dO]
    # print(hmax, end=" ")
    # for F_i in F:
    #     #f.append(assemble_multimesh(F_i))
    #     print("{:e}".format(assemble_multimesh(F_i)), end=" ")
    # print("")

    sd = dict(
        dofs=dofs,
        L2_error=L2error,
        H10_error=H10error,
        energy_error=energy_error,
        vm_error=vm_error,
        sxx_error=sxx_error,
        sxy_error=sxy_error,
        syy_error=syy_error,
        condno=condno,
    )
    print("total multimesh solve took", timer_tot.elapsed()[0])
    return sd


def check_vol(mesh, exact_volume, exact_area):
    if isinstance(mesh, cpp.mesh.MultiMesh):
        print("multimesh check_vol")
        mesh_type = "multimesh"
        # # Test rebuild and use smaller quadrature rule: no change for propeller
        # multimesh = MultiMesh()
        # for i in range(mesh.num_parts()):
        #     multimesh.add(mesh.part(i))
        # multimesh.build(1)
        # vol = multimesh.compute_volume()
        # area = multimesh.compute_area()
        vol = mesh.compute_volume()
        area = mesh.compute_area()
        dsC_area = assemble_multimesh(1.0 * dsC(domain=mesh))
        rel_dsC = abs(area - dsC_area) / area
        print("relative error dsC area", rel_dsC)
        assert rel_dsC < 1e-10
        print("multimesh dsC area", dsC_area)
    else:
        print("single mesh check_vol")
        mesh_type = "single mesh"
        vol = assemble(1.0 * dx(domain=mesh))
        area = assemble(1.0 * ds(domain=mesh))

    def measure_error(vol, exact_volume, tag, mesh_type):
        volume_error = abs(vol - exact_volume) / exact_volume
        print(mesh_type, tag, vol, "(exact =", exact_volume)
        print(mesh_type, tag, "with delta=", args.tag, "relative error", volume_error)
        # if (volume_error > 1e-10):
        #    print("   WARNING: large", tag, "error")
        return volume_error

    relative_volume_error = measure_error(vol, exact_volume, "volume", mesh_type)
    relative_area_error = measure_error(area, exact_area, "area", mesh_type)

    if isinstance(mesh, cpp.mesh.MultiMesh):
        f = open(args.volfile, "at")
        s = (
            args.tag
            + " "
            + str(vol)
            + " "
            + str(area)
            + " "
            + str(relative_volume_error)
            + " "
            + str(relative_area_error)
            + "\n"
        )
        f.write(s)
        f.close()

    return relative_volume_error, relative_area_error


# def print_multimesh_info(multimesh, i, param):
#     hmin=[]; hmax=[]; nc=[]; nv=[]; vol=[]; area=[]
#     for p in range(multimesh.num_parts()):
#         mesh = multimesh.part(p)
#         hmin.append(mesh.hmin())
#         hmax.append(mesh.hmax())
#         nc.append(mesh.num_cells())
#         nv.append(mesh.num_vertices())
#         vol.append(assemble(1.0*dx(domain=mesh))),
#         area.append(assemble(1.0*ds(domain=mesh)))
#         print("mmp", p, hmin[-1], hmax[-1], nc[-1], nv[-1], vol[-1], area[-1])
#     print("mm", i, param, multimesh.num_parts(), numpy.mean(hmin), numpy.mean(hmax), numpy.sum(nc), numpy.sum(nv), multimesh.compute_volume(), multimesh.compute_area())


def add_geom_info(d, mesh, exact_volume, exact_area):
    if isinstance(mesh, cpp.mesh.MultiMesh):
        hmax = 0.0
        for p in range(mesh.num_parts()):
            hmax = max(hmax, mesh.part(p).hmax())
    else:
        hmax = mesh.hmax()
    d["hmax"] = hmax
    # Add relative vol & area error to dict
    relative_volume_error, relative_area_error = check_vol(
        mesh, exact_volume, exact_area
    )
    d["vol_error"] = relative_volume_error
    d["area_error"] = relative_area_error
    return d


def run(build_mesh_fcn, mesh_parameters, LX, LY, boundary):

    timer = Timer()
    smdata = list()
    mmdata = list()

    for i in range(len(mesh_parameters)):
        print("")
        print(i, mesh_parameters[i])
        print("polynomial degree", args.degree)
        print("quadrature order", quadrature_order())

        # Single mesh
        mesh, exact_volume, exact_area = build_mesh_fcn(mesh_parameters[i], False)
        # print("sm", i, mesh_parameters[i], 1, mesh.hmin(), mesh.hmax(), mesh.num_cells(), mesh.num_vertices(), assemble(1.0*dx(domain=mesh)), assemble(1.0*ds(domain=mesh)))
        if not args.only_geometry and (
            args.tag == "" or float(args.tag) == 4
        ):  # only relevant to run with four blades
            sm = solve_single_elasticity(mesh, mesh_parameters[i], LX, LY, boundary)
        else:
            sm = dict(
                hmax=0,
                dofs=0,
                L2_error=0,
                H10_error=0,
                energy_error=0,
                vm_error=0,
                sxx_error=0,
                sxy_error=0,
                syy_error=0,
                condno=0,
                area_error=0,
                vol_error=0,
            )
        sm = add_geom_info(sm, mesh, exact_volume, exact_area)
        print("single mesh dict", sm)
        smdata.append(sm)

        # Multimesh
        timer.start()
        multimesh, exact_volume, exact_area = build_mesh_fcn(mesh_parameters[i], True)
        # check_vol(multimesh, exact_volume, exact_area)
        # print_multimesh_info(multimesh, i, mesh_parameters[i])
        print("multimesh construction took", timer.elapsed()[0])
        if not args.only_geometry:
            mm = solve_multimesh_elasticity(multimesh, LX, LY, boundary)
        else:
            mm = dict(
                hmax=0,
                dofs=0,
                L2_error=0,
                H10_error=0,
                energy_error=0,
                vm_error=0,
                sxx_error=0,
                sxy_error=0,
                syy_error=0,
                condno=0,
                area_error=0,
                vol_error=0,
            )
        mm = add_geom_info(mm, multimesh, exact_volume, exact_area)
        print("multimesh dict", mm)
        mmdata.append(mm)

    # Error rates
    def rates(err, h):
        r = numpy.log(err[1:] / err[:-1]) / numpy.log(h[1:] / h[:-1])
        r = numpy.append(r, numpy.nan)
        return r

    def extract(key, dictname):
        lst = [d[key] for d in dictname]
        arr = numpy.array(lst)
        # print(key, len(arr))
        return arr

    hs = extract("hmax", smdata)
    hm = extract("hmax", mmdata)
    dofs = extract("dofs", smdata)
    dofm = extract("dofs", mmdata)
    L2errors = extract("L2_error", smdata)
    L2errorm = extract("L2_error", mmdata)
    H10errors = extract("H10_error", smdata)
    H10errorm = extract("H10_error", mmdata)
    energy_errors = extract("energy_error", smdata)
    energy_errorm = extract("energy_error", mmdata)
    sxx_errors = extract("sxx_error", smdata)
    sxx_errorm = extract("sxx_error", mmdata)
    sxy_errors = extract("sxy_error", smdata)
    sxy_errorm = extract("sxy_error", mmdata)
    syy_errors = extract("syy_error", smdata)
    syy_errorm = extract("syy_error", mmdata)
    vm_errors = extract("vm_error", smdata)
    vm_errorm = extract("vm_error", mmdata)
    # condnos = extract("condno", smdata)
    # condnom = extract("condno", mmdata)
    area_errors = extract("area_error", smdata)
    area_errorm = extract("area_error", mmdata)
    vol_errors = extract("vol_error", smdata)
    vol_errorm = extract("vol_error", mmdata)

    L2rates = rates(L2errors, hs)
    L2ratem = rates(L2errorm, hm)
    H10rates = rates(H10errors, hs)
    H10ratem = rates(H10errorm, hm)
    energy_rates = rates(energy_errors, hs)
    energy_ratem = rates(energy_errorm, hm)
    sxx_rates = rates(sxx_errors, hs)
    sxx_ratem = rates(sxx_errorm, hm)
    sxy_rates = rates(sxy_errors, hs)
    sxy_ratem = rates(sxy_errorm, hm)
    syy_rates = rates(syy_errors, hs)
    syy_ratem = rates(syy_errorm, hm)
    vm_rates = rates(vm_errors, hs)
    vm_ratem = rates(vm_errorm, hm)
    # condnorates = rates(condnos, hs)
    # condnoratem = rates(condnom, hm)
    area_rates = rates(area_errors, hs)
    area_ratem = rates(area_errorm, hm)
    vol_rates = rates(vol_errors, hs)
    vol_ratem = rates(vol_errorm, hm)

    print("num data points", len(L2rates))

    # Write to file
    filename = "table"
    for arg in sorted(vars(args)):
        if arg not in args_to_skip:
            print(arg, getattr(args, arg))
            filename += "_" + str(arg) + "_" + str(getattr(args, arg))
    filename += ".txt"
    f = open(filename, "w")
    s = "Single mesh \t\t\t\t\t\t MultiMesh" + str(args)
    print(s)
    # f.write(s + "\n")

    np = 9
    hf = "    %.5e "
    dofsf = "%i    "
    errf = "%.12e " * np
    ratef = "%.3f " * np
    formats = (hf + dofsf + errf + ratef + "   ") * 2

    for i in range(len(L2rates)):
        s = formats % (
            hs[i],
            dofs[i],
            L2errors[i],  # 3
            H10errors[i],
            sxx_errors[i],
            sxy_errors[i],
            syy_errors[i],
            vm_errors[i],
            energy_errors[i],
            area_errors[i],  # 10
            vol_errors[i],
            #
            L2rates[i],
            H10rates[i],
            sxx_rates[i],
            sxy_rates[i],
            syy_rates[i],
            vm_rates[i],
            energy_rates[i],
            area_rates[i],
            vol_rates[i],
            #
            hm[i],  # 21
            dofm[i],
            L2errorm[i],  # 23
            H10errorm[i],
            sxx_errorm[i],
            sxy_errorm[i],
            syy_errorm[i],
            vm_errorm[i],
            energy_errorm[i],
            area_errorm[i],
            vol_errorm[i],  # 31
            #
            L2ratem[i],
            H10ratem[i],
            sxx_ratem[i],
            sxy_ratem[i],
            syy_ratem[i],
            vm_ratem[i],
            energy_ratem[i],
            area_ratem[i],
            vol_ratem[i],
        )
        f.write(s + "\n")
        print(s)
    f.close()


if __name__ == "__main__":

    for arg in sorted(vars(args)):
        print(arg, getattr(args, arg))
    # set_log_level(10)

    if args.dim3:
        domain = "bracket3d"
        LX = 10
        LY = 10
        # domain = "beams3d"; LX = 1; LY = 1
    else:
        # domain = "unitsquare"; LX = 1; LY = 1
        # domain = "bracket"; LX = 10; LY = 10
        # domain = "bracket2"; LX = 10; LY = 10
        # domain = "propeller"; LX = 30; LY = 20
        # domain = "propeller2"; LX = 30; LY = 20
        # domain = "separating_blocks"; LX = 0.3; LY = 0.3
        # domain = "separating_blocks_repair"; LX = 0.3; LY = 0.3
        domain = "separating_diamonds"
        LX = 0.3
        LY = 0.3

    # Setup which function to call to generate mesh and appropriate
    # mesh parameters
    if domain == "unitsquare":
        powers = range(args.start + 2, args.stop + 2 + 1)
        NNx = numpy.power(2, powers)
        print("NNx =", NNx)
        mesh_parameters = NNx
        build_mesh_fcn = build_unitsquare_mesh

    elif domain == "bracket":
        # We cannot run all these bracket cases due to Duplication of MPI communicator failed error
        # clscales = ["2", "1", "0.5", "0.25", "0.125", "0.0625", "0.03125", "0.015625"]
        clscales = ["2", "1", "0.5", "0.25", "0.125"]
        clscales = clscales[0 : min(len(clscales), args.stop + 1)]
        print("clscales =", clscales)
        mesh_parameters = clscales
        build_mesh_fcn = build_bracket_mesh

    elif domain == "bracket2":
        clscales = ["2", "1", "0.5", "0.25", "0.125", "0.0625", "0.03125"]
        clscales = clscales[0 : min(len(clscales), args.stop + 1)]
        print("clscales =", clscales)
        mesh_parameters = clscales
        build_mesh_fcn = build_bracket_2_mesh

        class Boundary(SubDomain):
            def inside(self, x, on_boundary):
                return near(x[0], 0.0) and on_boundary

        boundary = (Boundary(), exactsolution(LX, LY))

    elif domain == "bracket3d":
        clscales = [
            "16",
            "8",
            "4",
            "2",
            "1",
            "0.5",
            "0.25",
            "0.125",
            "0.0625",
            "0.03125",
        ]
        clscales = clscales[args.start : min(len(clscales), args.stop + 1)]
        print("clscales =", clscales)
        mesh_parameters = clscales
        build_mesh_fcn = build_bracket_3d_mesh
        # class Boundary(SubDomain):
        #     def inside(self, x, on_boundary):
        #         return near(x[0], 0.0) and on_boundary
        # boundary_domain = Boundary()
        # boundary = (boundary_domain, Constant((0.0, 0.0, 0.0)))

    elif domain == "propeller":
        clscales = ["8", "4", "2", "1", "0.5", "0.25", "0.125"]
        clscales = clscales[args.start : args.stop + 1]
        print("clscales =", clscales)
        mesh_parameters = clscales
        build_mesh_fcn = build_propeller_mesh  # Set number of blades with tag

    elif domain == "propeller2":
        clscales = [
            "8",
            "4",
            "2",
            "1",
            "0.5",
            "0.25",
            "0.125",
            "0.0625",
        ]  # , "0.03125"]
        clscales = clscales[args.start : args.stop + 1]
        print("clscales =", clscales)
        mesh_parameters = clscales
        build_mesh_fcn = build_propeller_2_mesh  # Set number of blades with tag

    elif domain == "separating_blocks":
        # clscales = ["0.0333"]
        # clscales = clscales[args.start:args.stop+1]
        # print("clscales =", clscales)
        mesh_parameters = [None]  # Set mesh size when building mesh
        build_mesh_fcn = build_separating_blocks_mesh  # Move blocks with tag

        class Boundary(SubDomain):
            def inside(self, x, on_boundary):
                return near(x[1], 0.0) and on_boundary

        boundary = (Boundary(), exactsolution(LX, LY))

    elif domain == "separating_blocks_repair":
        # clscales = ["0.0333"]
        # clscales = clscales[args.start:args.stop+1]
        # print("clscales =", clscales)
        mesh_parameters = [None]  # Set mesh size when building mesh
        build_mesh_fcn = build_separating_blocks_repair_mesh  # Move blocks with tag

        class Boundary(SubDomain):
            def inside(self, x, on_boundary):
                return near(x[1], 0.0) and on_boundary

        boundary = (Boundary(), exactsolution(LX, LY))

    elif domain == "separating_diamonds":
        # clscales = ["0.0333"]
        # clscales = clscales[args.start:args.stop+1]
        # print("clscales =", clscales)
        mesh_parameters = [None]  # Set mesh size when building mesh
        build_mesh_fcn = build_separating_diamonds_mesh  # Move blocks with tag

        class Boundary(SubDomain):
            def inside(self, x, on_boundary):
                return near(x[1], 0.0) and on_boundary

        boundary = (Boundary(), exactsolution(LX, LY))

    elif domain == "beams3d":
        # Remember to use strong_bc
        assert args.strong_bc
        clscales = ["0.25", "0.125", "0.0625", "0.03125", "0.015625", "0.0078125"]
        clscales = clscales[args.start : args.stop + 1]
        print("clscales =", clscales)
        mesh_parameters = clscales
        build_mesh_fcn = build_beams3d_mesh  # Set number of blades with tag

    elif domain == "squares":
        Nx = [4, 8, 16, 32, 64, 128]
        Nx = Nx[args.start : args.stop + 1]
        print("Nx =", Nx)
        mesh_parameters = Nx
        build_mesh_fcn = build_squares

    else:
        import ipdb

        ipdb.set_trace()

    # Set as default if not already set
    try:
        boundary
    except NameError:
        print("Use default data for bc")

        class Boundary(SubDomain):
            def inside(self, x, on_boundary):
                return on_boundary

        boundary = (Boundary(), exactsolution(LX, LY))
    else:
        print("Use custom bc data")

    # Run the simulation
    run(build_mesh_fcn, mesh_parameters, LX, LY, boundary)
