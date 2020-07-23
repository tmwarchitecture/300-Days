import Rhino as rc
import math
import random
import Rhino.Geometry as rg
import scriptcontext as sc
import rhinoscriptsyntax as rs
import util
from itertools import combinations
import clr; clr.AddReference("Grasshopper") 
import Grasshopper as gh


#Computational Geometry
def PoissonDiscSampling(r, width, height):
    """Generates points within the domains
    inputs:
        r - Minimum distance between samples
        width - highest x domain
        height - highest y domain
    returns:
        rc.Geometry.Point3d [list]
    """
    def get_cell_coords(pt):
        """Get the coordinates of the cell that pt = (x,y) falls in."""
        return int(pt[0] // a), int(pt[1] // a)
    
    def get_neighbours(coords):
        """Return the indexes of points in cells neighbouring cell at coords.
    
        For the cell at coords = (x,y), return the indexes of points in the cells
        with neighbouring coordinates illustrated below: ie those cells that could 
        contain points closer than r.
    
                                         ooo
                                        ooooo
                                        ooXoo
                                        ooooo
                                         ooo
    
        """
    
        dxdy = [(-1,-2),(0,-2),(1,-2),(-2,-1),(-1,-1),(0,-1),(1,-1),(2,-1),
                (-2,0),(-1,0),(1,0),(2,0),(-2,1),(-1,1),(0,1),(1,1),(2,1),
                (-1,2),(0,2),(1,2),(0,0)]
        neighbours = []
        for dx, dy in dxdy:
            neighbour_coords = coords[0] + dx, coords[1] + dy
            if not (0 <= neighbour_coords[0] < nx and
                    0 <= neighbour_coords[1] < ny):
                # We're off the grid: no neighbours here.
                continue
            neighbour_cell = cells[neighbour_coords]
            if neighbour_cell is not None:
                # This cell is occupied: store this index of the contained point.
                neighbours.append(neighbour_cell)
        return neighbours
    
    def point_valid(pt):
        """Is pt a valid point to emit as a sample?
    
        It must be no closer than r from any other point: check the cells in its
        immediate neighbourhood.
    
        """
    
        cell_coords = get_cell_coords(pt)
        for idx in get_neighbours(cell_coords):
            nearby_pt = samples[idx]
            # Squared distance between or candidate point, pt, and this nearby_pt.
            distance2 = (nearby_pt[0]-pt[0])**2 + (nearby_pt[1]-pt[1])**2
            if distance2 < r**2:
                # The points are too close, so pt is not a candidate.
                return False
        # All points tested: if we're here, pt is valid
        return True
    
    def get_point(k, refpt):
        """Try to find a candidate point relative to refpt to emit in the sample.
    
        We draw up to k points from the annulus of inner radius r, outer radius 2r
        around the reference point, refpt. If none of them are suitable (because
        they're too close to existing points in the sample), return False.
        Otherwise, return the pt.
    
        """
        i = 0
        while i < k:
            rho, theta = random.uniform(r, 2*r), random.uniform(0, 2*math.pi)
            pt = refpt[0] + rho*math.cos(theta), refpt[1] + rho*math.sin(theta)
            if not (0 <= pt[0] < width and 0 <= pt[1] < height):
                # This point falls outside the domain, so try again.
                continue
            if point_valid(pt):
                return pt
            i += 1
        # We failed to find a suitable point in the vicinity of refpt.
        return False    
    
    # Choose up to k points around each reference point as candidates for a new
    # sample point
    k = 30
    
    # Cell side length
    a = r/math.sqrt(2)
    # Number of cells in the x- and y-directions of the grid
    nx, ny = int(width / a) + 1, int(height / a) + 1
    
    # A list of coordinates in the grid of cells
    coords_list = [(ix, iy) for ix in range(nx) for iy in range(ny)]
    # Initilalize the dictionary of cells: each key is a cell's coordinates, the
    # corresponding value is the index of that cell's point's coordinates in the
    # samples list (or None if the cell is empty).
    cells = {coords: None for coords in coords_list}
    
    # Pick a random point to start with.
    pt = (random.uniform(0, width), random.uniform(0, height))
    samples = [pt]
    # Our first sample is indexed at 0 in the samples list...
    cells[get_cell_coords(pt)] = 0
    # ... and it is active, in the sense that we're going to look for more points
    # in its neighbourhood.
    active = [0]
    
    nsamples = 1
    # As long as there are points in the active list, keep trying to find samples.
    while active:
        # choose a random "reference" point from the active list.
        idx = random.choice(active)
        refpt = samples[idx]
        # Try to pick a new point relative to the reference point.
        pt = get_point(k, refpt)
        if pt:
            # Point pt is valid: add it to the samples list and mark it as active
            samples.append(pt)
            nsamples += 1
            active.append(len(samples)-1)
            cells[get_cell_coords(pt)] = len(samples) - 1
        else:
            # We had to give up looking for valid points near refpt, so remove it
            # from the list of "active" points.
            active.remove(idx)
    rcPts = []
    for sample in samples:
        rcPts.append(rc.Geometry.Point3d(sample[0], sample[1], 0))
    return rcPts

class AStar():
    """
    Setup the list of nodes using __init__ then call AStarPathFinder(start, end) to return a path of nodes.
    
    example:
    searchNetwork = AStar(srfs)
    start = searchNetwork.GetNodeClosestToPt(rg.Point3d(0,0,0))
    end = searchNetwork.GetNodeClosestToPt(rg.Point3d(50,50,0))
    result, path = searchNetwork.AStarPathFinder(start, end)
    """
    def __init__(self, srfs):
        """
        parameter:
            srfs [list]: triangular srfs, not joined
        """
        self.nodes = []
        self.start = None
        self.end = None
        
        #Create Nodes
        for srf in srfs:
            srfPts = srf.Brep.Vertices
            thisSrfNodes = []
            for srfPt in srfPts:
                pt = rg.Point3d(srfPt.Location.X, srfPt.Location.Y, 0)
                node0 = None
                for node in self.nodes:
                    if node.pos == pt:
                        node0 = node
                        break
                if node0 is None:
                    node0 = self.Node(pt)
                thisSrfNodes.append(node0)
            
            #Setup node neighbors
            for thisSrfNode in thisSrfNodes:
                for otherNode in thisSrfNodes:
                    if thisSrfNode is otherNode: continue
                    if otherNode not in thisSrfNode.neighbors:
                        thisSrfNode.neighbors.append(otherNode)
                if thisSrfNode not in self.nodes:
                    self.nodes.append(thisSrfNode)
    
    def GetNodeClosestToPt(self, pt):
        """
        parameters:
            pt (point): point to find node closest to
        returns:
            node: node closest to pt
        """
        closestDist = None
        closestNode = None
        for node in self.nodes:
            d = rs.Distance(pt, node.pos)
            if d < closestDist or closestDist is None:
                closestDist = d
                closestNode = node
        return closestNode
    
    def AStarPathFinder(self, start, end):
        """
        paramters:
            start (node):
            end (node):
        returns:
            Bool (success or failure)
            list (nodes visited) (use the .pos to get the rhino point)
        """
        openSet = [start]
        closedSet = []
        path = []
        searching = True
        while searching:
            if sc.escape_test(True): return
            if len(openSet) > 0:
                
                #Choose tile with lowest f score
                lowestTile = openSet[0]
                for tile in openSet:
                    if tile is lowestTile: continue
                    if tile.f < lowestTile.f or lowestTile is None:
                        lowestTile = tile
                current = lowestTile
                
                path = []
                temp = current
                path.append(temp)
                while temp.previous:
                    path.append(temp.previous)
                    temp = temp.previous
                
                #Check if at the end
                if current is end: 
                    searching = False
                    break
                
                #Move current tile from open to closed set
                openSet.remove(current)
                closedSet.append(current)
                
                #Check all the neighbors
                for neighbor in current.neighbors:
                    #if neighbor.type == 0: continue #Use this if nodes are blocked
                    if neighbor not in closedSet:
                        tempG = current.g + rs.Distance(current.pos, neighbor.pos)
                        
                        #Is this a better path?
                        if neighbor not in openSet:
                            openSet.append(neighbor)
                        elif tempG >= neighbor.g:
                            #It is not a better path
                            continue
                        
                        neighbor.previous = current
                        neighbor.g = tempG
                        neighbor.h = rs.Distance(current.pos, end.pos)
                        neighbor.f = neighbor.g + neighbor.h
            else:
                #print "No Solution"
                return False, None
        return True, path
    
    class Node():
        def __init__(self, pt):
            self.pos = pt
            self.neighbors = []
            self.previous = None
            self.f = 0
            self.g = 0
            self.h = 0
            self.type = None
            
class AStarMesh():
    """
    Setup the list of nodes using __init__ then call AStarPathFinder(start, end) to return a path of nodes.
    
    example:
        searchNetwork = geo.AStarMesh(mesh, sourceIndex, targetIndex)
        result, path = searchNetwork.AStarPathFinder() 
    """
    def __init__(self, mesh, start, end):
        """
        parameter:
            srfs [list]: triangular srfs, not joined
        """
        self.nodes = []
        
        for i, v in enumerate(mesh.Vertices):
            self.nodes.append(self.Node(v))
        for i, v in enumerate(mesh.Vertices):
            indices = mesh.Vertices.GetConnectedVertices(i)
            for index in indices:
                self.nodes[i].neighbors.append(self.nodes[index])
        
        self.start = self.nodes[start]
        self.end = self.nodes[end]
        
        if False:
            #Create Nodes
            for srf in srfs:
                srfPts = srf.Brep.Vertices
                thisSrfNodes = []
                for srfPt in srfPts:
                    pt = rg.Point3d(srfPt.Location.X, srfPt.Location.Y, 0)
                    node0 = None
                    for node in self.nodes:
                        if node.pos == pt:
                            node0 = node
                            break
                    if node0 is None:
                        node0 = self.Node(pt)
                    thisSrfNodes.append(node0)
                
                #Setup node neighbors
                for thisSrfNode in thisSrfNodes:
                    for otherNode in thisSrfNodes:
                        if thisSrfNode is otherNode: continue
                        if otherNode not in thisSrfNode.neighbors:
                            thisSrfNode.neighbors.append(otherNode)
                    if thisSrfNode not in self.nodes:
                        self.nodes.append(thisSrfNode)
    
    def GetNodeClosestToPt(self, pt):
        """
        parameters:
            pt (point): point to find node closest to
        returns:
            node: node closest to pt
        """
        closestDist = None
        closestNode = None
        for node in self.nodes:
            d = rs.Distance(pt, node.pos)
            if d < closestDist or closestDist is None:
                closestDist = d
                closestNode = node
        return closestNode
    
    def AStarPathFinder(self):
        """
        paramters:
            start (node):
            end (node):
        returns:
            Bool (success or failure)
            list (nodes visited) (use the .pos to get the rhino point)
        """
        openSet = [self.start]
        closedSet = []
        path = []
        searching = True
        while searching:
            if sc.escape_test(True): return
            if len(openSet) > 0:
                
                #Choose tile with lowest f score
                lowestTile = openSet[0]
                for tile in openSet:
                    if tile is lowestTile: continue
                    if tile.f < lowestTile.f or lowestTile is None:
                        lowestTile = tile
                current = lowestTile
                
                path = []
                temp = current
                path.append(temp)
                while temp.previous:
                    path.append(temp.previous)
                    temp = temp.previous
                
                #Check if at the end
                if current is self.end: 
                    searching = False
                    break
                
                #Move current tile from open to closed set
                openSet.remove(current)
                closedSet.append(current)
                
                #Check all the neighbors
                for neighbor in current.neighbors:
                    #if neighbor.type == 0: continue #Use this if nodes are blocked
                    if neighbor not in closedSet:
                        tempG = current.g + rs.Distance(current.pos, neighbor.pos)
                        
                        #Is this a better path?
                        if neighbor not in openSet:
                            openSet.append(neighbor)
                        elif tempG >= neighbor.g:
                            #It is not a better path
                            continue
                        
                        neighbor.previous = current
                        neighbor.g = tempG
                        neighbor.h = rs.Distance(current.pos, self.end.pos)
                        neighbor.f = neighbor.g + neighbor.h
            else:
                #print "No Solution"
                return False, None
        return True, path
    
    class Node():
        def __init__(self, pt):
            self.pos = rg.Point3d(pt)
            self.neighbors = []
            self.previous = None
            self.f = 0
            self.g = 0
            self.h = 0
            self.type = None
            
            
def Delaunay2d(pts):
    """
    Delaunay Triangulation
    parameters:
        pts [list]
    return:
        PolylineCurve [list]: in counter-clockwise orientation
    """
    triangles = []
    set = list(combinations(pts,3))
    for tuple in set:
        c1 = tuple[0]
        c2 = tuple[1]
        c3 = tuple[2]
        if (c1[0]-c2[0])*(c3[1]-c2[1])-(c1[1]-c2[1])*(c3[0]-c2[0]) != 0:
            circle = rg.Circle(c1,c2,c3)
            center = circle.Center
            circle = circle.ToNurbsCurve()
            delaunay = 0
            for point in pts:
                if circle.Contains(point) == rg.PointContainment.Inside:
                    delaunay = 1
                    continue
            if delaunay == 0:
                crv = rg.PolylineCurve([c1,c2,c3,c1])
                if crv.ClosedCurveOrientation() == rg.CurveOrientation.Clockwise:
                    crv.Reverse()
                triangles.append(crv)
    return triangles

def Delaunay2dPts(pts):
    """
    Delaunay Triangulation
    parameters:
        pts [list]
    return:
        Pts [list]: in counter-clockwise orientation
    """
    triangles = []
    set = list(combinations(pts,3))
    for tuple in set:
        c1 = tuple[0]
        c2 = tuple[1]
        c3 = tuple[2]
        if (c1[0]-c2[0])*(c3[1]-c2[1])-(c1[1]-c2[1])*(c3[0]-c2[0]) != 0:
            circle = rg.Circle(c1,c2,c3)
            circle = circle.ToNurbsCurve()
            delaunay = 0
            for point in pts:
                if circle.Contains(point) == rg.PointContainment.Inside:
                    delaunay = 1
                    continue
            if delaunay == 0:
                if False:
                    c1t = circle.ClosestPoint(c1)[1]
                    c2t = circle.ClosestPoint(c2)[1]
                    c3t = circle.ClosestPoint(c3)[1]
                    group = [[c1t, c1], [c2t, c2], [c3t, c3]]
                    group.sort()
                    triangles.append([group[0][1],group[1][1],group[2][1]])
                triangles.append([c1, c2, c3])
    return triangles

def DelaunayMesh(pts, plane):
    """
    Delaunay Triangulation to a mesh
    parameters:
        pts [list]
        plane: Plane to project to
    return:
        Mesh
    """
    mesh = rg.Mesh()
    ptsList = rc.Collections.Point3dList(pts)
    
    #Transform to worldXY
    xform = rg.Transform.PlaneToPlane(plane, rg.Plane.WorldXY)
    ptsList.Transform(xform)
    
    #Add pts to mesh
    for pt in ptsList:
        mesh.Vertices.Add(pt)
    
    #Project to plane
    ptsList.SetAllZ(0)
    
    #Find delaunay
    allPts = Delaunay2dPts(ptsList)
    
    #Return to correct Z
    returnToZPts = []
    for tri in allPts:
        mesh.Faces.AddFace(ptsList.ClosestIndex(tri[0]), ptsList.ClosestIndex(tri[1]), ptsList.ClosestIndex(tri[2]))
    
    #Return to original space
    returnXform = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, plane)
    mesh.Transform(returnXform)
    
    mesh.UnifyNormals()
    mesh.RebuildNormals()
    
    return mesh

