"""300 Days of Code
Sketches 201-300 by Tim Williams
"""
import Rhino as rc
import Rhino.Geometry as rg
import rhinoscriptsyntax as rs
import scriptcontext as sc
import math
import random
import os
import System.Drawing as drawing
import time
import datetime
import clr; clr.AddReference("Grasshopper") 
import Grasshopper as gh
from itertools import combinations as cb
import itertools

import lib.color as color
import lib.mp4 as mp4
import lib.geometry as geo
import lib.util as util
import lib.perlin as perlin
import lib.region as region


class TempDisplay():
    def __init__(self, objs = [], color = drawing.Color.Gold):
        self.attr = rc.DocObjects.ObjectAttributes()
        self.attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        self.attr.ObjectColor = color
        
        self.Enabled = True
        self.guids = []
        if type(objs) != list:
            objs = [objs]
        self.Add(objs, color)
    
    def Add(self, objs, color = None):
        if self.Enabled == False: return
        oldColor = self.attr.ObjectColor
        if type(objs) != list:
            objs = [objs]
        for obj in objs:
            if type(obj) == rg.Point3d:
                self.guids.append(sc.doc.Objects.AddPoint(obj, self.attr))
            elif type(obj) == rg.LineCurve or type(obj) == rg.PolylineCurve:
                self.guids.append(sc.doc.Objects.AddCurve(obj, self.attr))
            else:
                print "Cannot add temp obj, type not supported"
        
    def Cleanup(self):
        for id in self.guids:
            sc.doc.Objects.Delete(id, True)

class Scene():
    def __init__(self):
        self.floorID = r'ec68de3f-0f6f-4c67-95e9-cb86d8a13d7e'
        self.floor = rs.coercesurface(self.floorID)

class HUD():
    def __init__(self, skNum, numFrames):
        self.numFrames = numFrames
        self.skNumID = r'9307b2df-e6e2-4c74-8671-b350783d5ff0'
        self.textID = r'7bd51e90-2a02-4532-ab53-563ec9ad6351'
        self.param1ID = r'806cc725-66fb-4d1e-b58e-399232a82585'
        self.param2ID = r'0f1272f2-e148-44e6-8aad-6c4df5ddd485'
        self.param3ID = r'b5089d05-07b4-460c-ae65-8ffcb8b3e8f7'
        self.skNum = rs.coercerhinoobject(self.skNumID)
        self.param1 = rs.coercerhinoobject(self.param1ID)
        self.param2 = rs.coercerhinoobject(self.param2ID)
        self.param3 = rs.coercerhinoobject(self.param3ID)
        self.text = rs.coercerhinoobject(self.textID)
        
        self.progressBarID = r'e0ac605f-ff4d-471d-a5eb-65e1f8b6be94'
        self.progress = rs.coercerhinoobject(self.progressBarID).BrepGeometry
        self.plane = rg.Plane.WorldXY
        self.plane.Origin = rg.Point3d(5,100,85.913)
        
        self.skNum.Geometry.Text = 'sk'+str(skNum)
        self.skNum.CommitChanges()
        self.param1.Geometry.Text = ' '
        self.param1.CommitChanges()
        self.param2.Geometry.Text = ' '
        self.param2.CommitChanges()
        self.param3.Geometry.Text = ' '
        self.param3.CommitChanges()
        
        bbox = self.progress.GetBoundingBox(rg.Plane.WorldXY)
        currLength = bbox.Max.X - bbox.Min.X
        xScale = 1 / currLength
        xform = rg.Transform.Scale(self.plane, xScale, 1, 1)
        self.progress.Transform(xform)
        sc.doc.Objects.Replace(rs.coerceguid(self.progressBarID), self.progress)
        
        
    def Update(self, frameNum):
        self.text.Geometry.Text = str(frameNum)
        self.text.CommitChanges()
    
    def UpdateParam1(self, paramData):
        self.param1.Geometry.Text = str(paramData)
        self.param1.CommitChanges()
    def UpdateParam2(self, paramData):
        self.param2.Geometry.Text = str(paramData)
        self.param2.CommitChanges()
    def UpdateParam3(self, paramData):
        self.param3.Geometry.Text = str(paramData)
        self.param3.CommitChanges()
    
    def UpdateScaleBar(self):
        stepSize = 90/self.numFrames
        self.progress = rs.coercerhinoobject(self.progressBarID).BrepGeometry
        bbox = self.progress.GetBoundingBox(rg.Plane.WorldXY)
        currLength = bbox.Max.X - bbox.Min.X
        xScale = (currLength + stepSize) / currLength
        xform = rg.Transform.Scale(self.plane, xScale, 1, 1)
        self.progress.Transform(xform)
        sc.doc.Objects.Replace(rs.coerceguid(self.progressBarID), self.progress)
