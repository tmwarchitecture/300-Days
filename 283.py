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
#import clr; clr.AddReference("Grasshopper") 
#import Grasshopper as gh
#from itertools import combinations as cb
#import itertools

import lib.color as color
import lib.mp4 as mp4
import lib.geometry as geo
import lib.util as util
import lib.perlin as perlin
import lib.region as region
#from lib.chull2 import Hull  


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
class Dot():
    def __init__(self, system):
        self.system = system
        self.pos = rg.Point3d(random.uniform(10,90), random.uniform(10,90), random.uniform(10,90))
        #self.vel = rg.Vector3d(random.uniform(-2, 2),random.uniform(-2, 2),random.uniform(-2, 2))
        self.vel = rg.Vector3d(0,0,0)
        self.vel.Unitize()
        self.vel *= 5
        self.acc = rg.Vector3d(0,0,0)
        
        self.vel += self.acc
        self.id = None
        self.ids = []
        self.age = 0
        
        self.prevPlane = rg.Plane.WorldXY
        self.xform = None
        
        #Attr
        self.attr = rc.DocObjects.ObjectAttributes()
        self.attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        self.grad = color.GetGradient(10)
        self.attr.ObjectColor = color.GradientOfColors(self.grad, 0)
        self.attr.MaterialSource = rc.DocObjects.ObjectMaterialSource.MaterialFromObject
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = self.attr.ObjectColor
        self.mat.CommitChanges()
        self.attr.MaterialIndex = index
        
        self.InitTriangle()
        #self.mesh = self.InitTriangle()
    
    def InitTriangle(self):
        xval = util.Remap(self.pos.X, 0, 100, 0, 1*2)
        yval = util.Remap(self.pos.Y, 0, 100, 0, 1*2)
        zval = util.Remap(self.pos.Z, 0, 100, 0, 1*5)
        val = self.system.pn.noise3(xval+self.system.p.pos.X, yval+self.system.p.pos.Y, zval+self.system.p.pos.Z)
        self.size = util.Remap(val, -1, 1, -2, 2)
        if self.size > 0:
            self.pt0 = rg.Point3f(0, self.size, 0)
            self.pt1 = rg.Point3f(-self.size/2, 0, 0)
            self.pt2 = rg.Point3f(self.size/2, 0, 0)
            
            camPos = sc.doc.Views.ActiveView.ActiveViewport.CameraLocation
            vec = camPos - self.pos
            plane = rg.Plane(self.pos, vec)
            testPt = self.pos + rg.Vector3f(0,0,1)
            cp = plane.ClosestPoint(testPt)
            yAxis = cp-self.pos
            xprod = rg.Vector3d.CrossProduct(vec, yAxis)
            plane = rg.Plane(self.pos, xprod, yAxis)
            xform = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, plane)
            #self.xform = rg.Transform.PlaneToPlane(self.prevPlane, plane)
            self.prevPlane = plane.Clone()
            
            col = color.GradientOfColors(self.grad, util.Remap(val, -1, 1, -1, 1), 2)
            
            self.system.mesh.VertexColors.Add(col)
            self.system.mesh.VertexColors.Add(col)
            self.system.mesh.VertexColors.Add(col)
            
            self.pt0.Transform(xform)
            self.pt1.Transform(xform)
            self.pt2.Transform(xform)
            i0 = self.system.mesh.Vertices.Add(self.pt0)
            i1 = self.system.mesh.Vertices.Add(self.pt1)
            i2 = self.system.mesh.Vertices.Add(self.pt2)
            self.system.mesh.Faces.AddFace(i0, i1, i2)
        
    
    def MoveTriangle(self):
        camPos = sc.doc.Views.ActiveView.ActiveViewport.CameraLocation
        vec = camPos - self.pos
        plane = rg.Plane(self.pos, vec)
        testPt = self.pos + rg.Vector3f(0,0,1)
        cp = plane.ClosestPoint(testPt)
        yAxis = cp-self.pos
        xprod = rg.Vector3d.CrossProduct(vec, yAxis)
        plane = rg.Plane(self.pos, xprod, yAxis)
        self.xform = rg.Transform.PlaneToPlane(self.prevPlane, plane)
        self.prevPlane = plane.Clone()
        self.system.mesh.Transform(self.xform)
    
    def CalcPrimaryAxis(self):
        data = [[abs(self.vel.X),0], [abs(self.vel.Y), 1], [abs(self.vel.Z), 2]]
        data.sort()
        largest = data[-1]
        if largest[1] == 0:
            self.primaryAxis = rg.Vector3d(1,0,0) * self.futureVel.X
        elif largest[1] == 1:
            self.primaryAxis = rg.Vector3d(0,1,0) * self.futureVel.Y
        elif largest[1] == 2:
            self.primaryAxis = rg.Vector3d(0,0,1) * self.futureVel.Z
    
    def CalcFuturePos(self):
        tempVel = rg.Vector3d(self.vel)
        tempVel += self.acc
        self.futureVel = rg.Vector3d(self.vel)
        self.futureVel += self.acc
        self.futurePos = rg.Point3d.Add(self.pos, tempVel)
        
        self.primaryAxis = self.CalcPrimaryAxis()
    
    def CheckForFloorCollision(self):
        x0 = self.futurePos.X+self.box.X.Min
        x1 = self.futurePos.X+self.box.X.Max
        y0 = self.futurePos.Y+self.box.Y.Min
        y1 = self.futurePos.Y+self.box.Y.Max
        z0 = self.futurePos.Z+self.box.Z.Min
        z1 = self.futurePos.Z+self.box.Z.Max
        
        tempAcc = rg.Vector3d(self.acc)
        tempAcc.Reverse()
        if z0 < 0:
            reaction = rg.Vector3d(0,0,-1)
            reaction *= z0
            self.vel += reaction
            self.vel.X *=.9
            self.vel.Y *=.9
        elif x0 < 0:
            reaction = rg.Vector3d(-1,0,0)
            reaction *= x0
            self.vel += reaction
            self.vel.X *=.9
            self.vel.Y *=.9
        elif y0 < 0:
            reaction = rg.Vector3d(0,-1,0)
            reaction *= y0
            self.vel += reaction
            self.vel.X *=.9
            self.vel.Y *=.9
        elif x1 > 100:
            reaction = rg.Vector3d(-1,0,0)
            reaction *= x1-100
            self.vel += reaction
            self.vel.X *=.9
            self.vel.Y *=.9
        elif y1 > 100:
            reaction = rg.Vector3d(0,-1,0)
            reaction *= y1-100
            self.vel += reaction
            self.vel.X *=.9
            self.vel.Y *=.9
    
    def Update(self):
        self.age += 1
        self.UpdatePosition()
        #self.UpdateDisplay()
    
    def UpdatePosition(self):
        self.vel *= .5
        
        self.vel += self.acc
        #self.vel *= util.Constrain(self.vel.Length, 2)
        self.pos += self.vel
        
        self.InitTriangle()
    
    def UpdateDisplay(self):
        self.attr.ObjectColor = color.GradientOfColors(self.grad, util.Remap(self.acc.Length, 0, .25, 0, 1))
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = self.attr.ObjectColor
        self.mat.CommitChanges()
        self.attr.MaterialIndex = index
        
        #for id in self.ids:
        #    sc.doc.Objects.Delete(id, True)
        
        #if self.id: sc.doc.Objects.Delete(self.id, True)
        
        #self.id = sc.doc.Objects.AddMesh(self.mesh, self.attr)
        
        #if self.id is None:
        #    self.id = sc.doc.Objects.AddMesh(self.mesh, self.attr)
        #else:
        #    self.id = sc.doc.Objects.Transform(self.id, self.xform, True)

