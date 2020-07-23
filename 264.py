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
class Dot():
    def __init__(self, system):
        self.system = system
        self.pos = rg.Point3d(random.uniform(10,90), random.uniform(10,90), random.uniform(10,90))
        self.vel = rg.Vector3d(random.uniform(-2, 2),random.uniform(-2, 2),random.uniform(-2, 2))
        self.vel.Unitize()
        self.vel *= 5
        self.acc = rg.Point3d(50,50,50) - self.pos
        self.acc.Unitize()
        self.acc *= .1
        
        self.vel += self.acc
        self.id = None
        self.ids = []
        self.age = 0
        
        self.prevPlane = rg.Plane.WorldXY
        self.xform = None
        
        #Attr
        self.attr = rc.DocObjects.ObjectAttributes()
        self.attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        self.grad = color.GetGradient(2)
        self.attr.ObjectColor = color.GradientOfColors(self.grad, 0)
        self.attr.MaterialSource = rc.DocObjects.ObjectMaterialSource.MaterialFromObject
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = self.attr.ObjectColor
        self.mat.CommitChanges()
        self.attr.MaterialIndex = index
        
        size = .5
        self.pt0 = rg.Point3f(0, size, 0)
        self.pt1 = rg.Point3f(-size/2, 0, 0)
        self.pt2 = rg.Point3f(size/2, 0, 0)
        self.mesh = self.InitTriangle()
    
    def InitTriangle(self):
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
        mesh = rg.Mesh()
        
        i0 = mesh.Vertices.Add(self.pt0)
        i1 = mesh.Vertices.Add(self.pt1)
        i2 = mesh.Vertices.Add(self.pt2)
        mesh.Faces.AddFace(i0, i1, i2)
        mesh.Transform(xform)
        return mesh
    
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
        self.mesh.Transform(self.xform)
    
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
        #print self.vel.Length
        #self.CalcPrimaryAxis()
        #self.CheckForFloorCollision()
        self.UpdatePosition()
        self.UpdateDisplay()
        
    def UpdatePosition(self):
        self.acc = self.pos - rg.Point3d(50,50,50)
        if self.acc.Length > 10:
            self.acc.Reverse()
        self.acc.Unitize()
        self.acc *= 5
        
        rand = geo.RandomVector3d(1)
        self.acc += rand
        
        self.vel += self.acc
        self.pos += self.vel
        
        self.MoveTriangle()
        #xform = rg.Transform.Translation(self.vel)
        #self.box.Transform(xform)
        #self.boxBrep.Transform(xform)
    
    def UpdateDisplay(self):
        self.attr.ObjectColor = color.GradientOfColors(self.grad, util.Remap(self.vel.Length, 3, 7, 0, 1))
        self.attr.MaterialSource = rc.DocObjects.ObjectMaterialSource.MaterialFromObject
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = self.attr.ObjectColor
        self.mat.CommitChanges()
        self.attr.MaterialIndex = index
        
        #if self.id: sc.doc.Objects.Delete(self.id, True)
        for id in self.ids:
            sc.doc.Objects.Delete(id, True)
        
        if self.id is None:
            self.id = sc.doc.Objects.AddMesh(self.mesh, self.attr)
        else:
            self.id = sc.doc.Objects.Transform(self.id, self.xform, True)
        
        #self.id = sc.doc.Objects.AddMesh(self.mesh, self.attr)
        
        
    
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
    
class ParticleSystem():
    def __init__(self):
        self.dots = []
        self.time = 0
        self.links = []
        for i in range(10000):
            self.dots.append(Dot(self))
        
    def Update(self, time):
        self.time = time
        
        for dot in self.dots:
            dot.Update()
        
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
        
    
####
def main():
    skNum = (datetime.date.today()-datetime.date(2020, 03, 29)).days + 201
    if int(skNum) > int(os.path.splitext(os.path.basename(__file__))[0]):
        print "!!!!SAVE THE SKETCH WITH A NEW NAME!!!!"
    
    rs.UnselectAllObjects()
    
    init_time = time.time()
    version = 'c'   
    anim = mp4.Animation(os.path.splitext(os.path.basename(__file__))[0] + version)
    numFrames = 150
    numPasses = 100
    anim.fps = 30
    
    td = TempDisplay()
    display = HUD(os.path.splitext(os.path.basename(__file__))[0], numFrames)
    s = Scene()
    ################################
    #SETUP
    #bSystem = BoxSystem()
    pSystem = ParticleSystem()
    
    ################################
    for i in range(numFrames):
        start_time = time.time()
        print "Frame {}".format(i)
        if sc.escape_test(False): anim.Cleanup(); return
        ################################
        #MAIN LOOP
        #bSystem.Update(i)
        pSystem.Update(i)
        
        
        ################################
        #HUD
        #display.UpdateParam1('boxes: ' + str(len(bSystem.boxes)))
        #display.UpdateParam2('links: ' + str(len(bSystem.links)))
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