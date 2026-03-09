# FreeCAD object administration utilities (don't do geometry operations here)
import FreeCAD

def open(FCStd_name_long):
    from pathlib import Path
    FCStd_name = Path(FCStd_name_long).stem
    FCStd_name_dash = FCStd_name.replace('-', '_') # There's sth fishy with -
    docs = FreeCAD.listDocuments()
    #print(FCStd_name, FCStd_name_dash)
    #import pprint
    #pprint.pprint(docs)
    #print(FCStd_name in docs)
    if FCStd_name in docs:
        return docs[FCStd_name]
    elif FCStd_name_dash in docs:
        return docs[FCStd_name_dash]
    else:
        return FreeCAD.open(FCStd_name_long)
        
def flatten(x):
    import collections
    if isinstance(x, collections.Iterable):
        return [a for i in x for a in flatten(i)]
    else:
        return [x]

def printif(s):
    if debug:
        print(s)

def get_objects(names):
    objects = []
    for name in names:
        objects.append(FreeCAD.ActiveDocument.getObject(name))
    return objects
    
def hide_objects(olist, doc=FreeCAD.ActiveDocument):
    if not isinstance(olist, list):
        olist = [olist]
    #docname = doc.Name
    #guidoc = Gui.getDocument(docname)
    if isinstance(olist[0], str):
        for name in olist:
            #print("docname", doc.Name)
            #print("try to hide " + name)
            obj = doc.getObject(name)
            #print("obj", obj)
            #assert obj, name
            #obj.ViewObject.hide()
            guiobj = obj.ViewObject
            guiobj.Visibility = False
            #Gui.ActiveDocument.getObject(name).Visibility=False # Must for groups
            #guidoc.getObject(name).Visibility=False
    else:
        for obj in olist:
            #print("try to hide object " + obj.Name)
            #obj.ViewObject.hide()
            #Gui.ActiveDocument.getObject(obj.Name).Visibility=False
            try:
                doc.getObject(obj.Name).Visibility = False
                obj.ViewObject.hide()
            except:
                obj.ViewObject.hide()
            #FreeCAD.ActiveDocument.recompute()

def show_objects(olist):
    if not isinstance(olist, list):
        olist = [olist]
    if isinstance(olist[0], str):
        for name in olist:
            #printif("try to hide " + name)
            obj = FreeCAD.ActiveDocument.getObject(name)
            obj.ViewObject.show()
    else:
        for obj in olist:
            #printif("try to hide object " + obj.Name)
            obj.ViewObject.show()
    #FreeCAD.ActiveDocument.recompute()

    
def convert_point_to_vector(p):
    v = FreeCAD.Vector(p.X, p.Y, p.Z)
    return v

def move_to_group(doc, olist, groupname):
    group = FreeCAD.ActiveDocument.getObject(groupname)
    print("group",group)
    if isinstance(olist[0], str):
        for name in olist:
            obj = FreeCAD.ActiveDocument.getObject(name)
            group.addObject(obj)
    else:
        for obj in olist:
            group.addObject(obj)

def print_spline(e, name="name", objcnt=0):
    c = e.Curve
    print(f"obj{objcnt} = doc.addObject(\"Part::Feature\", \"{name}\")")
    print("bs = Part.BSplineCurve()")
    print("knots =", c.getKnots())
    print("mults =", c.getMultiplicities())
    print("poles =", str(c.getPoles()).replace("Vector", "FreeCAD.Vector"))
    print("degree =", c.Degree)
    print("periodic = False")
    print("weights =", c.getWeights())
    print("bs.buildFromPolesMultsKnots(poles, mults, knots, periodic, degree, weights)")
    print(f"obj{objcnt}.Shape = bs.toShape()")
    
def print_circle(e, name="name", objcnt=0):
    c = e.Circle
    print(f"obj{objcnt} = doc.addObject(\"Part::Feature\", \"{name}\")")
    print("r = ", c.Radius)
    print("x = ", str(c.Location).replace("Vector", "FreeCAD.Vector"))
    print("circle = Part.makeCircle(x, FreeCAD.Vector(0,1,0), r)")
    print(f"obj{objcnt}.Shape = circle.toShape()")