class Link():
    def __init__(self, a, b):
        self.objA = a
        self.objB = b
        self.objs = [a,b]
        self.report = []
    
    def Resolve(self):
        if self.objA.age < 10: return
        if self.objB.age < 10: return
        self.report = []
        
        safety  = 0
        collided = True
        while collided:
            safety += 1
            if safety > 20:
                #print "SAFETY {}".format(safety)
                self.report.append(self.objA.id)
                self.report.append(self.objB.id)
                return
            collided = False
            x0a = self.objA.futurePos.X+self.objA.box.X.Min
            x1a = self.objA.futurePos.X+self.objA.box.X.Max
            y0a = self.objA.futurePos.Y+self.objA.box.Y.Min
            y1a = self.objA.futurePos.Y+self.objA.box.Y.Max
            z0a = self.objA.futurePos.Z+self.objA.box.Z.Min
            z1a = self.objA.futurePos.Z+self.objA.box.Z.Max
            
            x0b = self.objB.futurePos.X+self.objB.box.X.Min
            x1b = self.objB.futurePos.X+self.objB.box.X.Max
            y0b = self.objB.futurePos.Y+self.objB.box.Y.Min
            y1b = self.objB.futurePos.Y+self.objB.box.Y.Max
            z0b = self.objB.futurePos.Z+self.objB.box.Z.Min
            z1b = self.objB.futurePos.Z+self.objB.box.Z.Max
            
            boolX, xd0, xd1 = self.OverlappingIntervals(x0a,x1a, x0b, x1b)
            boolY, yd0, yd1 = self.OverlappingIntervals(y0a,y1a, y0b, y1b)
            boolZ, zd0, zd1 = self.OverlappingIntervals(z0a,z1a, z0b, z1b)
            if boolX == True and boolY == True and boolZ == True:
                #1 Yes, all overlapping
                collided = True
                
                #2 Which pos's overlapping?
                nonOverlappingAxis = [0,1,2]
                nonOverlappingAxis = self.RemoveOverlappingAxis(nonOverlappingAxis)
                if len(nonOverlappingAxis) > 0:
                    rA = self.GetSmallestAxis(self.objA.vel, nonOverlappingAxis)
                    rB = self.GetSmallestAxis(self.objB.vel, nonOverlappingAxis)
                    tunnelDist = [0,0,0]
                    xd = 0
                    yd = 0
                    zd = 0
                else:
                    #pos is already totally overlapping
                    xd = xd0-xd1
                    yd = yd0-yd1
                    zd = zd0-zd1
                    vals = [[xd,0],[yd,1],[zd,2]]
                    vals.sort()
                    axis = vals[0][1]
                    rA = self.GetLargestAxis(self.objA.vel, [0,1,2], [xd,yd,zd])
                    rB = self.GetLargestAxis(self.objB.vel, [0,1,2], [xd,yd,zd])
                    
                f = .0
                self.objA.vel += (rA*(1+f))
                self.objB.vel += (rB*(1+f))
                
                self.objA.Update()
                self.objB.Update()
                
                self.objA.CalcFuturePos()
                self.objB.CalcFuturePos()
        if collided == False:
            self.report.append(safety)
    
    def OverlappingIntervals(self, a0, a1, b0, b1):
        if a1 > b0 and b1 > a0:
            return True, max(a1,b1)-min(a0,b0), a1-b0
        else:
            return False, 0, 0
    
    def OverlappingIntervals2(self, axis):
        a0 = self.objA.pos[axis] + self.objA.box.X.Min
        a1 = self.objA.pos[axis] + self.objA.box.X.Max
        b0 = self.objB.pos[axis] + self.objB.box.X.Min
        b1 = self.objB.pos[axis] + self.objB.box.X.Max
        
        if a1 > b0 and b1 > a0:
            return True
        else:
            return False
    
    def RemoveOverlappingAxis(self, axes):
        axesToRemove = []
        for axis in axes:
            if self.OverlappingIntervals2(axis):
                axesToRemove.append(axis)
        
        for axis in axesToRemove:
            axes.remove(axis)
        
        return axes
    
    def GetSmallestAxis(self, vec, axes):
        tempVec = rg.Vector3d(vec)
        #tempVec += self.objA.acc
        
        smallestAxis = None
        smallestAxisVal = None
        for axis in axes:
            if abs(tempVec[axis]) < smallestAxisVal or smallestAxisVal is None:
                smallestAxisVal = abs(tempVec[axis])
                smallestAxis = axis
        r = rg.Vector3d(0,0,0)
        r[smallestAxis] = tempVec[smallestAxis] * -1
        return r
    
    def GetLargestAxis(self, vec, axes, tunnelDists):
        largestAxis = None
        largestAxisVal = None
        for axis in axes:
            if abs(vec[axis]) > largestAxisVal or largestAxisVal is None:
                largestAxisVal = abs(vec[axis])
                largestAxis = axis
        r = rg.Vector3d(0,0,0)
        r[largestAxis] = vec[largestAxis] * -1
        additionalDist = rg.Vector3d(0,0,0)
        additionalDist[largestAxis] = tunnelDists[largestAxis]
        if r[largestAxis] < 0:
            additionalDist *= -1
        r -= additionalDist
        return r
    
    def PrintReport(self):
        if len(self.report) > 1:
            print self.report
    
    def Seperate(self, minDist):
        d = (self.objA.pos-self.objB.pos).Length
        if d < minDist:
            pass
            #print "Too Close"