def Voronoi2D(pts, bbCorners = None):
    """
    Calculates 2d voronoi using Grasshopper code
    parameters:
        pts (rg.Point3d)[list]
        bbCorners (rg.Point3d)[list]: 4 points for boundary
    returns:
        rg.PolylineCurve [list]: Closed region
    """
    if bbCorners is None:
        # Create a boundingbox and get its corners
        bb = rc.Geometry.BoundingBox(pts)
        d = bb.Diagonal
        dl = d.Length
        f = dl/15
        bb.Inflate(f,f,f)
        bbCorners = bb.GetCorners()
    
    # Create a list of outline nodes using the BB
    outline = gh.Kernel.Geometry.Node2List()
    for p in bbCorners:
        n = gh.Kernel.Geometry.Node2(p.X,p.Y)
        outline.Append(n)
    
    # Create a list of nodes
    nodes = gh.Kernel.Geometry.Node2List()
    for p in pts:
        n = gh.Kernel.Geometry.Node2(p.X,p.Y)
        nodes.Append(n)
    
    # Calculate the delaunay triangulation
    delaunay = gh.Kernel.Geometry.Delaunay.Solver.Solve_Connectivity(nodes,0.1,False)
    
    # Calculate the voronoi diagram
    voronoi = gh.Kernel.Geometry.Voronoi.Solver.Solve_Connectivity(nodes,delaunay,outline)
    
    # Get polylines from the voronoi cells and return them to GH
    polylines = []
    for c in voronoi:
        pl = c.ToPolyline()
        polylines.append(pl.ToPolylineCurve())
    return polylines


