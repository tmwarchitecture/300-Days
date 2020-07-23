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
class Particle():
    def __init__(self):
        self.pos = rg.Point3d(50,50,35)
        self.vel = rg.Vector3d(random.uniform(-1,1), random.uniform(-1,1), 0.01)
        self.vel.Unitize()
        self.vel *= 3
        self.id = sc.doc.Objects.AddPoint(self.pos)
    def Update(self):
        if self.id:sc.doc.Objects.Delete(self.id, True)
        
        futurePos = rg.Point3d.Add(self.pos, self.vel)
        offset = 10
        if futurePos.X < offset:
            self.vel.X *= -1
        if futurePos.Y < offset:
            self.vel.Y *= -1
        if futurePos.Z < offset:
            self.vel.Z *= -1
        if futurePos.X > 100-offset:
            self.vel.X *= -1
        if futurePos.Y > 100-offset:
            self.vel.Y *= -1
        if futurePos.Z > 100-offset:
            self.vel.Z *= -1
        
        
        #rand = rg.Vector3d(random.uniform(-1,1), random.uniform(-1,1), 0)
        #rand.Unitize()
        #rand *= .5
        #self.vel += rand
        self.pos += self.vel
        self.id = sc.doc.Objects.AddPoint(self.pos)

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
        
        if len(self.neighborIndices) <= 4:
            self.isAnchor = True
        #self.isAnchor = False
        self.neighborDists = []
        for neigh in self.neighborIndices:
            self.neighborDists.append((rg.Point3d(self.system.mesh.Vertices[neigh]) - self.pos).Length)
    
    def Update(self):
        self.vel *= 0
        geo.VectorLimit(self.acc, 1)
        self.vel += self.acc
        #geo.VectorLimit(self.vel, 1)
        if self.isAnchor == False:
            self.pos += self.vel
            self.acc *= 0
    
    def ApplyGravity(self):
        self.acc += rg.Vector3d(0,0,-.1)
    
    def ApplySpringForce(self):
        for i, neighborIndex in enumerate(self.neighborIndices):
            k = .2
            #d = abs((self.system.target.pos - self.pos).Length)
            #f = util.Remap(d, 10, 30, .8, 1)
            f = .95
            restLength = self.neighborDists[i]*f
            force = rg.Point3d(self.system.mesh.Vertices[neighborIndex]) - self.pos
            x = restLength - force.Length
            force = rg.Vector3d(force)
            force.Unitize()
            force *= (-k*x)
            self.acc += force
    
    def ApplySpringForce2(self):
        for i, neighborIndex in enumerate(self.neighborIndices):
            restLength = self.neighborDists[i]
            force = rg.Point3d(self.system.mesh.Vertices[neighborIndex]) - self.pos
            x = restLength - force.Length
            force = rg.Vector3d(force)
            force.Unitize()
            force *= -x*2
            self.acc += force
    
    def ApplyInflation(self):
        n = rg.Vector3d(self.system.mesh.Normals[self.index])
        n.Unitize()
        n *= .45
        self.acc += n
    
    def AvoidBall(self):
        sphere = rg.Sphere(rg.Point3d(50,50,50), 25)
        tempVel = rg.Vector3d(self.vel)
        tempVel += self.acc
        futurePos = rg.Point3d.Add(self.pos, tempVel)
        futureD = (futurePos - rg.Point3d(50,50,50)).Length
        if futureD < 25:
            newPt = rg.Point3d.Add(self.pos, tempVel)
            
            b, p0, p1 = sphere.ClosestParameter(self.pos)
            n = sphere.NormalAt(p0, p1)
            plane = rg.Plane(self.pos, n)
            
            d = plane.DistanceTo(newPt)
            
            n.Unitize()
            n *= -d
            
            self.acc += n
    
    def ApplyToMesh(self):
        self.system.mesh.Vertices[self.index] = rg.Point3f(self.pos.X, self.pos.Y, self.pos.Z)

