import Rhino as rc
import Rhino.Geometry as rg
import rhinoscriptsyntax as rs
import scriptcontext as sc
import random
import System.Drawing as drawing
import util
import math

class _Vertex():
    def __init__(self, obj):
        self.obj = obj
        self.edges = []

    def GetNextEdge(self, baseEdge):
        smallestAngle = None
        smallestAngledEdge = None
        for edge in self.edges:
            if edge is baseEdge:
                continue

            b = self.obj
            if baseEdge.vertexAtEnd is self:
                a = baseEdge.vertexAtStart.obj
            else: a = baseEdge.vertexAtEnd.obj
            if edge.vertexAtEnd is self:
                c = edge.vertexAtStart.obj
            else: c = edge.vertexAtEnd.obj
            if rs.Distance(a, b) < sc.doc.ModelAbsoluteTolerance or rs.Distance(c, b) < sc.doc.ModelAbsoluteTolerance:
                continue
            try:
                angle = util.AngleABC(a,b,c)
            except:
                print "A: {}, B: {}, C: {}".format(a,b,c)
            ###
            if angle < smallestAngle or smallestAngle is None:
                smallestAngle = angle
                smallestAngledEdge = edge
        return smallestAngledEdge

class _Edge():
    def __init__(self, obj):
        self.obj = obj
        self.vertexAtStart = None
        self.vertexAtEnd = None
        self.CheckedForwards = False
        self.CheckedBackwards = False
        self.parameters = []
        self.vertices = []

    def sortParameters(self):
        self.vertices = [x for _,x in sorted(zip(self.parameters,self.vertices))]
        self.parameters = sorted(self.parameters)

class _Region():
    def __init__(self):
        self.vertices = []
        self.pline = None
        self.arrowSize = 1
        self.arrows = []
        self.attr = rc.DocObjects.ObjectAttributes()
        self.attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        self.attr.ObjectColor = drawing.Color.White
    
    def CreatePolyline(self):
        pts = []
        for v in self.vertices:
            pts.append(v.obj)
        self.pline = rg.Polyline(pts)
        self.pline = self.pline.ToPolylineCurve()
        
        arrowOffset = .5
        for i in range(len(self.vertices)-1):
            mdPt = (self.vertices[i].obj + self.vertices[i+1].obj) / 2
            vec = rs.VectorCreate(self.vertices[i+1].obj, self.vertices[i].obj)
            vec.Reverse()
            
            #Point
            vecPerp = vec.Clone()
            vecPerp = rg.Vector3d(vecPerp.Y, -vecPerp.X, 0)
            vecPerp.Unitize()
            vecPerp *= arrowOffset
            newMdPt = rg.Point3d.Add(mdPt, vecPerp)
            
            #Tail
            vec1 = vec.Clone()
            #vec1.Reverse()
            vec1.Unitize()
            vec1 *= self.arrowSize*2
            stPt = rg.Point3d.Add(mdPt, vec1+vecPerp)
            
            #End
            vec.Rotate(math.radians(135), rg.Vector3d(0,0,1))
            vec.Unitize()
            vec.Reverse()
            vec *= self.arrowSize
            endPt = rg.Point3d.Add(mdPt, vec+vecPerp)
            
            self.arrows.append(rg.LineCurve(newMdPt, endPt))
            self.arrows.append(rg.LineCurve(newMdPt, stPt))