class ConvexHull(): 
    """
    Code modified from https://startupnextdoor.com/computing-convex-hull-in-python/
    
    initialize then use get_hull_points or get_polyline
    
    paramters:
        allPts (pts [point]): list of pts
    """
    def __init__(self, allPts):
        self._hull_points = []
        self._points = allPts
        self.compute_hull()

    def _get_orientation(self, origin, p1, p2):
        '''
        Returns the orientation of the Point p1 with regards to Point p2 using origin.
        Negative if p1 is clockwise of p2.
        :param p1:
        :param p2:
        :return: integer
        '''
        difference = (
            ((p2.X - origin.X) * (p1.Y - origin.Y))
            - ((p1.X - origin.X) * (p2.Y - origin.Y))
        )

        return difference

    def compute_hull(self):
        '''
        Computes the points that make up the convex hull.
        :return:
        '''
        points = self._points

        # get leftmost point
        start = points[0]
        min_x = start.X
        for p in points[1:]:
            if p.X < min_x:
                min_x = p.X
                start = p

        point = start
        self._hull_points.append(start)

        far_point = None
        while far_point is not start:

            # get the first point (initial max) to use to compare with others
            p1 = None
            for p in points:
                if p is point:
                    continue
                else:
                    p1 = p
                    break

            far_point = p1

            for p2 in points:
                # ensure we aren't comparing to self or pivot point
                if p2 is point or p2 is p1:
                    continue
                else:
                    direction = self._get_orientation(point, far_point, p2)
                    if direction > 0:
                        far_point = p2

            self._hull_points.append(far_point)
            point = far_point

    def get_hull_points(self):
        """
        returns:
             pts [list]
        """
        if self._points and not self._hull_points:
            self.compute_hull()
        
        return self._hull_points

    def get_polyline(self):
        """
        returns:
            polyline
        """
        return rc.Geometry.Polyline(self._hull_points)