class PointObj(geo.Particle):
    def UpdateDisplay(self):
        self.pos += self.vel
        sphere = rg.Sphere(self.pos, self.size)
        if self.id:
            sc.doc.Objects.Delete(self.id, True)
        self.id = sc.doc.Objects.AddSphere(sphere)

class ParticleSystem():
    def __init__(self):
        self.p = Target(rg.Point3d(50,50,50), rg.Vector3d(.05,0.05,0.05))
        self.dots = []
        self.time = 0
        self.links = []
        self.id = None
        self.grad = color.GetGradient(10)
        self.mesh = rg.Mesh()
        self.pn = perlin.SimplexNoise()
        for i in range(1000):
            self.dots.append(Dot(self))
        
        #Attr
        self.attr = rc.DocObjects.ObjectAttributes()
        self.attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        self.grad = color.GetGradient(10)
        self.attr.ObjectColor = color.GradientOfColors(self.grad, 0)
        self.attr.MaterialSource = rc.DocObjects.ObjectMaterialSource.MaterialFromObject
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = self.attr.ObjectColor
        self.mat.CommitChanges()
        self.attr.MaterialIndex = index
        
    def Update(self, time):
        self.time = time
        self.p.Update()
        #print self.p.pos
        
        for dot in self.dots:
            dot.Update()
        
        if self.id: sc.doc.Objects.Delete(self.id, True)
        self.id = sc.doc.Objects.AddMesh(self.mesh, self.attr)
        
        self.mesh = rg.Mesh()
        
        #for link in self.links:
        #    link.Resolve()
        
        if False:
            self.links = []
            for i in range(len(self.boxes)):
                for j in range(i+1, len(self.boxes)):
                    #Could add in a distance max here
                    if (self.boxes[i].pos - self.boxes[j].pos).Length < 30:
                        if self.boxes[i].age > 20 and self.boxes[i].age > 20:
                            self.links.append(Link(self.boxes[i], self.boxes[j]))

class Crawler():
    def __init__(self, system):
        self.system = system
        self.pos = geo.RandomPoint()
        self.vel = geo.RandomVector3d(1)
        self.acc = rg.Vector3d(0,0,0)
        #self.id = sc.doc.Objects.AddPoint(self.pos)
        self.plineId = None
        self.history = []
        self.speed = 3
        self.mesh = rg.Mesh()
        self.meshID = None
        self.neighbors = []
    
    def Update(self):
        futurePos = rg.Point3d.Add(self.pos, self.vel)
        if futurePos.X < 5:
            self.vel.X *= -1
        if futurePos.Y < 5:
            self.vel.Y *= -1
        if futurePos.Z < 5:
            self.vel.Z *= -1
        if futurePos.X > 95:
            self.vel.X *= -1
        if futurePos.Y > 95:
            self.vel.Y *= -1
        if futurePos.Z > 95:
            self.vel.Z *= -1
        
        
        mp = self.system.mesh.ClosestMeshPoint(futurePos, 1000)
        
        n = self.system.mesh.NormalAt(mp.FaceIndex, mp.T[0], mp.T[1], mp.T[2], mp.T[3])
        plane = rg.Plane(mp.Point, n)
        
        projPt = rg.Point3d.Add(mp.Point, self.vel)
        closestPt = plane.ClosestPoint(projPt)
        prevSpeed = self.vel.Length
        self.vel = closestPt-mp.Point
        
        self.vel.Unitize()
        self.vel *= prevSpeed
        
        #rand = geo.RandomVector3d(1)
        #self.vel += rand
        self.vel += self.acc
        
        self.pos = mp.Point
        self.history.append(self.pos)
        self.acc = rg.Vector3d(0,0,0)
        
    
    def ApplySpringForce(self):
        for neighbor in self.neighbors:
            k = .4
            restLength = 2
            force = neighbor.pos - self.pos
            x = restLength - force.Length
            force = rg.Vector3d(force)
            force.Unitize()
            self.acc += force
    
    def UpdateNeighbors(self):
        self.neighbors = []
        for pt in self.system.pts:
            if pt is self: continue
            d = (pt.pos-self.pos).Length
            if d < 7:
                self.neighbors.append(pt)
        
        self.neighbors = self.neighbors[:4]
        
        self.ApplySpringForce()
    
    def UpdateDisplay(self):
        #if self.id: sc.doc.Objects.Delete(self.id, True)
        if self.plineId: sc.doc.Objects.Delete(self.plineId, True)
        if self.meshID: sc.doc.Objects.Delete(self.meshID, True)
        
        mesh = rg.Mesh()
        
        for neighbor in self.neighbors:
            for neighborNeighbor in neighbor.neighbors:
                if neighborNeighbor in self.neighbors:
                    id0 = mesh.Vertices.Add(self.pos)
                    id1 = mesh.Vertices.Add(neighbor.pos)
                    id2 = mesh.Vertices.Add(neighborNeighbor.pos)
                    face = mesh.Faces.AddFace(id0, id1, id2)
        
        
        
        self.meshID = sc.doc.Objects.AddMesh(mesh)
        #self.id = sc.doc.Objects.AddPoint(self.pos)
        #pline = rg.Polyline(self.history)
        #self.plineId = sc.doc.Objects.AddPolyline(pline)

