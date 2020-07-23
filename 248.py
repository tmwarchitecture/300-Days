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
class System():
    def __init__(self):
        self.particles = []
        self.boundary = rg.Box(rg.Plane.WorldXY, rg.Interval(-25,125), rg.Interval(-25,125), rg.Interval(0,100))
        self.boundary = self.boundary.ToBrep()
        
        self.time = 0
        self.ids = []
        
        self.attr = rc.DocObjects.ObjectAttributes()
        self.attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        self.attr.MaterialSource = rc.DocObjects.ObjectMaterialSource.MaterialFromObject
        
        grad = color.GetGradient(1)
        self.attr.ObjectColor = color.GradientOfColors(grad, 0)
        self.attr.ObjectColor = drawing.Color.White
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = self.attr.ObjectColor
        self.mat.CommitChanges()
        self.attr.MaterialIndex = index
        
        self.attr = rc.DocObjects.ObjectAttributes()
        self.attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        self.attr.MaterialSource = rc.DocObjects.ObjectMaterialSource.MaterialFromObject
        
        attr = self.attr.Duplicate()
        grad = color.GetGradient(0)
        col1 = color.GradientOfColors(grad, util.Remap(self.time, 0, 150, 0,1))
        
        attr.ObjectColor = col1
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = attr.ObjectColor
        self.mat.CommitChanges()
        attr.MaterialIndex = index
        
        self.particles = []
        
        #for i in range(2):
        self.particles.append(Particle(self, rg.Point3d(25, 50, 80), attr))
        self.particles.append(Particle(self, rg.Point3d(75, 50, 80), attr))
    
    def Update(self, time):
        for id in self.ids:
            if id:
                sc.doc.Objects.Delete(id, True)
        self.time = time
        #################################
        attr = self.attr.Duplicate()
        grad = color.GetGradient(0)
        col1 = color.GradientOfColors(grad, util.Remap(self.time, 0, 150, 0,1))
        attr.ObjectColor = col1
        
        attr.ObjectColor = col1
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = attr.ObjectColor
        self.mat.CommitChanges()
        attr.MaterialIndex = index
        
        safety = 0
        while True:
            safety += 1
            if safety > 20: 
                print "Safety"
                break
            newParticle = Particle(self, geo.RandomPoint(10,90,10,90,80,80), attr)
            if newParticle.hit == False:
                self.particles.append(newParticle)
                break
        
        for particle in self.particles:
            particle.Update()
    
class Particle():
    def __init__(self, system, pt, attr):
        self.pos = pt
        self.vel = rg.Vector3d(0,0,-1)
        self.speed = 4
        self.vel *= self.speed
        self.system = system
        self.size = 6
        self.prevPos = None
        self.union = None 
        self.hit = False
        self.ids = []
        self.age = 0
        self.attr = attr
        
        plane = rg.Plane(self.pos, geo.RandomVector3d(1))
        self.brep = rg.Box(plane, rg.Interval(-self.size/2, self.size/2),rg.Interval(-self.size/2, self.size/2),rg.Interval(-self.size/2, self.size/2))
        self.brep = self.brep.ToBrep()
        
        closestD = None
        for particle in self.system.particles:
            if particle is self: continue
            pt0, pt1 = BrepProximity(self.brep, particle.brep)
            d = (pt0-pt1).Length
            if d < closestD or closestD is None:
                closestD = d
        if closestD < self.speed*2:
            self.hit = True
        
    def Update(self):
        for id in self.ids:
            if id:
                sc.doc.Objects.Delete(id, True)
        self.age += 1
        
        #Previous positions
        self.prevPos = rg.Point3d(self.pos)
        #######################################################
        futureXform = rg.Transform.Translation(self.vel)
        futureObj = self.brep.Duplicate()
        futureObj.Transform(futureXform)
        
        closestD = None
        for particle in self.system.particles:
            if particle is self: continue
            pt0, pt1 = BrepProximity(self.brep, particle.brep)
            d = (pt0-pt1).Length
            if d < closestD or closestD is None:
                closestD = d
        
        pt0, pt1 = BrepProximity(self.brep, self.system.boundary)
        d = (pt0-pt1).Length
        if d < closestD or closestD is None:
            closestD = d
        
        if closestD < 2:
            self.vel *= 0
        else:
            self.vel.Unitize()
            self.vel *= self.speed
        
        self.pos += self.vel
        xform = rg.Transform.Translation(self.vel)
        if self.pos.Z < 5:
            hit = True
        
        #######################################################
        xform = rg.Transform.Translation(self.vel)
        self.brep.Transform(xform)
        
        self.ids.append(sc.doc.Objects.AddBrep(self.brep, self.attr))

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
    pSystem = System()
    
    ################################
    for i in range(numFrames):
        start_time = time.time()
        print "Frame {}".format(i)
        if sc.escape_test(False): anim.Cleanup(); return
        ################################
        #MAIN LOOP
        pSystem.Update(i)
        
        
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