def minBoundingBox(crv):
    """Returns the minimal 2d bounding box of a curve or surface.
    Parameters:
      crv (curve) = planar curve or surface
    Returns:
      polylineCurve = min polyline based on area
    """
    #Get control points
    P = rs.CurveEditPoints(crv)
    p = []
    for i in range(0, len(P)-1):
        p.append(P[i])
    
    #get The convex hull
    hull = ConvexHull(p)
    convexHull = hull.get_polyline()
    
    minArea = None
    minBoundary = None
    
    plane = crv.TryGetPlane()[1]
    normal = plane.Normal
    
    
    #For each edge
    for i in range(convexHull.SegmentCount):
        edge = convexHull.SegmentAt(i)
        segVec = edge.PointAt(0) - edge.PointAt(1)
        yVec = rs.VectorCrossProduct(normal, segVec)
        plane = rg.Plane(rs.coerce3dpoint((0,0,0)), segVec, yVec)
        bbPts = rs.BoundingBox(crv, view_or_plane = plane)
        newPts = bbPts[:4]
        newPts.append(bbPts[0])
        
        pline = rg.PolylineCurve(newPts)
        am = rg.AreaMassProperties.Compute(pline)
        
        area = am.Area
        if area < minArea or minArea is None:
            minArea = area
            minBoundary = pline
    return minBoundary