######
def ProjectVectorToPlane(vec, plane):
    pt = rg.Point3d.Add(plane.Origin, vec)
    projPt = plane.ClosestPoint(pt)
    newVec = pt-projPt
    return newVec

def RandomPointOnBrep(brep):
    safety = 0
    while True:
        safety +=1
        if safety > 30: print "Safety";break
        
        index = random.randint(0,brep.Faces.Count-1)
        face = brep.Faces[index]
        
        d0 = face.Domain(0)
        d1 = face.Domain(1)
        u = random.uniform(d0.T0, d0.T1)
        v = random.uniform(d1.T0, d1.T1)
        
        if face.IsPointOnFace(u, v):
            break
    return face.PointAt(u, v)

def BrepProximity(brep0, brep1, numBounces = 10):
    #Returns the two closest points between brep0, and brep1, on both.
    breps = [brep0, brep1]
    finalPts = [None, None]
    
    finalPts[0] = RandomPointOnBrep(breps[0])
    finalPts[1] = breps[1].ClosestPoint(finalPts[0])
    for i in range(numBounces):
        finalPts[i%1] = breps[i%1].ClosestPoint(finalPts[i%2])
    return finalPts


######
class SpecialVertex():
    def __init__(self, system, index):
        self.system = system
        self.index = index
        self.posOrig = self.system.mesh.Vertices[self.index]
        self.pos = rg.Point3d(self.posOrig)
        self.vel = rg.Vector3d(0,0,0)
        self.acc = rg.Vector3d(0,0,0)
        self.isAnchor = False
        self.neighborIndices = self.system.mesh.TopologyVertices.ConnectedTopologyVertices(self.index, True)
        if len(self.neighborIndices) < 4:
            self.isAnchor = True
    
    def Update(self):
        if self.isAnchor == False:
            geo.VectorLimit(self.acc, 1)
            self.vel += self.acc
            geo.VectorLimit(self.vel, 1)
            self.pos += self.vel
            self.acc *= 0
    
    def ApplyGravity(self):
        self.acc += rg.Vector3d(0,0,+.03)
    
    def ApplySpringForce(self):
        for neighborIndex in self.neighborIndices:
            k = .4
            restLength = 2
            force = rg.Point3d(self.system.mesh.Vertices[neighborIndex]) - self.pos
            x = restLength - force.Length
            force = rg.Vector3d(force)
            force.Unitize()
            force *= (-k*x)
            self.acc += force
    
    def ApplyToMesh(self):
        self.system.mesh.Vertices[self.index] = rg.Point3f(self.pos.X, self.pos.Y, self.pos.Z)

class Spring:
    def __init__(self, restLength, strength):
        self.restLength = restLength
        self.k = .1
        self.maxLength = 3
        self.strength = strength
    
    def connect(self, anchorBoid, boid):
        boidActualPos = boid.pos + boid.velocity
        anchorActualPos = anchorBoid.pos + anchorBoid.velocity
        
        force = rs.VectorCreate(anchorActualPos, boidActualPos)
        d = force.Length
        stretch = d - (self.restLength)
        
        force.Unitize()
        force *= self.k * stretch * self.strength
        boid.applyHardForce(force)
        return force
    
    def connectHard(self, anchorBoid, boid):
        boidActualPos = boid.pos + boid.velocity
        anchorActualPos = anchorBoid.pos + anchorBoid.velocity
        
        force = rs.VectorCreate(anchorActualPos, boidActualPos)
        d = force.Length
        stretch = d - (self.restLength)
        
        force.Unitize()
        force *= stretch * self.k
        #force *= self.k * stretch * self.strength
        boid.applyForce(force)
        return force

class Anchor():
    def __init__(self, system, index):
        self.system = system
        self.index = index
        self.age = 0