class Vertex():
    def __init__(self, system, x,y,z, xi, yi, zi):
        self.system = system
        self.pos = rg.Point3f(x,y,z)
        
        self.xi = xi
        self.yi = yi
        self.zi = zi
        
        sum = 0
        for target in self.system.targets:
            d = ((target.pos - rg.Point3d(self.pos)).Length)
            if d > 0:
                sum += target.radius/d
        self.isoValue = sum
        
        self.attr = self.system.attr.Duplicate()
        self.attr.ObjectColor = color.GradientOfColors(self.system.grad, util.Remap(self.isoValue, .2, .8, 0, 1), 2)
        
        #self.id = sc.doc.Objects.AddPoint(self.pos, self.attr)
        self.neighbors = []
        
        
    
    def Update(self):
        sum = 0
        for target in self.system.targets:
            d = ((target.pos - rg.Point3d(self.pos)).Length)
            if d > 0:
                sum += target.radius/d
            
        self.isoValue = sum

class Edge():
    def __init__(self, system, v0, v1):
        self.system = system
        self.vertices = [v0, v1]
        self.v0 = v0
        self.v1 = v1
        self.line = rg.Line(v0.pos, v1.pos)
        self.isoPt = None
    def CheckCompliance(self):
        val = self.system.isoValue
        if self.v0.isoValue < val and self.v1.isoValue < val:
            return 0, None
            #both smaller
        elif self.v0.isoValue < val and self.v1.isoValue > val:
            #v0 smaller
            delta = self.system.isoValue - self.v0.isoValue
            d = self.v1.isoValue-self.v0.isoValue
            t = delta/d
            pt = self.line.PointAt(t)
            return 2, pt
        elif self.v0.isoValue > val and self.v1.isoValue < val:
            #v1 smaller
            delta = self.system.isoValue - self.v0.isoValue
            d = self.v1.isoValue-self.v0.isoValue
            t = delta/d
            pt = self.line.PointAt(t)
            return 2, pt
        elif self.v0.isoValue > val and self.v1.isoValue > val:
            #all are larger
            return 1, None
        
class Voxel():
    def __init__(self, system, x,y,z, xi,yi,zi):
        self.system = system
        self.pos = rg.Point3d(x,y,z)
        plane = rg.Plane(self.pos, rg.Vector3d(0,0,1))
        box = rg.Box(plane, rg.Interval(0, self.system.voxelSize), rg.Interval(0, self.system.voxelSize), rg.Interval(0, self.system.voxelSize))
        self.box = rg.Mesh.CreateFromBox(box, 1, 1, 1)
        self.centerPt = None
        self.val = None
        self.xi = xi
        self.yi = yi
        self.zi = zi
        self.vertices = []
        self.Setup()
        self.id = None
        self.attr = self.system.attr.Duplicate()
        
        self.edges = []
        self.SetupEdges()
        self.interPts = []
    
    def Setup(self):
        self.vertices.append(self.system.vertices[self.xi][self.yi+1][self.zi])
        self.vertices.append(self.system.vertices[self.xi+1][self.yi+1][self.zi])
        self.vertices.append(self.system.vertices[self.xi+1][self.yi][self.zi])
        self.vertices.append(self.system.vertices[self.xi][self.yi][self.zi])
        self.vertices.append(self.system.vertices[self.xi][self.yi+1][self.zi+1])
        self.vertices.append(self.system.vertices[self.xi+1][self.yi+1][self.zi+1])
        self.vertices.append(self.system.vertices[self.xi+1][self.yi][self.zi+1])
        self.vertices.append(self.system.vertices[self.xi][self.yi][self.zi+1])
        
        self.centerPt = geo.PointBetweenPoints(self.vertices[0].pos, self.vertices[6].pos)
    
    def SetupEdges(self):
        self.edges = []
        self.edges.append(Edge(self.system, self.vertices[0], self.vertices[1]))
        self.edges.append(Edge(self.system, self.vertices[1], self.vertices[2]))
        self.edges.append(Edge(self.system, self.vertices[2], self.vertices[3]))
        self.edges.append(Edge(self.system, self.vertices[3], self.vertices[0]))
        
        self.edges.append(Edge(self.system, self.vertices[4], self.vertices[5]))
        self.edges.append(Edge(self.system, self.vertices[5], self.vertices[6]))
        self.edges.append(Edge(self.system, self.vertices[6], self.vertices[7]))
        self.edges.append(Edge(self.system, self.vertices[7], self.vertices[4]))
        
        self.edges.append(Edge(self.system, self.vertices[0], self.vertices[4]))
        self.edges.append(Edge(self.system, self.vertices[1], self.vertices[5]))
        self.edges.append(Edge(self.system, self.vertices[2], self.vertices[6]))
        self.edges.append(Edge(self.system, self.vertices[3], self.vertices[7]))
    
    def AddMesh(self):
        m = rg.Mesh()
        ids = []
        for v in self.vertices:
            ids.append(m.Vertices.Add(v.pos))
        id0 = m.Vertices.Add(self.vertices[0].pos)
        id1 = m.Vertices.Add(self.vertices[3].pos)
        id2 = m.Vertices.Add(self.vertices[6].pos)
        m.Faces.AddFace(id0, id1, id2)
        self.id = sc.doc.Objects.AddMesh(m)
    
    def Update(self):
        self.interPts = []
        for edge in self.edges:
            r, pt = edge.CheckCompliance()
            if r == 2:
                self.interPts.append(pt)
    
    def UpdateDisplay(self):
        if self.id: sc.doc.Objects.Delete(self.id, True)
        
        if len(self.interPts) >= 3:
            
            r, plane = rg.Plane.FitPlaneToPoints(self.interPts)
            if r == rg.PlaneFitResult.Success:
                if False:
                    v = plane.RemapToPlaneSpace(self.vertices[0].pos)[1]
                    if v.Z < 0 and self.vertices[0].isoValue < self.system.isoValue:
                        #keep plane
                        pass
                    elif v.Z < 0 and self.vertices[0].isoValue >= self.system.isoValue:
                        #flip plane
                        nRev = plane.Normal
                        nRev.Reverse()
                        plane = rg.Plane(plane.Origin, nRev)
                    elif v.Z >= 0 and self.vertices[0].isoValue < self.system.isoValue:
                        #flip plane
                        nRev = plane.Normal
                        nRev.Reverse()
                        plane = rg.Plane(plane.Origin, nRev)
                    elif v.Z >= 0 and self.vertices[0].isoValue >= self.system.isoValue:
                        #keep plane
                        pass
                
                mesh = geo.DelaunayMesh(self.interPts, plane)
                self.system.mesh.Append(mesh)
                
                #self.id = sc.doc.Objects.AddMesh(mesh)
        
        
        if False:
            self.attr.ObjectColor = color.GradientOfColors(self.system.grad, util.Remap(len(self.belowVertices), 0, 8, 0, 1), 2)            
            
            index = sc.doc.Materials.Add()
            mat = sc.doc.Materials[index]
            mat.DiffuseColor = self.attr.ObjectColor
            mat.CommitChanges()
            self.attr.MaterialIndex = index