#Pts
def MidPoint(pt1, pt2):
    """
    pointBetweenPoints(pt1, pt2)
    input:
        pt1 = rc point
        pt2 = rc point
    return:
        new rc point
    """
    x = util.Remap(.5, 0, 1, min(pt1.X, pt2.X), max(pt1.X, pt2.X))
    y = util.Remap(.5, 0, 1, min(pt1.Y, pt2.Y), max(pt1.Y, pt2.Y))
    z = util.Remap(.5, 0, 1, min(pt1.Z, pt2.Z), max(pt1.Z, pt2.Z))
    return rc.Geometry.Point3d(x,y,z)

def PointBetweenPoints(pt1, pt2, t = .5):
    """
    pointBetweenPoints(pt1, pt2, t = .5)
    input:
        pt1 = rc point
        pt2 = rc point
        t = normalized pt between pt1 and pt2
    return:
        new rc point
    """
    line = rg.Line(pt1, pt2)
    return line.PointAt(t)

def RandomPoint(x0 = 0, x1 = 100, y0 = 0, y1 = 100, z0 = 0, z1 = 100):
    """Randomly creates point between x0->x1, y0->y1, and z0->z1domains
    
    """
    return rg.Point3d(random.uniform(x0,x1), random.uniform(y0,y1),random.uniform(z0,z1))

