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
class Box():
    def __init__(self, system):
        self.system = system
        self.pos = rg.Point3d(random.uniform(10,90), random.uniform(10,90), 90)
        self.vel = rg.Vector3d(0,0,0)
        self.acc = rg.Vector3d(0,0,-.5)
        self.ids = []
        self.width = random.uniform(1, 9)
        self.depth = random.uniform(1, 9)
        self.height = random.uniform(1, 9)
        self.plane = rg.Plane.WorldXY
        self.plane.Origin = self.pos
        xSize = rg.Interval(-self.width/2, self.width/2)
        ySize = rg.Interval(-self.depth/2, self.depth/2)
        zSize = rg.Interval(-self.height/2, self.height/2)
        self.box = rg.Box(self.plane, xSize, ySize, zSize)
        self.boxBrep = self.box.ToBrep()
        self.id = sc.doc.Objects.AddBrep(self.boxBrep)
        self.vel += self.acc
        self.futurePos = rg.Point3d.Add(self.pos, self.vel)
        self.attr = rc.DocObjects.ObjectAttributes()
        self.attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        grad = color.GetGradient(1)
        self.attr.ObjectColor = color.GradientOfColors(grad, random.uniform(0,1))
        self.attr.MaterialSource = rc.DocObjects.ObjectMaterialSource.MaterialFromObject
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = self.attr.ObjectColor
        self.mat.CommitChanges()
        self.attr.MaterialIndex = index
        
    def CalcFuturePos(self):
        tempVel = rg.Vector3d(self.vel)
        tempVel += self.acc
        self.futurePos = rg.Point3d.Add(self.pos, tempVel)
    
    def CheckForCollision(self):
        self.CalcFuturePos()
        
        x0 = self.futurePos.X+self.box.X.Min
        x1 = self.futurePos.X+self.box.X.Max
        y0 = self.futurePos.Y+self.box.Y.Min
        y1 = self.futurePos.Y+self.box.Y.Max
        z0 = self.futurePos.Z+self.box.Z.Min
        z1 = self.futurePos.Z+self.box.Z.Max
        
        if z0 < 0:
            reaction = rg.Vector3d(0,0,abs(z0))
            self.vel += reaction
        
        for otherBox in self.system.boxes:
            if otherBox is self: continue
            self.BoxBoxCollision(otherBox)
        
    def BoxBoxCollision(self, otherBox):
        otherBox.CalcFuturePos()
        self.CalcFuturePos()
        
        x0 = self.futurePos.X+self.box.X.Min
        x1 = self.futurePos.X+self.box.X.Max
        y0 = self.futurePos.Y+self.box.Y.Min
        y1 = self.futurePos.Y+self.box.Y.Max
        z0 = self.futurePos.Z+self.box.Z.Min
        z1 = self.futurePos.Z+self.box.Z.Max
        
        x0b = otherBox.futurePos.X+otherBox.box.X.Min
        x1b = otherBox.futurePos.X+otherBox.box.X.Max
        y0b = otherBox.futurePos.Y+otherBox.box.Y.Min
        y1b = otherBox.futurePos.Y+otherBox.box.Y.Max
        z0b = otherBox.futurePos.Z+otherBox.box.Z.Min
        z1b = otherBox.futurePos.Z+otherBox.box.Z.Max
        
        xb, xd0, xd1 = self.OverlappingIntervals(x0,x1, x0b, x1b)
        yb, yd0, yd1 = self.OverlappingIntervals(y0,y1, y0b, y1b)
        zb, zd0, zd1 = self.OverlappingIntervals(z0,z1, z0b, z1b)
        if xb == True and yb == True and zb == True:
            reaction = rg.Vector3d(0,0,zd0)
            self.vel += reaction
            self.attr.ObjectColor = drawing.Color.FromArgb(255,0,0)
            index = sc.doc.Materials.Add()
            self.mat = sc.doc.Materials[index]
            self.mat.DiffuseColor = self.attr.ObjectColor
            self.mat.CommitChanges()
            self.attr.MaterialIndex = index
        
    def OverlappingIntervals(self, a0, a1, b0, b1):
        if a1 > b0 and b1 > a0:
            return True, max(a1,b1)-min(a0,b0), a1-b0
        else:
            return False, 0, 0
    
    def Update(self):
        self.CheckForCollision()
        self.UpdatePosition()
        self.UpdateDisplay()
    
    def UpdatePosition(self):
        self.vel += self.acc
        self.pos += self.vel
        
        xform = rg.Transform.Translation(self.vel)
        self.box.Transform(xform)
        self.boxBrep.Transform(xform)
    
    def UpdateDisplay(self):
        if self.id: sc.doc.Objects.Delete(self.id, True)
        self.id = sc.doc.Objects.AddBrep(self.boxBrep, self.attr)
    
class Link():
    def __init__(self, a, b):
        self.objA = a
        self.objB = b
        self.objs = [a,b]
   
class BoxSystem():
    def __init__(self):
        self.boxes = []
        self.boxes.append(Box(self))
        self.time = 0
        self.links = []
        
    
    def Update(self, time):
        self.time = time
        for box in self.boxes:
            box.Update()
        
        if self.time %3==0:
            self.boxes.append(Box(self))
        
        self.links = []
        for i in range(len(self.boxes)):
            for j in range(i+1, len(self.box)):
                self.links.append(Link(self.boxes[i], self.boxes[j]))
        if self.time == 20:
            print
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
    bSystem = BoxSystem()
    
    ################################
    for i in range(numFrames):
        start_time = time.time()
        print "Frame {}".format(i)
        if sc.escape_test(False): anim.Cleanup(); return
        ################################
        #MAIN LOOP
        bSystem.Update(i)
        
        
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