def print_line(edge, name="name", objcnt=0):
    print(f"obj{objcnt} = doc.addObject(\"Part::Feature\", \"{name}\")")
    print("p0 = ", str(edge.Vertexes[0].Point).replace("Vector", "FreeCAD.Vector"))
    print("p1 = ", str(edge.Vertexes[1].Point).replace("Vector", "FreeCAD.Vector"))
    print(f"obj{objcnt}.Shape = Part.makeLine(p0,p1)")
                     
def print_generic(edge, name="name", objcnt=0):
    import Part
    if isinstance(edge.Curve, Part.BSplineCurve):
        print_spline(edge, name, objcnt)
    elif isinstance(edge.Curve, Part.Line):
        print_line(edge, name, objcnt)
    #elif isinstance(e, Part.Circle): # not tested
    #    print_circle(e, name)
    else:
        print("not implemented instance", type(edge))
    
    
def create_faces(doc, objs, direction, facename):
    # Objs must be wires
    faces = []
    import Draft
    for i, o in enumerate(objs):
        assert(len(o.Shape.Edges) == 1)
        
        # Copy
        o2 = Draft.move(o, direction, copy=True)

        # Fill
        faceobj = doc.addObject('Part::RuledSurface', facename + "_" + str(i))
        faceobj.Curve1 = (o, ['Edge1'])
        faceobj.Curve2 = (o2, ['Edge1'])
        faces.append(faceobj)
    return faces
    
def set_label(objs, label):
    for o in objs:
        o.label = label

def extrude(doc, objs, direction, distance, symmetric, name):
    if not isinstance(objs, list):
        objs = [objs]
    out = []
    for i, obj in enumerate(objs):
        print("extrude", obj.Name)
        f = doc.addObject('Part::Extrusion', name + "_" + str(i)) 
        f.Base = obj
        f.DirMode = "Custom"
        f.Dir = direction
        f.DirLink = None
        f.LengthFwd = distance
        f.LengthRev = 0.0
        f.Solid = True
        f.Reversed = False
        f.Symmetric = symmetric
        f.TaperAngle = 0.0
        f.TaperAngleRev = 0.0
        f.Base.ViewObject.hide()
        hide_objects(obj, doc)
        out.append(f)
    if len(out) == 1:
        out = out[0]
    hide_objects(objs)
    hide_objects(objs, doc)
    return out

    # import Draft
    # if not isinstance(objs, list):
    #     objs = [objs]
    # oo = []
    # for i,o in enumerate(objs):
    #     print("extrude", name, i)
    #     o2 = Draft.extrude(o, distance*direction)
    #     o2.Label = name + "_" + str(i)
    #     oo.append(o2)
    # oo = move_to_doc(oo, doc)
    # return oo
    
def cut(doc, obj1, obj2, name):
    obj = doc.addObject("Part::Cut", name)
    obj.Base = obj1
    obj.Tool = obj2
    #hide_objects([obj1, obj2])
    return obj

    # if not isinstance(obj2, list):
    #     obj2 = [obj2]
    # objs = []
    # for i, o2 in enumerate(obj2):
    #     obj = doc.addObject("Part::Cut", name+"_"+str(i))
    #     obj.Base = obj1
    #     obj.Tool = o2
    #     doc.recompute()
    #     objs.append(obj)
    # hide_objects(obj1)
    # hide_objects(obj2)
    # return objs
    
def compound(doc, objs, name):
    from itertools import chain
    objs = flatten(objs)
    cmpnd = doc.addObject("Part::Compound", name)
    cmpnd.Links = objs
    doc.recompute()
    return cmpnd

def close():
    for k in FreeCAD.listDocuments():
        FreeCAD.closeDocument(k)
    
def spline(doc,pts,name,interpolate=True,it=None,ft=None):
    FreeCAD.setActiveDocument(doc.Name)
    # 3D if needed
    if len(pts[0]) == 2:
        pts2 = []
        for p in pts:
            pts2.append(flatten([p, 0.0]))
        print("3d:", pts2)
        pts = pts2

    import Part
    obj = doc.addObject("Part::Feature", name)
    bs = Part.BSplineCurve()
    if it is None:
        if interpolate:
            bs.interpolate(Points=pts, PeriodicFlag=False)
        else:
            bs.approximate(Points=pts)
    else:
        bs.interpolate(Points=pts, InitialTangent=it, FinalTangent=ft)
    obj.Shape = bs.toShape()
    import Draft
    for p in pts:
        if isinstance(p, list) or isinstance(p, tuple):
            Draft.makePoint(FreeCAD.Vector(p[0],p[1],p[2]))
        else:
            Draft.makePoint(p)
    return obj