def RemoveDuplicatePts(points):
    # Create a dictionary to keep track of the Id
    pointDict = {}
    ptList = []
    for pt in points:
        pt3d = rs.coerce3dpoint(pt)
        pointDict[pt3d] = pt
        ptList.append(pt3d)
    
    #sortList
    ptList.sort()
    ptLast = ptList[-1]
    
    tol = sc.doc.ModelAbsoluteTolerance
    
    for i in range(len(ptList)-2,-1,-1):
        if (abs(ptList[i][0]-ptLast[0]) < tol) and (abs(ptList[i][1]-ptLast[1])) < tol and (abs(ptList[i][2]-ptLast[2]) < tol):
            del ptList[i]
        else:
            ptLast = ptList[i]
    
    #find the the ids with the new list
    outputList = []
    for pt in ptList:
        ptId = pointDict[pt]
        outputList.append(ptId)
    
    return outputList

def CentroidOfPoints(pts):
    centerPt = rg.Point3d(0,0,0)
    for pt in pts:
        centerPt += pt
    return centerPt/len(pts)


#Vectors
def VectorDisplay(point, vector, accel):
    endPt = rc.Geometry.Point3d.Add(point, vector)
    accelEndPt = rc.Geometry.Point3d.Add(endPt, accel)
    line1 = rc.Geometry.Line(point, endPt)
    line2 = rc.Geometry.Line(endPt, accelEndPt)
    return sc.doc.Objects.AddLine(line1), sc.doc.Objects.AddLine(line2)

def DotProduct(a, b):
    return a.X*b.X + a.Y*b.Y + a.Z*b.Z

def VectorAngle(a, b):
    return math.acos(dotProduct(a,b) / (a.Length*b.Length))

def VectorLimit(vector, t):
    if vector.Length >= t:
        vector.Unitize()
        vector *= t
    return vector

def RandomVector(size = 1):
    """Random 2d vector
    parameters:
        size(float)[optional]: length of return vector
    returns:
        Vector3d
    """
    vec = rg.Vector3d(random.uniform(-1, 1), random.uniform(-1, 1), 0)
    vec.Unitize()
    vec *= size
    return vec

def RandomVector3d(amp = None):
    """
    returns random unitized vector
    if amp: returns vector of length amp
    """
    vec = rg.Vector3d(random.uniform(-1,1), random.uniform(-1, 1), random.uniform(-1,1))
    vec.Unitize()
    if amp:vec *= amp
    return vec

def GetCornerVecs(pts, leftHanded = False, amplitude = 1):
    """
    Returns the corner vector 
    parameters:
        pts (Point3d)[list]: list of verticies
        leftHanded (bool, optional): if True, will get left hand side vecs
        amplitude (float, optional): amplitude of the returned vecs
    returns:
        Vector3d [list]
    """
    def GetCornerVec(pt0, pt1, pt2):
        ang = util.AngleABC(pt0, pt1, pt2)
        
        vec0 = pt0-pt1
        vec1 = pt2-pt1
        vec0.Unitize()
        vec1.Unitize()
        cornerVec = (vec0 + vec1)/2
        cornerVec.Unitize()
        if ang < 180:
            cornerVec.Reverse()
        return cornerVec 
    
    cornerVecs = []
    for i in range(len(pts)):
        vec = GetCornerVec(pts[(i-1)%len(pts)], pts[(i)%len(pts)], pts[(i+1)%len(pts)])
        vec *= amplitude
        if leftHanded:
            vec.Reverse()
        cornerVecs.append(vec)
    return cornerVecs

