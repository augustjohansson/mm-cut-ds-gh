// ============================================================================
// dolfin::IntersectionConstruction -- high-level vector<Point> dispatch
// ============================================================================

std::vector<dolfin::Point>
dolfin::IntersectionConstruction::intersection(const std::vector<dolfin::Point>& p,
                                                const std::vector<dolfin::Point>& q,
                                                std::size_t gdim)
{
  const std::size_t d0 = p.size() - 1;
  const std::size_t d1 = q.size() - 1;

  // Use symmetry: ensure d0 <= d1 to reduce the number of cases
  if (d0 > d1)
    return intersection(q, p, gdim);

  if (gdim == 1)
  {
    std::vector<double> r;
    if (d0 == 0 && d1 == 0)
      r = intersection_point_point_1d(p[0].x(), q[0].x());
    else if (d0 == 0 && d1 == 1)
      r = intersection_segment_point_1d(q[0].x(), q[1].x(), p[0].x());
    else if (d0 == 1 && d1 == 1)
      r = intersection_segment_segment_1d(p[0].x(), p[1].x(), q[0].x(), q[1].x());
    else
      dolfin_error("IntersectionConstruction.cpp",
                   "compute intersection",
                   "Unknown entity dimensions %zu and %zu for gdim 1", d0, d1);
    std::vector<Point> result;
    for (double x : r)
      result.emplace_back(x);
    return result;
  }
  else if (gdim == 2)
  {
    if (d0 == 0 && d1 == 0)
      return intersection_point_point_2d(p[0], q[0]);
    if (d0 == 0 && d1 == 1)
      return intersection_segment_point_2d(q[0], q[1], p[0]);
    if (d0 == 0 && d1 == 2)
      return intersection_triangle_point_2d(q[0], q[1], q[2], p[0]);
    if (d0 == 1 && d1 == 1)
      return intersection_segment_segment_2d(p[0], p[1], q[0], q[1]);
    if (d0 == 1 && d1 == 2)
      return intersection_triangle_segment_2d(q[0], q[1], q[2], p[0], p[1]);
    if (d0 == 2 && d1 == 2)
      return intersection_triangle_triangle_2d(p[0], p[1], p[2], q[0], q[1], q[2]);
  }
  else if (gdim == 3)
  {
    if (d0 == 0 && d1 == 0)
      return intersection_point_point_3d(p[0], q[0]);
    if (d0 == 0 && d1 == 1)
      return intersection_segment_point_3d(q[0], q[1], p[0]);
    if (d0 == 0 && d1 == 2)
      return intersection_triangle_point_3d(q[0], q[1], q[2], p[0]);
    if (d0 == 0 && d1 == 3)
      return intersection_tetrahedron_point_3d(q[0], q[1], q[2], q[3], p[0]);
    if (d0 == 1 && d1 == 2)
      return intersection_triangle_segment_3d(q[0], q[1], q[2], p[0], p[1]);
    if (d0 == 1 && d1 == 3)
      return intersection_tetrahedron_segment_3d(q[0], q[1], q[2], q[3], p[0], p[1]);
    if (d0 == 2 && d1 == 2)
      return intersection_triangle_triangle_3d(p[0], p[1], p[2], q[0], q[1], q[2]);
    if (d0 == 2 && d1 == 3)
      return intersection_tetrahedron_triangle_3d(q[0], q[1], q[2], q[3], p[0], p[1], p[2]);
    if (d0 == 3 && d1 == 3)
      return intersection_tetrahedron_tetrahedron_3d(p[0], p[1], p[2], p[3],
                                                     q[0], q[1], q[2], q[3]);
  }

  dolfin_error("IntersectionConstruction.cpp",
               "compute intersection",
               "Not implemented for topological dimensions %zu and %zu with geometric dimension %zu",
               d0, d1, gdim);
  return {};
}