class VoxelSystem():
    def __init__(self, targets, iv):
        self.numVoxels = 25
        self.voxelSize = 4
        self.grad = color.GetGradient(10)
        self.targets = []
        self.isoValue = iv
        self.mesh = rg.Mesh()
        self.id = None
        self.pts = []
        self.ptsCollection = rc.Collections.Point3dList()
        
        
        self.targets = targets
        
        self.attr = rc.DocObjects.ObjectAttributes()
        self.attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        grad = color.GetGradient(5)
        self.attr.ObjectColor = color.GradientOfColors(grad, util.Remap(self.isoValue, .3, .5, 0, 1), 3)
        self.attr.MaterialSource = rc.DocObjects.ObjectMaterialSource.MaterialFromObject
        index = sc.doc.Materials.Add()
        mat = sc.doc.Materials[index]
        mat.DiffuseColor = self.attr.ObjectColor
        mat.CommitChanges()
        self.attr.MaterialIndex = index
        
        
        
        #Setup Vertices
        self.vertices = []
        for x in range(self.numVoxels+1):
            yRow = []
            for y in range(self.numVoxels+1):
                zRow = []
                for z in range(self.numVoxels+1):
                    zRow.append(Vertex(self, x*self.voxelSize, y*self.voxelSize, z*self.voxelSize, x, y, z))
                yRow.append(zRow)
            self.vertices.append(yRow)
        
        #Setup Voxels
        self.voxels = []
        index = 0
        for x in range(self.numVoxels):
            for y in range(self.numVoxels):
                for z in range(self.numVoxels):
                    self.voxels.append(Voxel(self, x*self.voxelSize, y*self.voxelSize, z*self.voxelSize, x,y,z))
    
    def Update(self):
        for row in self.vertices:
            for column in row:
                for vertex in column:
                    vertex.Update()
        for voxel in self.voxels:
            voxel.Update()
            voxel.UpdateDisplay()
    
    def UpdateDisplay(self):
        if self.id: sc.doc.Objects.Delete(self.id, True)
        
        self.mesh.Compact()
        self.mesh.UnifyNormals()
        self.mesh.RebuildNormals()
        self.id = sc.doc.Objects.AddMesh(self.mesh, self.attr)
    
    def ClearMesh(self):
        self.mesh = rg.Mesh()
    
    def AddPoints(self):
        for i in range(1500):
            self.pts.append(Crawler(self))
    
    def UpdatePoints(self):
        for pt in self.pts:
            pt.UpdateNeighbors()
        for pt in self.pts:
            pt.Update()
            pt.UpdateDisplay()

class vObject():
    def __init__(self, system, v, i):
        self.size = 4
        
        self.index = i
        self.system = system
        self.vertex = rg.Point3d(v)
        self.pos = rg.Point3d(v)
        self.neighbors = self.system.mesh.Vertices.GetConnectedVertices(self.index)
        
        
        
        self.attr = self.system.attr.Duplicate()
        self.d = 0
        self.vel = geo.RandomVector3d(1)
        self.vel = rg.Vector3d(0,0,0)
        self.acc = rg.Vector3d(0,0,0)
        
        
        self.isAnchor = False
        meshEdgePointStatus = self.system.mesh.GetNakedEdgePointStatus()
        if meshEdgePointStatus[self.index] == True:
            self.isAnchor = True
        
        if self.isAnchor == False:
            val = random.uniform(0,1)
            if val < .1:
                self.isMover = True
            else:
                self.isMover = False
    
    def UpdateDisplay(self):
        sphere = rg.Sphere(self.system.mesh.Vertices[self.index], .8)
        
        self.attr.ObjectColor = color.GradientOfColors(self.system.grad, util.Remap(self.d, 0, 30, 0, 1), 3)
        index = sc.doc.Materials.Add()
        mat = sc.doc.Materials[index]
        mat.DiffuseColor = self.attr.ObjectColor
        mat.CommitChanges()
        self.attr.MaterialIndex = index
        
        self.system.ids.append(sc.doc.Objects.AddSphere(sphere, self.attr))
    
    def UpdateNeighbors(self):
        self.neighbors = self.system.mesh.Vertices.GetConnectedVertices(self.index)
    
    def ApplySpring(self):
        #self.size += .25
        restLength = 0
        self.vertex = rg.Point3d(self.system.mesh.Vertices[self.index])
        pts = []
        
        for neigh in self.neighbors:
            p = rg.Point3d(self.system.mesh.Vertices[neigh])
            force = self.vertex-p
            d = force.Length
            stretch = d- restLength
            
            force.Unitize()
            force.Reverse()
            stretch = util.Constrain(stretch, -3, 3)
            force*= stretch*.2
            
            self.acc += force
    
    def UpdatePosition(self):
        self.vel += self.acc
        if self.isAnchor == False:
            self.system.mesh.Vertices[self.index] += rg.Vector3f(self.vel.X, self.vel.Y, self.vel.Z)
        self.vel *= .4
        self.acc = rg.Vector3d(0,0,0)