#Curves
def SplitSelfIntersection(crv, safety = 0):
    """Splits curves into clockwise and counterclockwise loops at self intersection.
    parameters:
        crv: Closed planar curve
    returns:
        cw loops [list]
        cc loops [list]
    """
    safety += 1
    cwLoops = []
    ccLoops = []
    
    #Reparamterize
    newDomain = rg.Interval(0,1)
    crv.Domain = newDomain
    
    #Check for self intersection
    events = rg.Intersect.Intersection.CurveSelf(crv, sc.doc.ModelAbsoluteTolerance)
    #print "{} intersections".format(len(events))
    
    #Collect intersection parameters
    parameters = [0]
    if len(events) > 0:
        for event in events:
            parameters.append(event.ParameterA)
            parameters.append(event.ParameterB)
    else:
        if crv.ClosedCurveOrientation() == rg.CurveOrientation.CounterClockwise:
            ccLoops = [crv]
        else:
            cwLoops = [crv]
        return cwLoops, ccLoops
    parameters.append(1)
    parameters.sort()
    
    #Split into segments
    segments = []
    for i in range(len(parameters)-1):
        segments.append(crv.Trim(parameters[i], parameters[i+1]))
    
    #If segments are closed themselves, add to loop list
    segmentsToRemove = []
    for segment in segments:
        if segment.IsClosed:
            if segment.ClosedCurveOrientation() == rg.CurveOrientation.CounterClockwise:
                ccLoops.append(segment)
            else:
                cwLoops.append(segment)
            segmentsToRemove.append(segment)
    for segment in segmentsToRemove:
        segments.remove(segment)
    
    #Join segments to make new loops
    newCrv = rg.PolyCurve()
    for segment in segments:
        newCrv.Append(segment)
    
    events = rg.Intersect.Intersection.CurveSelf(newCrv, sc.doc.ModelAbsoluteTolerance)
    if len(events) > 0 and safety < 10:
        #Enter recursion
        cwResults, ccResults = SplitSelfIntersection(newCrv, safety)
        for result in ccResults:
            ccLoops.append(result)
        for result in cwResults:
            cwLoops.append(result)
    else:
        if newCrv.ClosedCurveOrientation() == rg.CurveOrientation.CounterClockwise:
            ccLoops.append(newCrv)
        else:
            cwLoops.append(newCrv)
    
    return cwLoops, ccLoops

def CustomOffset(crv, iter_d, rd):
    """
    parameters:
        crv: Rhino curve
        inter_d (float): offset distance
        rd: rebuild distance
    returns:
        crv [list]: curves in same orientation as input crv
    """
    n = int(crv.GetLength() / rd)
    if n < 3:
        n = 3
    crv = crv.Rebuild(n, 3, True)
    params = crv.DivideByCount(n, False)
    newPts = []
    for param in params:
        pt = crv.PointAt(param)
        tan = crv.TangentAt(param)
        tan.Rotate(math.radians(90), rg.Vector3d(0,0,1))
        tan.Unitize()
        tan *= iter_d
        newPt = rg.Point3d.Add(pt, tan)
        newPts.append(newPt)
    newCrv = rg.NurbsCurve.Create(True, 3, newPts)
    
    cwCrvs, ccCrvs = SplitSelfIntersection(newCrv)
    
    if crv.ClosedCurveOrientation() == rg.CurveOrientation.Clockwise:
        return cwCrvs
    else:
        return ccCrvs

#Geometry
def Cone(pt, vec, range, radius):
    """arcPtVecInt(pt, vec, range)
    input:
        pt: center point of arc
        vec:(vector) direction of arc 
        range:(float in degrees) Vision cone, aligned to vector 
        radius: (float) radius
    return:
        rc arc
    """
    perpVec = rc.Geometry.Vector3d(-vec.Y, vec.X, 0)
    plane = rc.Geometry.Plane(pt, vec, perpVec)
    plane.Rotate(math.pi, plane.Normal)
    circle = rc.Geometry.Circle(plane, radius)
    interval = rc.Geometry.Interval(math.pi+math.radians(range/2), math.pi-math.radians(range/2))
    arc = rc.Geometry.Arc(circle, interval)
    line1 = rc.Geometry.LineCurve(pt, arc.StartPoint)
    line2 = rc.Geometry.LineCurve(arc.EndPoint, pt)
    polycurve = rc.Geometry.PolyCurve()
    polycurve.Append(arc)
    polycurve.Append(line2)
    polycurve.Append(line1)
    return polycurve

