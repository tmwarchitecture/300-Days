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
        
        self.openPlanes = []
        self.deadPlanes = []
        self.nextRoundPlanes = [initPlane]
        self.modules = []
        
        self.size = 1
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
        
        
        self.pipes = []
        for i in range(1):
            self.pipes.append(Pipe(self))
    
    def Update(self, time):
        self.time = time
        self.openPlanes = self.nextRoundPlanes
        random.shuffle(self.openPlanes)
        openPlanes = self.openPlanes[:8]
        self.deadPlanes = self.openPlanes[8:]
        self.openPlanes = openPlanes
        self.nextRoundPlanes = []
        
        planesToRemove = []
        #size = util.Remap(self.time, 0,150,5,1)
        numToAdd = 0
        pipesToRemove = []
        for pipe in self.pipes:
            if pipe.alive:
                pipe.Update(time)
                if pipe.alive == False:
                    pipesToRemove.append(pipe)
        
        for pipe in self.pipes:
            if pipe.alive:
                pipe.UpdateDisplay()
        
        for pipe in pipesToRemove:
            self.pipes.append(Pipe(self))
        
        #for plane in self.openPlanes:
        #    planesToRemove.append(plane)
        #    #self.AddModule(plane, size)
        #    self.AddModule2(plane, self.size)
        
        #for plane in planesToRemove:
        #    self.openPlanes.remove(plane)
        
        #for plane in self.deadPlanes:
        #    sc.doc.Objects.AddSphere(rg.Sphere(plane, self.size), self.attr)
    
    def UpdateDisplay(self):
        pass
    
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
    
class Pipe():
    def __init__(self, system, vec = None):
        self.system = system
        self.majorBrep = rg.Brep()
        self.alive = True
        self.age = 0
        
        self.history = []
        self.segments = []
        
        #Movement
        #self.vel = rg.Vector3d(random.uniform(-1,1),random.uniform(-1,1), random.uniform(-.2,.2))
        #self.vel.Unitize()
        #self.size = random.uniform(1, 3)
        self.size = .1
        self.length = .75
        
        #Color and Material
        self.attr = rc.DocObjects.ObjectAttributes()
        self.attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        #self.grad = color.GetGradient(random.randint(0,9))
        self.grad = color.GetGradient(4)
        #col = drawing.Color.AliceBlue
        col = color.GradientOfColors(self.grad, random.uniform(0,1))
        self.attr.MaterialSource = rc.DocObjects.ObjectMaterialSource.MaterialFromObject
        self.attr.ObjectColor = col
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = self.attr.ObjectColor
        self.mat.CommitChanges()
        self.attr.MaterialIndex = index
        
        #Position
        self.pos =  rg.Point3d(random.uniform(5,95), random.uniform(5,95), .1)
        #self.pos =  rg.Point3d(50, 50, 99)
        self.dir = rg.Vector3d(0,0,1)
        initPlane = rg.Plane.WorldXY
        initPlane.Origin = self.pos
        
        initPlane = rg.Plane(self.pos, self.dir)
        
        self.openPlanes = []
        self.planesToRemove = []
        self.nextRoundPlanes = [initPlane]
        
        self.crv = None
        self.crvs = rc.Collections.CurveList()
        self.pts = []
        
        self.ids = []
        
        sc.doc.Objects.AddSphere(rg.Sphere(self.pos, self.size), self.attr)
    
    def Update(self, time):
        self.time = time
        self.age += 1
        #self.size = util.Remap(self.age, 0, 150, .1, 5)
        
        self.openPlanes = self.nextRoundPlanes
        random.shuffle(self.openPlanes)
        openPlanes = self.openPlanes[:8]
        self.deadPlanes = self.openPlanes[8:]
        self.openPlanes = openPlanes
        self.nextRoundPlanes = []
        
        planesToRemove = []
        
        for plane in self.openPlanes:
            #Rotate base plane
            plane.Rotate(math.radians(random.uniform(0,360)), plane.Normal)
            
            #Construct new arc
            vec = plane.Normal
            vec *= self.length
            pt0 = plane.Origin
            pt1 = rg.Point3d.Add(pt0, vec)
            
            closestDist = None
            closestPt = None
            for otherPipe in self.system.pipes:
                if otherPipe is self: continue
                for eachCrv in otherPipe.crvs:
                    result, param = eachCrv.ClosestPoint(pt1, 20)
                    if result:
                        closePt = eachCrv.PointAt(param)
                        d = rs.Distance(pt1, closePt)
                        if d < self.length*2:
                            if d < closestDist or closestDist is None:
                                closestDist = d
                                closestPt = closePt
            
            if closestPt:
                pt2 = closestPt
                self.alive = False
                #print "Joined"
            else:
                #vec.Rotate(math.radians(random.uniform(-90,90)), plane.XAxis)
                safety = 0
                while True:
                    safety += 1
                    if safety > 10:
                        break
                    vec.Rotate(math.radians(random.uniform(-5,5)), plane.XAxis)
                    vec.Unitize()
                    vec *= self.length
                    pt2 = rg.Point3d.Add(pt1, vec)
                    if self.age > 5:
                        results = self.system.boundary.ClosestPoint(pt2, 20)
                        if results[0]:
                            d = rs.Distance(pt2, results[1])
                            if d < 5:
                                continue
                    else:
                        break
            
            
            nurb = rg.NurbsCurve.Create(False, 2, [pt0, pt1, pt2])
            tan = nurb.TangentAt(1)
            
            circ = rg.Circle(plane, self.size)
            circNurb = circ.ToNurbsCurve()
            
            sweep = rg.SweepOneRail()
            geo = sweep.PerformSweep(nurb, circNurb)[0]
            
            results = rg.Intersect.Intersection.BrepBrep(geo, self.system.boundary, sc.doc.ModelAbsoluteTolerance)
            if len(results[1]) == 0:
                self.pts.append(pt1)
                self.pts.append(pt2)
                self.crvs.Add(nurb)
                self.history.append(circ)
                self.segments.append(Segment(self, circ, plane, nurb, self.size))
                endPlane = [rg.Plane(pt2, tan)]
                self.nextRoundPlanes += endPlane
        
        for plane in planesToRemove:
            self.openPlanes.remove(plane)
        
        for plane in self.deadPlanes:
            sc.doc.Objects.AddSphere(rg.Sphere(plane, self.size), self.attr)
        
        if len(self.nextRoundPlanes) == 0:
            self.alive = False
            sc.doc.Objects.AddSphere(rg.Sphere(plane.Origin, self.size), self.attr)
    
    def UpdateDisplay(self):
        for segment in self.segments:
            segment.UpdateDisplay()