def splineinfo(obj):
    print(obj.Name, obj.Label)
    c = obj.Shape.Edges[0].Curve
    print("poles",len(c.getPoles()), c.getPoles())
    print("mult",len(c.getMultiplicities()),c.getMultiplicities())
    print("knots",len(c.getKnots()),c.getKnots())
    print("degree",c.Degree)
    print("weights",len(c.getWeights()),c.getWeights())
    return c, c.getPoles(), c.getMultiplicities(), c.getKnots(), c.Degree, c.getWeights()

def spline2(doc,poles,mults,knots,degree,weights,name):
    # check
    #assert(sum(mults)-degree-1 == len(poles))
    assert_bs(poles, knots, degree, mults, weights)
    # import Draft
    # for p in poles:
    #     try:
    #         Draft.makePoint(p)
    #     except:
    #         Draft.makePoint(FreeCAD.Vector(p))
    import Part
    obj = doc.addObject("Part::Feature", name)
    bs = Part.BSplineCurve()
    periodic = False
    bs.buildFromPolesMultsKnots(poles, mults, knots, periodic, degree, weights)
    obj.Shape = bs.toShape()
    return obj

def spline3(doc,curve,name):
    import Part
    obj = doc.addObject("Part::Feature", name)
    bs = Part.BSplineCurve(curve)
    obj.Shape = bs.toShape()
    return obj

def plotknots(doc,bs):
    kk = bs.getKnots()
    import Draft
    for k in kk:
        p = bs.value(k)
        Draft.makePoint(p)

def move_to_doc(objs, doc):
    objs = flatten(objs)
    out = []
    for o in objs:
        ocopy = doc.copyObject(o, True)
        #print("move_to_doc", o.Name, o.ViewObject.Visibility, ocopy.ViewObject.Visibility)
        out.append(ocopy)
    return out
        
def assert_bs(pts, knots, degree, mults, weights):
    # Check validity of spline
    assert len(pts) + degree + 1 == sum(mults)
    assert len(mults) == len(knots)
    assert mults[0] == degree + 1
    assert mults[-1] == degree + 1

def concat(c0, c1):
    # Concatenate (join, merge) two curves that meet (end point of c0 is first of c1)
    import numpy
    assert c0.Degree == c1.Degree
    pts = c0.getPoles() + c1.getPoles()[1:]
    def fix_k(c):
        k = numpy.array(c.getKnots())
        k += 0.0
        k -= k.min()
        if k.max() != 0:
            k /= k.max()
        return k

    k0 = fix_k(c0)
    k1 = fix_k(c1)

    k1 += 1
    k = numpy.concatenate([k0, k1[1:]])
    m = numpy.concatenate([c0.getMultiplicities()[:-1], [2], c1.getMultiplicities()[1:]])
    w = numpy.concatenate([c0.getWeights()[:-1], c1.getWeights()])

    return pts, m, k, c0.Degree, w

def sort(vec, dim):
    import numpy
    vv = numpy.ndarray((len(vec), 3))
    for i, vi in enumerate(vec):
        vv[i] = numpy.array([vi.x, vi.y, vi.z])
        #vv.append(numpy.array(vi.x, vi.y, vi.z))
    ii = numpy.argsort(vv[:,dim])
    vv = vv[ii]
    for i in range(0,len(vec)):
        vec[i] = FreeCAD.Vector(vv[i][0], vv[i][1], vv[i][2])
    return vec

def bbox2list(bbox):
    a = [bbox.XMin, bbox.YMin, bbox.ZMin, bbox.XMax, bbox.YMax, bbox.ZMax]
    return a

def list2bbox(l):
    a = FreeCAD.BoundBox(l[0],l[1],l[2],l[3],l[4],l[5])
    return a