class vSystem():
    def __init__(self, mesh):
        self.attr = rc.DocObjects.ObjectAttributes()
        self.attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        self.grad = color.GetGradient(4)
        self.attr.MaterialSource = rc.DocObjects.ObjectMaterialSource.MaterialFromObject
        self.mesh = mesh.Duplicate()
        self.meshOrig = mesh.Duplicate()
        self.ids = []
        self.vObjects = []
        self.targets = []
        for i in range(len(self.mesh.Vertices)):
            self.targets.append(i)
        
        for i, v in enumerate(self.mesh.Vertices):
            self.vObjects.append(vObject(self, v, i))
        
        self.sourceIndex = random.randint(0, len(self.mesh.Vertices))
        self.vObjects[self.sourceIndex].UpdateDisplay()
        
        while True:
            self.targetIndex = random.randint(0, len(self.mesh.Vertices))
            if self.targetIndex != self.sourceIndex: break
        self.path = None
        self.targets.Remove(self.sourceIndex)
        
        pn = perlin.SimplexNoise()
        for i, v in enumerate(self.mesh.Vertices):
            val = pn.noise2(util.Remap(v.X, 10, 90, 0, 3), util.Remap(v.Y, 0, 50, 0, 3))
            vec = self.meshOrig.Normals[i]
            vec = rg.Vector3d(vec)
            vec *= val * 8
            xform = rg.Transform.Translation(vec)
            v.Transform(xform)
            self.mesh.Vertices[i] = v
        
        for i, v in enumerate(self.mesh.Vertices):
            val = pn.noise2(util.Remap(v.X, 10, 90, 0, 1), util.Remap(v.Y, 0, 50, 0, 1))
            vec = self.meshOrig.Normals[i]
            vec = rg.Vector3d(vec)
            vec *= val * 20
            xform = rg.Transform.Translation(vec)
            v.Transform(xform)
            self.mesh.Vertices[i] = v
        sc.doc.Objects.AddMesh(self.mesh)
        
        sphere = rg.Sphere(self.vObjects[self.sourceIndex].vertex, 4)
        sc.doc.Objects.AddSphere(sphere)
        
    def Update(self):
        source = self.vObjects[self.sourceIndex]
        
        self.targetIndex = random.choice(self.targets)
        self.targets.Remove(self.targetIndex)
        
        searchNetwork = geo.AStarMesh(self.mesh, self.sourceIndex, self.targetIndex)
        result, path = searchNetwork.AStarPathFinder() 
        
        if result:
            self.vObjects[self.targetIndex].d = len(path)
    
    def UpdateDisplay(self):
        #for id in self.ids:
        #    sc.doc.Objects.Delete(id, True)
        
        #for i, pt in enumerate(self.path):
        #    sphere = rg.Sphere(pt, .8)
        #    self.ids.append(sc.doc.Objects.AddSphere(sphere, self.attr))
        
        #self.ids.append(sc.doc.Objects.AddMesh(self.mesh))
        
        self.vObjects[self.targetIndex].UpdateDisplay()
        
        #for vObj in self.vObjects:
        #    vObj.UpdateDisplay()

