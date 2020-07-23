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
        self.particles = []
        
        self.boundary = rg.Box(rg.Plane.WorldXY, rg.Interval(0,100), rg.Interval(0,100), rg.Interval(0,100))
        self.boundary = self.boundary.ToBrep()
        
        initPlane = rg.Plane.WorldXY
        initPlane.Origin = rg.Point3d(50,50,50)
        
        self.majorBrep = rg.Brep()
        self.breps = []
        #self.pn = perlin.TileableNoise()
        
        self.openPlanes = []
        self.deadPlanes = []
        self.nextRoundPlanes = [initPlane]
        self.modules = []
        
        self.time = 0
        
        self.attr = rc.DocObjects.ObjectAttributes()
        self.attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        self.attr.MaterialSource = rc.DocObjects.ObjectMaterialSource.MaterialFromObject
        
        grad = color.GetGradient(5)
        self.attr.ObjectColor = color.GradientOfColors(grad, 0)
        self.attr.ObjectColor = drawing.Color.White
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = self.attr.ObjectColor
        self.mat.CommitChanges()
        self.attr.MaterialIndex = index
        
        self.balls = []
        for i in range(10):
            self.balls.append(Ball())
        #self.ball = Ball()
        
        self.voxels = []
        self.size = 10
        for i in range(0, 10):
            for j in range(0,10):
                for k in range(0,10):
                    s = 10
                    thisPlane = rg.Plane(rg.Point3d(i*s+(s/2), j*s+(s/2), k*s+(s/2)), rg.Vector3d(0,0,1))
                    self.openPlanes.append(thisPlane)
        
        for plane in self.openPlanes:
            self.voxels.append(Module(self, self.size, plane))
        
        for i in range(0):
            self.voxels.append(Module(self, self.size, 0))
            self.openPlanes += self.nextRoundPlanes
        self.nextRoundPlanes = []
    
    def Update(self, time):
        self.time = time
        #self.pn.randomize()
        for ball in self.balls:
            ball.Update()
    
    def UpdateDisplay(self):
        for voxel in self.voxels:
            voxel.UpdateDisplay()
    
    def AddModule(self, plane, size):
        safety = 0
        while True:
            safety += 1
            if safety > 10:
                self.deadPlanes.append(plane)
                return
            mod = Module(size)
            case = random.randint(0,2)
            if self.time < 5:
                case = 0
            if case == 0:
                mod.CreateStraight()
            elif case == 1:
                mod.CreateAngle()
            elif case == 2:
                mod.CreateT()
            
            originPlane = rg.Plane.WorldXY
            rot = random.randint(0,3) * 90
            #rot = random.uniform(0,360)
            rotXform = rg.Transform.Rotation(math.radians(rot), rg.Vector3d(0,0,1), rg.Point3d(0,0,0))
            originPlane.Transform(rotXform)
            xform = rg.Transform.PlaneToPlane(originPlane, plane)
            mod.geo.Transform(xform)
            
            results = rg.Intersect.Intersection.BrepBrep(mod.geo, self.boundary, sc.doc.ModelAbsoluteTolerance)
            if len(results[1]) == 0:
                results = rg.Intersect.Intersection.BrepBrep(mod.geo, self.majorBrep, sc.doc.ModelAbsoluteTolerance)
                if len(results[1]) < 2:
                    sc.doc.Objects.AddBrep(mod.geo, self.attr)
                    ends = mod.planeEnds[:]
                    for end in ends:
                        end.Transform(xform)
                    self.nextRoundPlanes += ends
                    self.majorBrep.Append(mod.geo)
                    return
    
    def AddModule2(self, plane, size):
        numObjects = 1
        if random.randint(0,4) == 0:
            numObjects = 2
        
        for i in range(numObjects):
            #Rotate base plane
            plane.Rotate(math.radians(random.uniform(0,360)), plane.Normal)
            
            #Construct new arc
            length = 4
            vec = plane.Normal
            vec *= length
            pt0 = plane.Origin
            pt1 = rg.Point3d.Add(pt0, vec)
            
            vec.Rotate(math.radians(random.uniform(-120,120)), plane.XAxis)
            vec.Unitize()
            vec *= length
            pt2 = rg.Point3d.Add(pt1, vec)
            nurb = rg.NurbsCurve.Create(False, 2, [pt0, pt1, pt2])
            tan = nurb.TangentAt(1)
            
            
            circ = rg.Circle(plane, self.size)
            circ = circ.ToNurbsCurve()
            sweep = rg.SweepOneRail()
            geo = sweep.PerformSweep(nurb, circ)[0]
            
            results = rg.Intersect.Intersection.BrepBrep(geo, self.boundary, sc.doc.ModelAbsoluteTolerance)
            if len(results[1]) == 0:
                endPlane = [rg.Plane(pt2, tan)]
                sc.doc.Objects.AddBrep(geo, self.attr)
                self.nextRoundPlanes += endPlane