class RegionDetection():
    """
    example:
    results = RegionDetection([lineCurves])
    results.Calculate()
    for eachRegion in results.regions:
        sc.doc.Objects.Add(eachRegion.pline, attr)
    """
    def __init__(self, lines):
        self.lines = lines
        self.regions = []
        self.pts = []
        self.edges = []
        self.plines = []
        
        self.OverKillEnabled = True
        
    def Calculate(self):
        segments = []
        edges = []
        vertices = []
        regions = []
        
        #0 Overkill lines
        if self.OverKillEnabled:
            lines = OverKill(self.lines)
        else:
            lines = self.lines
        
        #1 Setup segments
        for line in lines:
            segments.append(_Edge(line))
        
        #2 Get Intersection Pts
        for i in range(len(segments)):
            for j in range(i + 1, len(segments)):
                results = rg.Intersect.Intersection.CurveCurve(segments[i].obj, segments[j].obj, sc.doc.ModelAbsoluteTolerance, sc.doc.ModelAbsoluteTolerance)
                for result in results:
                    if result.IsPoint:
                        #Create vertices
                        v = _Vertex(result.PointA)
                        vertices.append(v)
                        
                        #Add params to each segment
                        segments[i].parameters.append(result.ParameterA)
                        segments[j].parameters.append(result.ParameterB)
                        segments[i].vertices.append(v)
                        segments[j].vertices.append(v)
                    elif result.IsOverlap:
                        #print "Overlap!"
                        #Create vertices
                        v0 = Vertex(segments[i].obj.PointAt(result.OverlapA.T0))
                        v1 = Vertex(segments[i].obj.PointAt(result.OverlapA.T1))
                        vertices.append(v0)
                        #vertices.append(v1)
                        
                        #Add params to each segment
                        segments[i].parameters.append(result.OverlapA.T0)
                        segments[j].parameters.append(result.OverlapB.T0)
                        segments[i].vertices.append(v0)
                        segments[j].vertices.append(v0)
        
        #3 Split the segments
        for segment in segments:
            segment.sortParameters()
            if len(segment.parameters) > 1:
                for i in range(len(segment.parameters)-1):
        
                    edges.append(_Edge(rg.LineCurve(segment.vertices[i].obj, segment.vertices[i+1].obj)))
                    edges[-1].vertexAtStart = segment.vertices[i]
                    edges[-1].vertexAtEnd = segment.vertices[i+1]
        
                    segment.vertices[i].edges.append(edges[-1])
                    segment.vertices[i+1].edges.append(edges[-1])
        
        #4 LOOP: Remove vertices with only one edge (not closed)
        hasDeadEnds = True
        while hasDeadEnds:
            hasDeadEnds = False
            for vertex in vertices:
                if len(vertex.edges) < 2:
                    vertices.remove(vertex)
                    if len(vertex.edges) > 0:
                        #Remove edge from other end's list of edges
                        if vertex.edges[0].vertexAtStart != vertex:
                            vertex.edges[0].vertexAtStart.edges.remove(vertex.edges[0])
                        else:
                            vertex.edges[0].vertexAtEnd.edges.remove(vertex.edges[0])
                        edges.remove(vertex.edges[0])
                    hasDeadEnds = True
                    break
        
        #5 Check if already done
        if len(edges) == 0:
            return None
        
        #6 Generate Regions: Follow smallest clockwise angle for each segment
        for edge in edges:
            self.edges.append(edge.obj)
            if edge.CheckedForwards == False:
                reg = _Region()
                edge.CheckedForwards = True
                startVertex = edge.vertexAtStart
                nextVertex = edge.vertexAtEnd
                reg.vertices.append(startVertex)
                reg.vertices.append(nextVertex)
                baseEdge = edge
                
            elif edge.CheckedBackwards == False:
                reg = _Region()
                edge.CheckedBackwards = True
                startVertex = edge.vertexAtEnd
                nextVertex = edge.vertexAtStart
                reg.vertices.append(startVertex)
                reg.vertices.append(nextVertex)
                baseEdge = edge
            else:
                continue
            
            
            safety = 0
            looping = True
            while looping:
                safety += 1
                if safety > 1000: print "loop safety"; break
                
                nextEdge = nextVertex.GetNextEdge(baseEdge)
                if nextEdge is None: break
                if nextEdge.vertexAtStart is nextVertex: #Nextedge in same direction
                    nextEdge.CheckedForwards = True
                    nextVertex = nextEdge.vertexAtEnd
                else:
                    nextEdge.CheckedBackwards = True
                    nextVertex = nextEdge.vertexAtStart
                
                reg.vertices.append(nextVertex)
                
                if nextVertex is startVertex: #if region completed
                    regions.append(reg)
                    looping = False
                    break
                else:
                    baseEdge = nextEdge
    
        #7 Remove nones from list
        #objs = []
        for region in regions:
            region.CreatePolyline()
        
        #DONE
        for vertex in vertices:
            self.pts.append(vertex.obj)
        self.regions = regions
        #self.plines = objs
    