class meshObj():
    def __init__(self):
        self.attr = util.BasicAttr()
        
        
        
        self.mesh = rg.Mesh()
        v0 = rg.Point3f(10,0,40)
        v1 = rg.Point3f(10,100,40)
        v2 = rg.Point3f(50,0,40)
        v3 = rg.Point3f(50,100,40)
        v4 = rg.Point3f(90,0,40)
        v5 = rg.Point3f(90,100,40)
        
        i0 = self.mesh.Vertices.Add(v0)
        i1 = self.mesh.Vertices.Add(v1)
        i2 = self.mesh.Vertices.Add(v2)
        i3 = self.mesh.Vertices.Add(v3)
        i4 = self.mesh.Vertices.Add(v4)
        i5 = self.mesh.Vertices.Add(v5)
        
        self.mesh.Faces.AddFace(i0, i1, i3, i2)
        self.mesh.Faces.AddFace(i2, i3, i5, i4)
        self.mesh = rs.coercemesh(r'77ac5660-bd0a-4946-8299-e4022a5e3849')
        self.mesh.Compact()
        
        self.vObjects = []
        for i, v in enumerate(self.mesh.Vertices):
            self.vObjects.append(vObject(self, v, i))
        
        self.meshID = None
        self.aVel = 0
        self.aAcc = .01
        if False:
            self.bump = Bump(self)
            
            self.links = []
            for i in range(len(self.vObjects)):
                for j in range(i+1, len(self.vObjects)):
                    if (self.vObjects[i].pos-self.vObjects[j].pos).Length < 10:
                        self.links.append(Link(self.vObjects[i], self.vObjects[j]))
    def Update(self, t):
        if t%15 == 0:
            self.aVel *= 0
        if t < 60:
            self.aAcc = .001
        else:
            self.aAcc = -.001
        
        t = t%60
        
        if t < 15:
            self.FoldMeshFace(1, 0)
            self.FoldMeshFace(2, 1)
            self.FoldMeshFace(3, 2)
            self.FoldMeshFace(4, 3)
        elif t >=15 and t < 30:
            self.FoldMeshFace(6, 5)
            self.FoldMeshFace(7, 6)
            self.FoldMeshFace(8, 7)
            self.FoldMeshFace(9, 8)
        elif t >=30 and t < 45:
            self.FoldMeshFace(11, 10)
            self.FoldMeshFace(12, 11)
            self.FoldMeshFace(13, 12)
            self.FoldMeshFace(14, 13)
        elif t >=45 and t < 60:
            self.FoldMeshFace(16, 15)
            self.FoldMeshFace(17, 16)
            self.FoldMeshFace(18, 17)
            self.FoldMeshFace(19, 18)
        
        
    def FoldMeshFace(self, faceIndex, fixedFaceIndex):
        self.aVel += self.aAcc
        
        #Get Axis between Faces
        faceEdges = self.mesh.TopologyEdges.GetEdgesForFace(faceIndex)
        fixedFaceEdges = self.mesh.TopologyEdges.GetEdgesForFace(fixedFaceIndex)
        
        axisCrv = None
        for faceEdge in faceEdges:
            if faceEdge in fixedFaceEdges:
                axisCrv = faceEdge
                break
        
        if axisCrv is None:
            print "Faces are not adjacent"
            return None
        
        edgeCrv = self.mesh.TopologyEdges.EdgeLine(axisCrv)
        axis = edgeCrv.From - edgeCrv.To
        
        #Create xform
        xform = rg.Transform.Rotation(self.aVel, axis, edgeCrv.From)
        
        #Get child faces
        childFaces = self.GetChildren(faceIndex, fixedFaceIndex)
        
        facePtIndices = self.mesh.Faces.GetTopologicalVertices(faceIndex)
        fixedFacePtIndices = self.mesh.Faces.GetTopologicalVertices(fixedFaceIndex)
        
        movingIndices = []
        for each in facePtIndices:
            if each not in fixedFacePtIndices:
                movingIndices.append(each)
        
        for child in childFaces:
            newIndices = self.mesh.Faces.GetTopologicalVertices(child)
            for each in newIndices:
                if each not in movingIndices:
                    movingIndices.append(each)
        
        for index in movingIndices:
            pt = self.mesh.Vertices[index]
            pt.Transform(xform)
            self.mesh.Vertices[index] = pt
    
    
    def GetChildren(self, faceIndex, fixedFaceIndex):
        facesToCheck = [(faceIndex, fixedFaceIndex)]
        children = []
        
        safety = 0
        while len(facesToCheck) > 0:
            safety += 1
            if safety > 100:
                print "SAFETY 1"
                break
            
            currentItem = facesToCheck[-1]
            facesToCheck.remove(currentItem)
            theseChildren = self.GetChildFaces(currentItem[0], currentItem[1])
            for child in theseChildren:
                children.append(child)
                facesToCheck.append((child,currentItem[0]) )
        return children
    def GetChildFaces(self, faceIndex, fixedFaceIndex):
        adFaces = list(self.mesh.Faces.AdjacentFaces(faceIndex))
        childFaces = []
        if fixedFaceIndex in adFaces:
            adFaces.Remove(fixedFaceIndex)
        return adFaces
        
        
    
    def FoldMeshFaceRandom(self, faceIndex):
        facePts = list(face)
        self.aVel += self.aAcc
        face = self.mesh.Faces[faceIndex]
        axis = self.mesh.Vertices[edge[0]]-self.mesh.Vertices[edge[1]]
        rotCenter = self.mesh.Vertices[edge[0]]
        xform = rg.Transform.Rotation(self.aVel, axis, rotCenter)
        
        movingPts = []
        
        for facePt in facePts:
            if facePt not in edge:
                movingPts.append(facePt)
        
        for eachPt in movingPts:
            pt = self.mesh.Vertices[eachPt]
            pt.Transform(xform)
            self.mesh.Vertices[eachPt] = pt
    
    def Update2(self, t):
        target = self.mesh.Vertices[self.bump.index]
        self.strength = self.bump.val
        for i in range(self.mesh.Vertices.Count):
            d = rs.Distance(target, self.mesh.Vertices[i])
            self.MoveVertexAlongNormal(i, d)
        
        #self.bump.Update()
        
        for link in self.links:
            link.Seperate(3)
        
        for obj in self.vObjects:
            obj.ApplySpring()
        for obj in self.vObjects:
            obj.UpdatePosition()
        
        if False:
            for i, face in enumerate(self.mesh.Faces):
                if self.FaceArea(face) > 30:
                    self.SubdivideTriangle(i)
        
        newIndices = self.AdaptivelySubdivide(self.mesh, 7)
        for i in newIndices:
            v = self.mesh.Vertices[i]
            self.vObjects.append(vObject(self, v, i))
        
        for obj in self.vObjects:
            obj.UpdateNeighbors()
        
        self.ShrinkFaces()
        
        self.links = []
        for i in range(len(self.vObjects)):
            for j in range(i+1, len(self.vObjects)):
                if (self.vObjects[i].pos-self.vObjects[j].pos).Length < 10:
                    self.links.append(Link(self.vObjects[i], self.vObjects[j]))
    
    def UpdateDisplay(self):
        if self.meshID: sc.doc.Objects.Delete(self.meshID, True)
        self.meshID = sc.doc.Objects.AddMesh(self.mesh)
    
    def FaceArea(self, face):
        totalArea = 0
        tri0 = []
        tri0.append(rg.Point3d(self.mesh.Vertices[face.A]))
        tri0.append(rg.Point3d(self.mesh.Vertices[face.B]))
        tri0.append(rg.Point3d(self.mesh.Vertices[face.C]))
        tri0.append(tri0[0])
        pline = rg.PolylineCurve(tri0)
        am = rg.AreaMassProperties.Compute(pline)
        totalArea += am.Area
        
        if face.IsQuad == True:
            tri1 = []
            tri1.append(rg.Point3d(self.mesh.Vertices[face.C]))
            tri1.append(rg.Point3d(self.mesh.Vertices[face.D]))
            tri1.append(rg.Point3d(self.mesh.Vertices[face.A]))
            tri1.append(tri1[0])
            pline = rg.PolylineCurve(tri1)
            am = rg.AreaMassProperties.Compute(pline)
            if am:
                totalArea += am.Area
        return totalArea
    
    def SubdivideTriangle(self, faceIndex):
        i0 = self.mesh.Faces[faceIndex].A
        i1 = self.mesh.Faces[faceIndex].B
        i2 = self.mesh.Faces[faceIndex].C
        
        n0 = self.mesh.Normals[i0]
        n1 = self.mesh.Normals[i1]
        n2 = self.mesh.Normals[i2]
        
        v0 = rg.Point3d(self.mesh.Vertices[i0])
        v1 = rg.Point3d(self.mesh.Vertices[i1])
        v2 = rg.Point3d(self.mesh.Vertices[i2])
        
        cn = (n0+n1+n2)/3
        ni = self.mesh.Normals.Add(cn)
        
        c = rg.Point3d((v0.X+v1.X+v2.X)/3, (v0.Y+v1.Y+v2.Y)/3, (v0.Z+v1.Z+v2.Z)/3)
        ci = self.mesh.Vertices.Add(c)
        
        self.vObjects.append(vObject(self, c, ci))
        
        self.mesh.Faces.AddFace(i0, i1, ci)
        self.mesh.Faces.AddFace(i1, i2, ci)
        self.mesh.Faces.AddFace(i2, i0, ci)
        
        self.mesh.Faces.DeleteFaces([faceIndex])
        self.mesh.Normals.ComputeNormals()
        self.mesh.Compact()
    
    def SubdivideQuad(self, faceIndex):
        i0 = self.mesh.Faces[faceIndex].A
        i1 = self.mesh.Faces[faceIndex].B
        i2 = self.mesh.Faces[faceIndex].C
        i3 = self.mesh.Faces[faceIndex].D
        
        #n0 = self.mesh.Normals[i0]
        #n1 = self.mesh.Normals[i1]
        #n2 = self.mesh.Normals[i2]
        #n3 = self.mesh.Normals[i3]
        
        v0 = rg.Point3d(self.mesh.Vertices[i0])
        v1 = rg.Point3d(self.mesh.Vertices[i1])
        v2 = rg.Point3d(self.mesh.Vertices[i2])
        v3 = rg.Point3d(self.mesh.Vertices[i3])
        
        #cn = (n0+n1+n2+n3)/4
        #ni = self.mesh.Normals.Add(cn)
        
        c = rg.Point3d((v0.X+v1.X+v2.X+v3.X)/4, (v0.Y+v1.Y+v2.Y+v3.Y)/4, (v0.Z+v1.Z+v2.Z+v3.Z)/4)
        ci = self.mesh.Vertices.Add(c)
        
        i01 = geo.PointBetweenPoints(v0, v1, .5)
        i12 = geo.PointBetweenPoints(v1, v2, .5)
        i23 = geo.PointBetweenPoints(v2, v3, .5)
        i30 = geo.PointBetweenPoints(v3, v0, .5)
        
        self.mesh.Faces.AddFace(i0, i01, ci, i30)
        self.mesh.Faces.AddFace(i1, i12, ci, i01)
        self.mesh.Faces.AddFace(i2, i23, ci, i12)
        self.mesh.Faces.AddFace(i2, i30, ci, i23)
        
        self.mesh.Faces.DeleteFaces([faceIndex])
        #self.mesh.Normals.ComputeNormals()
        self.mesh.Compact()
    
    def MoveVertexAlongNormal(self, i, d):
        vertex = self.mesh.Vertices[i]
        
        v = rg.Point3d(vertex)
        vec = rg.Vector3d(self.mesh.Normals[i])
        vec = rg.Vector3d(0,0,1)
        vec.Unitize()
        
        val = util.Remap(d, 0, 20, math.pi, 0)
        val = 1-(math.cos(val)+1)*.5        
        
        vec *= val*2
        
        v += vec
        
        self.mesh.Vertices[i] = rg.Point3f(v.X, v.Y, v.Z)
    
    def AdaptivelySubdivide(self, mesh, edgeLength):
        newIndices = []
        for i in range(mesh.TopologyEdges.Count-1):
            line = mesh.TopologyEdges.EdgeLine(i)
            if line.Length > edgeLength:
                mesh.TopologyEdges.SplitEdge(i, .5)
                newIndices.append(len(mesh.Vertices)-1)
        return newIndices
    
    def ShrinkFaces(self):
        self.meshDisplay = rg.Mesh()
        v0 = .05
        v1 = 1-v0*2
        for i, face in enumerate(self.mesh.Faces):
            pt0 = self.mesh.PointAt(i, v0, v1, v0, 0)
            pt1 = self.mesh.PointAt(i, v0, v0, v1, 0)
            pt2 = self.mesh.PointAt(i, v1, v0, v0, 0)
            i0 = self.meshDisplay.Vertices.Add(pt0)
            i1 = self.meshDisplay.Vertices.Add(pt1)
            i2 = self.meshDisplay.Vertices.Add(pt2)
            self.meshDisplay.Faces.AddFace(i0,i1,i2)