class Mesh():
    def __init__(self, down = False):
        #self.target = Particle()
        self.down = down
        offset = 12
        pt0 = rg.Point3d(offset, offset, 50)
        pt1 = rg.Point3d(100-offset, offset, 50)
        pt2 = rg.Point3d(100-offset, 100-offset, 50)
        pt3 = rg.Point3d(offset, 100-offset, 50)
        self.srf = rg.Brep.CreateFromCornerPoints(pt0, pt1, pt2, pt3, sc.doc.ModelAbsoluteTolerance)
        
        param = rg.MeshingParameters()
        param.MaximumEdgeLength = 5
        
        self.mesh = rg.Mesh.CreateFromBrep(self.srf, param)[0]
        
        if self.down:
            self.mesh.Flip(True, True, True)
        
        self.mesh.Faces.ConvertQuadsToTriangles()
        self.meshDisplay = self.mesh.Duplicate()
        self.time = 0
        #self.meshDisplay.Faces.ConvertQuadsToTriangles()
        #self.TriangulateAndSubdivide(self.meshDisplay)
        self.id = sc.doc.Objects.AddMesh(self.meshDisplay)
        
        self.vertices = []
        for i in range(0, self.mesh.Vertices.Count):
            self.vertices.append(SpecialVertex(self, i))
        
        
        #self.anchors = []
        #self.anchorIndices = [0, 32, 1088-32, 1088]
        #for vertex in self.vertices:
        #    if vertex.index in self.anchorIndices:
        #        vertex.isAnchor = True
    
    def Update(self, time):
        self.time = time
        #self.target.Update()
        
        if self.id:sc.doc.Objects.Delete(self.id, True)
        
        ####
        for vertex in self.vertices:
        #    vertex.ApplyGravity()
            vertex.ApplySpringForce()
            vertex.ApplyInflation()
            #vertex.AvoidBall()
        for vertex in self.vertices:
            vertex.Update()
        
        for vertex in self.vertices:
            vertex.ApplyToMesh()
        
        self.meshDisplay = self.mesh.Duplicate()
        self.TriangulateAndSubdivide(self.meshDisplay)
        self.MeshWindow()
        
        ####
        #self.meshDisplay = self.mesh.Duplicate()
        #self.meshDisplay.Faces.ConvertQuadsToTriangles()
        
        self.id = sc.doc.Objects.AddMesh(self.meshDisplay)
    
    def MeshWindow(self):
        #sc.doc.Objects.AddMesh(self.meshDisplay)
        
        toDelete = []
        for i in range(self.meshDisplay.Faces.Count):
            toDelete.append(i)
            #z = self.meshDisplay.Vertices[self.meshDisplay.Faces[i].A].Z
            t = math.sin(util.Remap(self.time, 0, 150, 0, 1)*15)
            
            offset = util.Remap(t, -1, 1, 0.3, .00)
            #offset = .1
            i0 = self.meshDisplay.Faces[i].A
            i1 = self.meshDisplay.Faces[i].B
            i2 = self.meshDisplay.Faces[i].C
            
            #n0 = self.mesh.Normals[i0]
            #n1 = self.mesh.Normals[i1]
            #n2 = self.mesh.Normals[i2]
            
            v0 = rg.Point3d(self.meshDisplay.Vertices[i0])
            v1 = rg.Point3d(self.meshDisplay.Vertices[i1])
            v2 = rg.Point3d(self.meshDisplay.Vertices[i2])
            
            c0 = self.meshDisplay.PointAt(i, offset, 1-offset*2, offset, 0)
            c1 = self.meshDisplay.PointAt(i, offset, offset, 1-offset*2, 0)
            c2 = self.meshDisplay.PointAt(i, 1-offset*2, offset, offset, 0)
            
            #cn = (n0+n1+n2)/3
            #ni = mesh.Normals.Add(cn)
            
            #c = rg.Point3d((v0.X+v1.X+v2.X)/3, (v0.Y+v1.Y+v2.Y)/3, (v0.Z+v1.Z+v2.Z)/3)
            c0i = self.meshDisplay.Vertices.Add(c0)
            c1i = self.meshDisplay.Vertices.Add(c1)
            c2i = self.meshDisplay.Vertices.Add(c2)
            
            self.meshDisplay.Faces.AddFace(i0, i1, c0i, c2i)
            self.meshDisplay.Faces.AddFace(i1, i2, c1i, c0i)
            self.meshDisplay.Faces.AddFace(i2, i0, c2i, c1i)
            #mesh.Faces.AddFace(i1, i2, ci)
            #mesh.Faces.AddFace(i2, i0, ci)
        
        self.meshDisplay.Faces.DeleteFaces(toDelete)
        self.meshDisplay.Normals.ComputeNormals()
        self.meshDisplay.Compact()
        self.meshDisplay.RebuildNormals()
    
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
    
    def MoveVertexAlongNormal(self, i, d):
        vertex = self.mesh.Vertices[i]
        
        v = rg.Point3d(vertex)
        vec = rg.Vector3d(self.mesh.Normals[i])
        vec.Unitize()
        
        val = util.Remap(d, 0, 20, math.pi, 0)
        val = 1-(math.cos(val)+1)*.5        
        
        vec *= val*1.5
        
        v += vec
        
        self.mesh.Vertices[i] = rg.Point3f(v.X, v.Y, v.Z)

    
####
def main():
    skNum = (datetime.date.today()-datetime.date(2020, 03, 29)).days + 201
    if int(skNum) > int(os.path.splitext(os.path.basename(__file__))[0]):
        print "!!!!SAVE THE SKETCH WITH A NEW NAME!!!!"
    
    rs.UnselectAllObjects()
    
    init_time = time.time()
    version = 'a'   
    anim = mp4.Animation(os.path.splitext(os.path.basename(__file__))[0] + version)
    numFrames = 150
    numPasses = 100
    anim.fps = 30
    
    td = TempDisplay()
    display = HUD(os.path.splitext(os.path.basename(__file__))[0], numFrames)
    s = Scene()
    ################################
    #SETUP
    mesh = Mesh()
    mesh1 = Mesh(True)
    
    ################################
    for i in range(numFrames):
        start_time = time.time()
        print "Frame {}".format(i)
        if sc.escape_test(False): anim.Cleanup(); return
        ################################
        #MAIN LOOP
        mesh.Update(i)
        mesh1.Update(i)
        
        
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
        
        #rs.Sleep(500)
        
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