def plotbbox(doc, bbox, name="bbox"):
    obj = box(doc,
              FreeCAD.Vector(bbox.XLength, bbox.YLength, bbox.ZLength),
              FreeCAD.Vector(bbox.XMin, bbox.YMin, bbox.ZMin),
              name)
    return obj
    

def max_pt(pt, vtx, dims):
    for d in dims:
        if vtx[d] > pt[d]:
            pt[d] = vtx[d]
    return pt

def min_pt(pt, vtx, dims):
    for d in dims:
        if vtx[d] < pt[d]:
            pt[d] = vtx[d]
    return pt

def find_close_pts(shape, dim, scalar, tol=1e-6):
    pts = []
    for e in shape.Edges:
        for v in e.Vertexes:
            #print(v.Point[dim],scalar,abs(v.Point[dim] - scalar))
            if abs(v.Point[dim] - scalar) < tol:
                pts.append(v)
    return pts

def macro_bbox(objs):
    if not isinstance(objs, list):
        objs = [objs]
    xmin = FreeCAD.Vector(9e99,9e99,9e99)
    xmax = -xmin
    for obj in objs:
        bbox = obj.Shape.BoundBox
        bbox_xmin = FreeCAD.Vector(bbox.XMin, bbox.YMin, bbox.ZMin)
        bbox_xmax = FreeCAD.Vector(bbox.XMax, bbox.YMax, bbox.ZMax)
        for d in range(0,3):
            if xmax[d] < bbox_xmax[d]:
                xmax[d] = bbox_xmax[d]
            if xmin[d] > bbox_xmin[d]:
                xmin[d] = bbox_xmin[d]
    # Macro bbox is (xmin,xmax,ymin,ymax,zmin,zmax)
    #macro_bbox = (xmin[0],xmax[0],xmin[1],xmax[1],xmin[2],xmax[2])
    macro_bbox = FreeCAD.BoundBox(xmin, xmax)
    return macro_bbox

def macro_bbox2bbox(i):
    o = FreeCAD.BoundBox(FreeCAD.Vector(i[0],i[2],i[4]),
                         FreeCAD.Vector(i[1],i[3],i[5]))
    return o

def printdims(info, bbox):
    print("dims " + info, bbox.XLength, bbox.YLength, bbox.ZLength)
def printbbox(info, bbox):
    return printdims(info, bbox)
    
def translate(objs, vec=None):
    if vec is None:
        # Translate such that lower left vertex of obj lies in origin. First
        # find the min point.
        vec = FreeCAD.Vector(-9e99, -9e99, 9e99)
        for obj in objs:
            shape = obj.Shape
            for e in shape.Edges:
                for v in e.Vertexes:
                    # Due to coordinate system
                    vx = max_pt(vec, v.Point, [0, 1])
                    vec[0] = vx[0]
                    vz = min_pt(vec, v.Point, [2])
                    vec[2] = vz[2]
                    
    # Translate
    import Draft
    objs2 = Draft.move(objs, -vec, copy=False)
    return objs2, vec
        
def mirror(doc, objs, normal, base):
    mirr = []
    for o in objs:
        obj = doc.addObject("Part::Mirroring", "mirror_" + o.Name)
        obj.Source = o
        obj.Normal = normal
        obj.Base = base
        mirr.append(obj)
    return mirr

def box(doc, dx, placement, name="box"):
    b = doc.addObject("Part::Box", name)
    b.Length = dx[0]
    b.Width = dx[1]
    b.Height = dx[2]
    b.Placement.Base = placement
    return b

def circle(doc, r, c, label):
    import Draft
    pl = FreeCAD.Placement()
    pl.Rotation.Q = (0.0,0.0,0.0,1.0)
    pl.Base = FreeCAD.Vector(c)
    c = Draft.makeCircle(radius=r, placement=pl, face=True)
    #c = Draft.autogroup(c)
    c.Label = label
    return c

def cylinder(doc, r, h, placement=FreeCAD.Vector(0,0,0), name="cylinder"):
    c = doc.addObject("Part::Cylinder",name)
    c.Radius = r
    c.Height = h
    pl = FreeCAD.Placement()
    pl.Rotation.Q = (0.0,0.0,0.0,1.0)
    pl.Base = placement
    c.Placement = pl
    return c