class Bump():
    def __init__(self, system):
        self.system = system
        self.index = random.randint(0, self.system.mesh.Vertices.Count-1)
        self.index = 200
        self.val = 0
        self.age = 0
    
    def Update(self):
        self.age += 1
        
        self.val = util.Remap(self.age, 0, 10, math.pi, 0)
        self.val = 1-(math.cos(self.val)+1)*.5        


####
def main():
    skNum = (datetime.date.today()-datetime.date(2020, 03, 29)).days + 201
    if int(skNum) > int(os.path.splitext(os.path.basename(__file__))[0]):
        print "!!!!SAVE THE SKETCH WITH A NEW NAME!!!!"
    
    rs.UnselectAllObjects()
    
    init_time = time.time()
    version = 'b'   
    anim = mp4.Animation(os.path.splitext(os.path.basename(__file__))[0] + version)
    numFrames = 120
    numPasses = 100
    anim.fps = 30
    
    td = TempDisplay()
    display = HUD(os.path.splitext(os.path.basename(__file__))[0], numFrames)
    s = Scene()
    ################################
    #SETUP
    mObj = meshObj()
    
    ################################
    for i in range(numFrames):
        start_time = time.time()
        print "Frame {}".format(i)
        if sc.escape_test(False): anim.Cleanup(); return
        ################################
        #MAIN LOOP
        #if i%10 == 0:
        #    mObj.MessUp()
        mObj.Update(i)
        mObj.UpdateDisplay()
        
        ################################
        #HUD
        display.UpdateParam1('faces: ' + str(len(mObj.mesh.Faces)))
        display.UpdateParam2('vobjs: ' + str(len(mObj.vObjects)))
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