def LineCurveLineCurveDistance(line1, line2):
    """
    paremeters:
        crv1 (LineCurve):
        crv2 (LineCurve):
    returns:
        float: distance between two curves
        LineCurve: line between two closestPoints (if curves touching, returns True)
    """
    result = rg.Intersect.Intersection.CurveCurve(crv1, crv2, sc.doc.ModelAbsoluteTolerance, sc.doc.ModelAbsoluteTolerance)
    if result.Count > 0:
        d = 0
        line = result[0]
    else:
        crv1Pts = [crv1.PointAtStart, crv1.PointAtEnd]
        crv2Pts = [crv2.PointAtStart, crv2.PointAtEnd]
        
        closestDist = None
        closestCrv1Pt = None
        closestCrv2Pt = None
        for crv1Pt in crv1Pts:
            closestParamOnCrv2 = crv2.ClosestPoint(crv1Pt, 0)
            closestPtOnCrv2 = crv2.PointAt(closestParamOnCrv2[1])
            dist = rs.Distance(crv1Pt, closestPtOnCrv2)
            if dist < closestDist or closestDist is None:
                closestDist = dist
                closestCrv1Pt = crv1Pt
                closestCrv2Pt = closestPtOnCrv2
        for crv2Pt in crv2Pts:
            closestParamOnCrv1 = crv1.ClosestPoint(crv2Pt, 0)
            closestPtOnCrv1 = crv1.PointAt(closestParamOnCrv1[1])
            dist = rs.Distance(crv2Pt, closestPtOnCrv1)
            if dist < closestDist or closestDist is None:
                closestDist = dist
                closestCrv1Pt = closestPtOnCrv1
                closestCrv2Pt = crv2Pt
        d = closestDist
        line = rg.LineCurve(closestCrv1Pt, closestCrv2Pt)
    return d, line

def IsCurveInsideCurve(plineCrv, testCrv):
    """IsCurveInsideCurve(plineCrv, testCrv)
    parameters:
        plineCrv (curve): closed polylineCurve
        testCrv (curve): curve to test if inside plineCrv
    returns:
        0 - Outside
        1 - Intersecting
        2 - Inside
    """
    result = rg.Intersect.Intersection.CurveCurve(plineCrv, testCrv, sc.doc.ModelAbsoluteTolerance, sc.doc.ModelAbsoluteTolerance)
    if len(result)>0:
        return 1
    if plineCrv.Contains(testCrv.PointAtStart) ==  rg.PointContainment.Inside or plineCrv.Contains(testCrv.PointAtEnd) ==  rg.PointContainment.Inside:
        return 2
    return 0

def main():
    obj = rs.GetObject("Select Objects", preselect = True)
    obj = rs.coercecurve(obj)
    
    cw, cc = SplitSelfIntersection(obj)
    
    #bbox = minBoundingBox(obj)
    for crv in cw:
        sc.doc.Objects.AddCurve(crv)
    for crv in cc:
        sc.doc.Objects.AddCurve(crv)

#Classes
class Particle():
    def __init__(self, pos = rg.Point3d(0,0,0), vel = rg.Vector3d(0,0,0)):
        self.pos = pos
        self.vel = vel
        self.acc = rg.Vector3d(0,0,0)
        self.id = None
        self.radius = 0
    
    def Update(self):
        futurePos = rg.Point3d.Add(self.pos, self.vel)
        if futurePos.X < self.radius:
            self.vel.X *= -1
        if futurePos.Y < self.radius:
            self.vel.Y *= -1
        if futurePos.Z < self.radius:
            self.vel.Z *= -1
        if futurePos.X > 100-self.radius:
            self.vel.X *= -1
        if futurePos.Y > 100-self.radius:
            self.vel.Y *= -1
        if futurePos.Z > 100-self.radius:
            self.vel.Z *= -1
        
        self.vel += self.acc
        self.pos += self.vel
    
    def UpdateDisplay(self):
        if self.id:sc.doc.Objects.Delete(self.id, True)
        self.id = sc.doc.Objects.AddPoint(self.pos)

if __name__ == "__main__":
    pts = []
    
    for i in range(10):
        pts.append(RandomPoint())
    
    mesh = DelaunayMesh(pts, rg.Plane.WorldXY)
    sc.doc.Objects.AddMesh(mesh)