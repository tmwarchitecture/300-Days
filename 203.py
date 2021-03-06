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
class System():
    def __init__(self):
        self.balls = []
        for i in range(1000):
            self.balls.append(Ball())
    def Update(self):
        for ball in self.balls:
            ball.Update()

class Ball():
    def __init__(self):
        self.radius = 2
        
        self.vel = rg.Vector3d(random.uniform(-1,1), random.uniform(-1,1), random.uniform(-.5,1))
        self.vel.Unitize()
        self.vel *= random.uniform(2, 5)
        self.acc = rg.Vector3d(0,0,-.3)
        
        self.attr = rc.DocObjects.ObjectAttributes()
        self.attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        self.attr.ObjectColor = color.ColorBetweenColors(drawing.Color.DeepSkyBlue, drawing.Color.LimeGreen, random.uniform(0,1))
        self.attr.MaterialSource = rc.DocObjects.ObjectMaterialSource.MaterialFromObject
        
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = self.attr.ObjectColor
        self.mat.CommitChanges()        
        
        self.attr.MaterialIndex = index
        
        #self.pos =  geo.RandomPoint(self.radius, 100-self.radius, self.radius, 100-self.radius, self.radius, 100-self.radius)
        self.pos =  rg.Point3d(50,50,80)
        #self.sphere = rg.Sphere(self.pos, self.radius)
        self.xSize = rg.Interval(-self.radius*.5, self.radius*.5)
        self.ySize = rg.Interval(-self.radius*.125, self.radius*.125)
        self.zSize = rg.Interval(-self.radius, self.radius)
        
        #self.plane = rg.Plane.WorldXY
        #self.plane.Origin = self.pos
        self.plane = rg.Plane(self.pos, self.vel)
        #self.plane.XAxis = self.vel
        
        self.box = rg.Box(self.plane, self.xSize, self.ySize, self.zSize)
        self.boxID = sc.doc.Objects.AddBox(self.box, self.attr)
        #self.sphereID = sc.doc.Objects.AddSphere(self.sphere, self.attr)
    
    def Update(self):
        self.vel += self.acc
        futurePos = self.pos + self.vel
        
        
        if futurePos.X < self.radius:
            self.vel.X *= -1
        if futurePos.Y < self.radius:
            self.vel.Y *= -1
        if futurePos.Z < self.radius:
            self.vel.Z *= -1
            #Friction
            self.vel *= .7
        if futurePos.X > 100-self.radius:
            self.vel.X *= -1
        if futurePos.Y > 100-self.radius:
            self.vel.Y *= -1
        if futurePos.Z > 100-self.radius:
            self.vel.Z *= -1
        
        self.zSize = rg.Interval(0, util.Remap(self.vel.Length, 2, 5, self.radius*.125, self.radius*4))
        self.pos += self.vel
        #self.plane.Origin = self.pos
        self.plane = rg.Plane(self.pos, self.vel)
        self.box = rg.Box(self.plane, self.xSize, self.ySize, self.zSize)
        #self.sphere = rg.Sphere(self.pos, self.radius)
        
        sc.doc.Objects.Delete(self.boxID, True)
        self.boxID = sc.doc.Objects.AddBox(self.box, self.attr)
        
        #sc.doc.Objects.Replace(self.sphere, self.sphereID)

####
def main():
    skNum = (datetime.date.today()-datetime.date(2020, 03, 28)).days + 201
    if int(skNum) > int(os.path.splitext(os.path.basename(__file__))[0]):
        print "!!!!SAVE THE SKETCH WITH A NEW NAME!!!!"
    
    rs.UnselectAllObjects()
    
    init_time = time.time()
    version = 'a'   
    anim = mp4.Animation(os.path.splitext(os.path.basename(__file__))[0] + version)
    numFrames = 200
    numPasses = 200
    anim.fps = 30
    
    td = TempDisplay()
    display = HUD(os.path.splitext(os.path.basename(__file__))[0], numFrames)
    s = Scene()
    ################################
    #SETUP
    ballSystem = System()
    
    ################################
    for i in range(numFrames):
        start_time = time.time()
        print "Frame {}".format(i)
        if sc.escape_test(False): anim.Cleanup(); return
        ################################
        #MAIN LOOP
        
        ballSystem.Update()
        
        ################################
        #HUD
        display.UpdateParam1('n: ' + str(len(ballSystem.balls)))
        #display.UpdateParam2('y: ' + str(ball.pos.Y))
        #display.UpdateParam3('z: ' + str(ball.pos.Z))
        display.UpdateScaleBar()
        ################################
        sc.doc.Views.Redraw()
        display.Update(i)
        anim.AddFrame(numberOfPasses = numPasses)
        
        #if result:
        #    break
        ################################
        #Framerate
        frameTime = time.time() - start_time
        timeLeft = (numFrames - i) * frameTime
        timeLeftStr = str(datetime.timedelta(seconds=timeLeft))
        print "Time remaining: {}".format(timeLeftStr)
    
    frameTime = time.time() - init_time
    timeLeftStr = str(datetime.timedelta(seconds=frameTime))
    print "Total Time: {}".format(timeLeftStr)
    
    if os.path.isdir(r"D:\Files\Work\LIBRARY\06_RHINO\10_Python\300 DAYS\anim"):
        anim.Create(r"D:\Files\Work\LIBRARY\06_RHINO\10_Python\300 DAYS\anim", frames2Keep = [i/2, i-1])
    else:
        anim.Create(r"C:\Tim\300 Days\anim", frames2Keep = [i/2, i-1])

if __name__ == "__main__":
    main()  