def OverKill(objs):
    def MergeLines(overlapObjs):
        for i in range(len(overlapObjs)):
            for j in range(i + 1, len(overlapObjs)):
                line1 = overlapObjs[i]
                line2 = overlapObjs[j]
                results = rg.Intersect.Intersection.CurveCurve(line1, line2, sc.doc.ModelAbsoluteTolerance, sc.doc.ModelAbsoluteTolerance)
                for result in results:
                    if result.IsOverlap:
                        pts = [line1.PointAtStart, line1.PointAtEnd, line2.PointAtStart, line2.PointAtEnd]
                        min = None
                        max = None
                        stPt = None
                        endPt = None
                        if abs(pts[0].X - pts[1].X) < sc.doc.ModelAbsoluteTolerance:
                            for pt in pts:
                                if pt.Y < min or min is None:
                                    min = pt.Y
                                    stPt = pt
                                if pt.Y > max or max is None:
                                    max = pt.Y
                                    endPt = pt
                        else:
                            for pt in pts:
                                if pt.X < min or min is None:
                                    min = pt.X
                                    stPt = pt
                                if pt.X > max or max is None:
                                    max = pt.X
                                    endPt = pt
                        
                        newLine = rg.LineCurve(stPt, endPt)
                        
                        overlapObjs.remove(line1)
                        overlapObjs.remove(line2)
                        overlapObjs.append(newLine)
                        return True, overlapObjs
        return False, overlapObjs
    
    attr = rc.DocObjects.ObjectAttributes()
    attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
    attr.ObjectColor = drawing.Color.Red
    
    overlapObjs = []
    nonOverlapObjs = []
    newLines = []
    
    #Create list of overlapping objects
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            results = rg.Intersect.Intersection.CurveCurve(objs[i], objs[j], sc.doc.ModelAbsoluteTolerance, sc.doc.ModelAbsoluteTolerance)
            for result in results:
                if result.IsOverlap:
                    if objs[i] not in overlapObjs:
                        overlapObjs.append(objs[i])
                    if objs[j] not in overlapObjs:
                        overlapObjs.append(objs[j])
    
    #Create list of non overlapping lines
    for obj in objs:
        if obj not in overlapObjs:
            nonOverlapObjs.append(obj)
    
    #Go through and try to merge overlapping lines
    looping = True
    while looping:
        looping, overlapObjs = MergeLines(overlapObjs)
    
    return overlapObjs + nonOverlapObjs



if __name__ == "__main__":
    attr = rc.DocObjects.ObjectAttributes()
    attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
    attr.ObjectColor = drawing.Color.FromArgb(255, 50, 50, 50)
    lines = []
    for i in range(20):
        x1 = random.uniform(0, 100)
        y1 = random.uniform(0, 100)
        pt1 = rg.Point3d(x1, y1, 0)
        x2 = random.uniform(0, 100)
        y2 = random.uniform(0, 100)
        pt2 = rg.Point3d(x2, y2, 0)
        
        lines.append(rg.LineCurve(pt1, pt2))
        #sc.doc.Objects.AddCurve(lines[-1], attr)
    
    detector = RegionDetection(lines)
    detector.Calculate()
    attr.ObjectColor = drawing.Color.White
    
    for region in detector.regions:
        #sc.doc.Objects.AddCurve(region.pline, attr)
        for arrow in region.arrows:
            sc.doc.Objects.AddCurve(arrow, attr)
    
    for pt in detector.pts:
        sc.doc.Objects.AddPoint(pt, attr)
    
    attr.ObjectColor = drawing.Color.Red
    for edge in detector.edges:
        pt1 = edge.PointAtNormalizedLength(.1)
        pt2 = edge.PointAtNormalizedLength(.9)
        partEdge = rg.LineCurve(pt1, pt2)
        sc.doc.Objects.AddCurve(partEdge, attr)
    sc.doc.Views.Redraw()