class Segment():
    def __init__(self, parent, circ, plane, path, size):
        self.size = size
        self.parent = parent
        self.circ = circ
        self.plane = plane
        self.path = path
        self.id = None
    def UpdateDisplay(self):
        if self.id:
            sc.doc.Objects.Delete(self.id, True)
        
        growthRate = .1
        
        xform = rg.Transform.Scale(self.plane.Origin, (self.size + growthRate) / self.size)
        self.size += growthRate
        self.circ.Transform(xform)
        newCircNurb = self.circ.ToNurbsCurve()
        sweep = rg.SweepOneRail()
        geo = sweep.PerformSweep(self.path, newCircNurb)[0]
        
        self.id = sc.doc.Objects.AddBrep(geo, self.parent.attr)
        
    
class Module():
    def __init__(self, size):
        self.planeStart = rg.Plane.WorldXY
        self.geo = None
        self.cylinderGeo = None
        self.angleGeo = None
        self.uTurnGeo = None
        self.geoID = None
        self.size = size
        self.length = size*1.5
        self.sec = rg.Rectangle3d(self.planeStart, rg.Interval(-self.size/2, self.size/2), rg.Interval(-self.size/2, self.size/2))
        self.sec = self.sec.ToNurbsCurve()
        self.sec.Reverse()
        self.sec = rg.Circle(rg.Plane.WorldXY, self.size/2)
        self.sec = self.sec.ToNurbsCurve()
        self.sec.Reverse()
        
        self.attr = rc.DocObjects.ObjectAttributes()
        self.attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        self.attr.MaterialSource = rc.DocObjects.ObjectMaterialSource.MaterialFromObject
        
        col = color.GetRandomNamedColor()
        self.attr.ObjectColor = col
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = self.attr.ObjectColor
        self.mat.CommitChanges()
        self.attr.MaterialIndex = index
        
        self.planeEnds = []
    
    def CreateNurbs(self):
        pass
    
    def CreateStraight(self):
        pt = rg.Point3d(0,0,self.length)
        planeEnd = rg.Plane.WorldXY
        planeEnd.Origin = pt
        self.planeEnds.append(planeEnd)
        
        self.geo = rg.Extrusion.Create(self.sec, -self.length, True)
        self.geo = self.geo.ToBrep(False)
    
    def CreateAngle(self):
        pt = rg.Point3d(self.length, 0, self.length)
        planeEnd = rg.Plane.WorldYZ
        planeEnd.Origin = pt
        self.planeEnds.append(planeEnd)
        
        centerPt = rg.Point3d(self.length, 0, 0)
        origin = rg.Point3d(0,0,0)
        
        centerPlane = rg.Plane(centerPt, origin, pt)
        circ = rg.Circle(centerPlane, self.length)
        arc = rg.Arc(circ, math.pi*.5)
        arc = arc.ToNurbsCurve()
        sweep = rg.SweepOneRail()
        self.geo = sweep.PerformSweep(arc, self.sec)[0]
    
    def CreateUturn(self):
        xDir = rg.Vector3d(-1,0,0)
        yDir = rg.Vector3d(0,1,0)
        planeEnd = rg.Plane(rg.Point3d(self.length*2, 0, 0), xDir, yDir)
        self.planeEnds.append(planeEnd)
        
        pt = rg.Point3d(self.length,0,self.length)
        
        centerPt = rg.Point3d(self.length, 0, 0)
        origin = rg.Point3d(0,0,0)
        
        centerPlane = rg.Plane(centerPt, origin, pt)
        circ = rg.Circle(centerPlane, self.length)
        arc = rg.Arc(circ, math.pi)
        arc = arc.ToNurbsCurve()
        
        sweep = rg.SweepOneRail()
        self.geo = sweep.PerformSweep(arc, self.sec)[0]
    
    def CreateT(self):
        geo0 = rg.Extrusion.Create(self.sec, -self.length + self.length/2, True)
        geo0 = geo0.ToBrep(False)
        
        sweepCenterPt = rg.Point3d(self.length, 0, 0)
        origin = rg.Point3d(0,0,0)
        pt = rg.Point3d(self.length, 0, self.length)
        centerPlane = rg.Plane(sweepCenterPt, origin, pt)
        
        circ = rg.Circle(centerPlane, self.length)
        arc = rg.Arc(circ, math.pi*.5)
        arc = arc.ToNurbsCurve()
        sweep = rg.SweepOneRail()
        geo1 = sweep.PerformSweep(arc, self.sec)[0]
        geo1 = geo1.CapPlanarHoles(sc.doc.ModelAbsoluteTolerance)
        
        rotXform = rg.Transform.Rotation(math.radians(180), rg.Vector3d(0,0,1), rg.Point3d(0,0,0))
        
        pt = rg.Point3d(self.size/2, 0, self.length/2)
        planeEnd = rg.Plane.WorldYZ
        planeEnd.Origin = pt
        self.planeEnds.append(planeEnd)
        
        pt = rg.Point3d(self.size/2, 0, self.length/2)
        planeEnd = rg.Plane.WorldYZ
        planeEnd.Origin = pt
        
        planeEnd.Transform(rotXform)
        self.planeEnds.append(planeEnd)
        
        planeXform = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, planeEnd)
        tempCirc = self.sec.Duplicate()
        tempCirc.Transform(planeXform)
        geo1 = rg.Extrusion.Create(tempCirc, self.size, True)
        geo1 = geo1.ToBrep(False)
        
        union = rg.Brep()
        results = union.CreateBooleanUnion([geo0, geo1], sc.doc.ModelAbsoluteTolerance)
        self.geo = results[0]

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
        if random.randint(0,20) == 0:
            pSystem.pipes.append(Pipe(pSystem))
        
        pSystem.Update(i)
        
        
        ################################
        #HUD
        display.UpdateParam1('open: ' + str(len(pSystem.pipes)))
        #display.UpdateParam2('y: ' + str(ball.pos.Y))
        #display.UpdateParam3('z: ' + str(ball.pos.Z))
        display.UpdateScaleBar()
        
        ################################
        sc.doc.Views.Redraw()
        display.Update(i)
        anim.AddFrame(numberOfPasses = numPasses)
        
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