class Ball():
    def __init__(self):
        #self.pos = rg.Point3d(50, 50, 50)
        self.pos = rg.Point3d(random.uniform(20, 80), random.uniform(20, 80), random.uniform(20, 80))
        self.size = 20
        self.sphere = rg.Sphere(self.pos, self.size)
        #self.id = sc.doc.Objects.AddSphere(self.sphere)
        self.brep = self.sphere.ToBrep()
        self.vel = rg.Vector3d(random.uniform(-1,1),random.uniform(-1,1),random.uniform(-1,1))
        self.vel.Unitize()
        self.vel *= 5
    
    def Update(self):
        futurePos = self.pos + self.vel
        hitBoundary = False
        f = 1
        repulsion = 10
        self.prevPos = rg.Point3d(self.pos)
        
        
        
        if futurePos.X < self.size * f:
            self.vel.X *= -1
        if futurePos.Y < self.size * f:
            self.vel.Y *= -1
        if futurePos.Z < self.size * f:
            self.vel.Z *= -1
        if futurePos.X > 100-self.size * f:
            self.vel.X *= -1
        if futurePos.Y > 100-self.size * f:
            self.vel.Y *= -1
        if futurePos.Z > 100-self.size * f:
            self.vel.Z *= -1
        
        self.pos += self.vel
        
        xform = rg.Transform.Translation(self.prevPos - self.pos)
        self.sphere.Transform(xform)
        self.brep.Transform(xform)
        #self.id = sc.doc.Objects.Transform(self.id, xform, True)

class Module():
    def __init__(self, system, size, plane):
        self.system = system
        self.ang = 0
        self.plane = plane
        self.geo = None
        self.size = size
        self.age = 0
        self.length = size*1.5
        
        self.attr = rc.DocObjects.ObjectAttributes()
        self.attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        self.attr.MaterialSource = rc.DocObjects.ObjectMaterialSource.MaterialFromObject
        
        col = color.GetRandomNamedColor()
        r = util.Remap(self.plane.Origin.X, 0, 100, 100, 255)
        g = util.Remap(self.plane.Origin.Y, 0, 100, 100, 255)
        b = util.Remap(self.plane.Origin.Z, 0, 100, 100, 255)
        col = drawing.Color.FromArgb(r,g,b)
        self.attr.ObjectColor = col
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = self.attr.ObjectColor
        self.mat.CommitChanges()
        self.attr.MaterialIndex = index
        self.id = None
        offset = 0.1
        
        loop = True
        safety = 0
        while loop:
            safety += 1
            if safety > 20:
                print "SAFETY"
                self.system.deadPlanes.append(plane)
                return
            
            box = rg.Box(self.plane, rg.Interval(-self.size/2+offset, self.size/2-offset),rg.Interval(-self.size/2+offset, self.size/2-offset),rg.Interval(offset, self.size-offset))
            testGeo = box.ToBrep()
            
            loop = False
            results = rg.Intersect.Intersection.BrepBrep(testGeo, self.system.boundary, sc.doc.ModelAbsoluteTolerance)
            if len(results[1]) > 0:
                print "HIT BOUNDARY"
                #self.system.deadPlanes.append(plane)
                return
            for eachGeo in self.system.breps:
                results = rg.Intersect.Intersection.BrepBrep(testGeo, eachGeo, sc.doc.ModelAbsoluteTolerance)
                if len(results[1]) > 0:
                    loop = True
        
        self.geo = testGeo
        self.system.breps.append(self.geo)
        #self.system.deadPlanes.append(plane)
        
        #Create Planes for other boxes
        if False:
            #Center Plane
            centerPlane = plane.Clone()
            vec = centerPlane.Normal
            vec *= self.size/2
            xform = rg.Transform.Translation(vec)
            centerPlane.Transform(xform)
            
            #Top plane
            vec = centerPlane.Normal
            vec *= self.size/2
            xform = rg.Transform.Translation(vec)
            topPlane = centerPlane.Clone()
            topPlane.Transform(xform)
            self.system.nextRoundPlanes.append(topPlane)
            
            #Xplane+
            vec = centerPlane.XAxis
            vec *= self.size/2
            xform = rg.Transform.Translation(vec)
            pt = centerPlane.Origin
            pt.Transform(xform)
            xPlanePlus = rg.Plane(pt, centerPlane.YAxis, centerPlane.ZAxis)
            self.system.nextRoundPlanes.append(xPlanePlus)
    
    def UpdateDisplay0(self):
        if self.id:
            sc.doc.Objects.Delete(self.id, True)
            self.id = None
        
        if self.system.ball.brep.IsPointInside(self.plane.Origin, sc.doc.ModelAbsoluteTolerance, False):
            self.id = sc.doc.Objects.AddBrep(self.geo, self.attr)
    
    def UpdateDisplay(self):
        self.age += 1
        #scale = .005
        #val = self.system.pn.noise3(self.plane.Origin.X*scale, self.plane.Origin.Y*scale, self.plane.Origin.Z*scale, 10000000, self.age)
        
        if self.id:
            sc.doc.Objects.Delete(self.id, True)
            self.id = None
        
        isInside = False
        for ball in self.system.balls:
            if ball.brep.IsPointInside(self.plane.Origin, sc.doc.ModelAbsoluteTolerance, False):
                isInside = True
        if isInside == True:
            self.id = sc.doc.Objects.AddBrep(self.geo, self.attr)


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
        pSystem.UpdateDisplay()
        
        
        ################################
        #HUD
        display.UpdateParam1('open: ' + str(len(pSystem.voxels)))
        #display.UpdateParam2('y: ' + str(ball.pos.Y))
        #display.UpdateParam3('z: ' + str(ball.pos.Z))
        display.UpdateScaleBar()
        
        ################################
        sc.doc.Views.Redraw()
        display.Update(i)
        anim.AddFrame(numberOfPasses = numPasses)
        
        rs.Sleep(200)
        
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