class Mesh():
    def __init__(self):
        offset = 20
        pt0 = rg.Point3d(offset, offset, 20)
        pt1 = rg.Point3d(100-offset, offset, 20)
        pt2 = rg.Point3d(100-offset, 100-offset, 20)
        pt3 = rg.Point3d(offset, 100-offset, 20)
        self.srf = rg.Brep.CreateFromCornerPoints(pt0, pt1, pt2, pt3, sc.doc.ModelAbsoluteTolerance)
        
        param = rg.MeshingParameters()
        param.MaximumEdgeLength = 2.5
        
        self.mesh = rg.Mesh.CreateFromBrep(self.srf, param)[0]
        
        self.meshDisplay = self.mesh.Duplicate()
        self.meshDisplay.Faces.ConvertQuadsToTriangles()
        self.TriangulateAndSubdivide(self.meshDisplay)
        self.id = sc.doc.Objects.AddMesh(self.meshDisplay)
        
        self.vertices = []
        for i in range(0, self.mesh.Vertices.Count):
            self.vertices.append(SpecialVertex(self, i))
        
        #self.anchors = []
        #self.anchorIndices = [0, 32, 1088-32, 1088]
        #for vertex in self.vertices:
        #    if vertex.index in self.anchorIndices:
        #        vertex.isAnchor = True
    
    def Update(self):
        if self.id:sc.doc.Objects.Delete(self.id, True)
        
        ####
        for vertex in self.vertices:
            vertex.ApplyGravity()
            vertex.ApplySpringForce()
        for vertex in self.vertices:
            vertex.Update()
        
        for vertex in self.vertices:
            vertex.ApplyToMesh()
        self.mesh.RebuildNormals()
        
        ####
        self.meshDisplay = self.mesh.Duplicate()
        self.meshDisplay.Faces.ConvertQuadsToTriangles()
        self.TriangulateAndSubdivide(self.meshDisplay)
        
        self.id = sc.doc.Objects.AddMesh(self.meshDisplay)
    
    def TriangulateAndSubdivide(self, mesh):
        everyOtherFace = []
        for i in range(mesh.Faces.Count):
            everyOtherFace.append(i)
            
            i0 = mesh.Faces[i].A
            i1 = mesh.Faces[i].B
            i2 = mesh.Faces[i].C
            
            n0 = mesh.Normals[i0]
            n1 = mesh.Normals[i1]
            n2 = mesh.Normals[i2]
            
            v0 = rg.Point3d(mesh.Vertices[i0])
            v1 = rg.Point3d(mesh.Vertices[i1])
            v2 = rg.Point3d(mesh.Vertices[i2])
            
            cn = (n0+n1+n2)/3
            ni = mesh.Normals.Add(cn)
            
            c = rg.Point3d((v0.X+v1.X+v2.X)/3, (v0.Y+v1.Y+v2.Y)/3, (v0.Z+v1.Z+v2.Z)/3)
            ci = mesh.Vertices.Add(c)
            
            mesh.Faces.AddFace(i0, i1, ci)
            mesh.Faces.AddFace(i1, i2, ci)
            mesh.Faces.AddFace(i2, i0, ci)
        
        mesh.Faces.DeleteFaces(everyOtherFace)
        mesh.Normals.ComputeNormals()
        mesh.Compact()
        #return mesh
####
def main():
    skNum = (datetime.date.today()-datetime.date(2020, 03, 29)).days + 201
    if int(skNum) > int(os.path.splitext(os.path.basename(__file__))[0]):
        print "!!!!SAVE THE SKETCH WITH A NEW NAME!!!!"
    
    rs.UnselectAllObjects()
    
    init_time = time.time()
    version = 'b'   
    anim = mp4.Animation(os.path.splitext(os.path.basename(__file__))[0] + version)
    numFrames = 250
    numPasses = 100
    anim.fps = 30
    
    td = TempDisplay()
    display = HUD(os.path.splitext(os.path.basename(__file__))[0], numFrames)
    s = Scene()
    ################################
    #SETUP
    mesh = Mesh()
    
    ################################
    for i in range(numFrames):
        start_time = time.time()
        print "Frame {}".format(i)
        if sc.escape_test(False): anim.Cleanup(); return
        ################################
        #MAIN LOOP
        mesh.Update()
        
        
        ################################
        #HUD
        #display.UpdateParam1('open: ' + str(len(pSystem.balls)))
        #display.UpdateParam2('y: ' + str(ball.pos.Y))
        #display.UpdateParam3('z: ' + str(ball.pos.Z))
        display.UpdateScaleBar()
        
        ################################
        sc.doc.Views.Redraw()
        display.Update(i)
        anim.AddFrame(numberOfPasses = numPasses)
        
        rs.Sleep(500)
        
        ################################
        #Framerate
        frameTime = time.time() - start_time
        timeLeft = (numFrames - i) * frameTime
        timeLeftStr = str(datetime.timedelta(seconds=timeLeft))
        print "Time remaining: {}".format(timeLeftStr)
    
    frameTime = time.time() - init_time
    timeLeftStr = str(datetime.timedelta(seconds=frameTime))
    print "Total Time: {}".format(timeLeftStr)
    
    if int(skNum) > int(os.path.splitext(os.path.basename(__file__))[0]):
        print "!!!!SAVE THE SKETCH WITH A NEW NAME!!!!"
    
    if os.path.isdir(r"D:\Files\Work\LIBRARY\06_RHINO\10_Python\300 DAYS\anim"):
        anim.Create(r"D:\Files\Work\LIBRARY\06_RHINO\10_Python\300 DAYS\anim", frames2Keep = [i/2, i-1])
    else:
        anim.Create(r"C:\Tim\300 Days\anim", frames2Keep = [i/2, i-1])

if __name__ == "__main__":
    main()