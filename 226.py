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
        initPlane.Origin = rg.Point3d(50,50, 10)
        
        self.majorBrep = rg.Brep()
        
        self.openPlanes = []
        self.nextRoundPlanes = [initPlane]
        self.modules = []
        
        self.attr = rc.DocObjects.ObjectAttributes()
        self.attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        self.attr.MaterialSource = rc.DocObjects.ObjectMaterialSource.MaterialFromObject
        
        grad = color.GetGradient(5)
        self.attr.ObjectColor = color.GradientOfColors(grad, 0)
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = self.attr.ObjectColor
        self.mat.CommitChanges()
        self.attr.MaterialIndex = index
    
    
    def Update(self, time):
        grad = color.GetGradient(1)
        self.attr.ObjectColor = color.GradientOfColors(grad, util.Remap(time, 0, 150, 0, 1))
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = self.attr.ObjectColor
        self.mat.CommitChanges()
        self.attr.MaterialIndex = index
        
        self.openPlanes = self.nextRoundPlanes
        self.openPlanes = self.openPlanes[:8]
        self.nextRoundPlanes = []
        
        planesToRemove = []
        for plane in self.openPlanes:
            planesToRemove.append(plane)
            self.AddModule(plane)
        
        for plane in planesToRemove:
            self.openPlanes.remove(plane)
    
    def UpdateDisplay(self):
        pass
    
    def AddModule(self, plane):
        safety = 0
        while True:
            safety += 1
            if safety > 10:
                return
            mod = Module(4)
            case = random.randint(0,2)
            #case = random.choice([0,2])
            if case == 0:
                mod.CreateStraight()
            elif case == 1:
                mod.CreateAngle()
            elif case == 2:
                mod.CreateT()
            
            originPlane = rg.Plane.WorldXY
            rot = random.randint(0,3) * 90
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

class Pipe():
    def __init__(self, system, vec = None):
        self.system = system
        self.val = None
        self.history = []
        self.historyPos = []
        self.pipeIDs = []
        self.pipe = None
        self.pipes = []
        self.alive = True
        self.size = random.uniform(1, 6)
        self.length = self.size*2
        self.turned = False
        self.prevVel = None
        self.majorBrep = rg.Brep()
        self.prevBrep = None
        self.planes = []
        self.ids = []
        self.breps = []
        
        self.straightSec =  Module(self.size)
        self.straightSec.CreateStraight()
        self.angleSec = Module(self.size)
        self.angleSec.CreateAngle()
        self.uTurnSec = Module(self.size)
        self.uTurnSec.CreateUturn()
        self.TSec = Module(self.size)
        self.TSec.CreateT()
        
        self.cases = {
        0: rg.Vector3d(1,0,0),
        1: rg.Vector3d(-1,0,0),
        2: rg.Vector3d(0,1,0),
        3: rg.Vector3d(0,-1,0),
        4: rg.Vector3d(0,0,1),
        5: rg.Vector3d(0,0,-1)
        }
        
        self.case = random.randint(0,len(self.cases)-1)
        
        #Movement
        #self.vel = rg.Vector3d(random.uniform(-1,1),random.uniform(-1,1), random.uniform(-.2,.2))
        if vec is None:
            self.vel = random.choice(self.cases)
        else:
            self.vel = vec
        self.vel.Unitize()
        self.tempVel = self.vel.Clone()
        self.speed = self.length
        self.vel *= self.speed
        self.acc = rg.Vector3d(0,0,0)
        self.size = 2
        self.cone = None
        self.coneID = None
        self.rotAngle = 0
        
        #Color and Material
        self.attr = rc.DocObjects.ObjectAttributes()
        self.attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        #self.grad = color.GetGradient(random.randint(0,9))
        self.grad = color.GetGradient(4)
        #col = drawing.Color.AliceBlue
        self.attr.MaterialSource = rc.DocObjects.ObjectMaterialSource.MaterialFromObject
        self.attr.ObjectColor = color.GradientOfColors(self.grad, random.uniform(0,1))
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = self.attr.ObjectColor
        self.mat.CommitChanges()
        self.attr.MaterialIndex = index
        
        self.attrCol1 = rc.DocObjects.ObjectAttributes()
        self.attrCol1.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        self.attrCol1.ObjectColor = drawing.Color.Red
        self.attrCol2 = rc.DocObjects.ObjectAttributes()
        self.attrCol2.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        self.attrCol2.ObjectColor = drawing.Color.Green
        self.attrCol3 = rc.DocObjects.ObjectAttributes()
        self.attrCol3.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        self.attrCol3.ObjectColor = drawing.Color.Blue
        
        #Position
        self.pos =  rg.Point3d(random.uniform(5,95), random.uniform(5,95), random.uniform(5,95))
        #self.pos =  rg.Point3d(50, 50, 50)
        self.plane = rg.Plane(self.pos, self.vel)
        self.planes.append(self.plane)
        self.origin = rg.Point3d(self.pos)
        
        #Bake
        self.tempIDs = []
        self.ids = []
        self.coneIDs = []
        self.id = None
    
    def Update(self, time):
        for id in self.ids:
            sc.doc.Objects.Delete(id, True)
        
        safety = 0
        masterSafety = 0
        
        while True:
            safety += 1
            masterSafety += 1
            if masterSafety > 100:
                self.alive = False
                print "MASTER SAFETY"
                break
            if safety > 20:
                print "SAFETY"
                self.majorBrep.Faces.RemoveAt(self.majorBrep.Faces.Count-1)
                self.planes.pop(-1)
                self.breps.pop(-1)
                safety = 0
                continue
            
            #closestD = None
            angle = math.radians(random.randint(0,3) * 90)
            currPlane = self.planes[-1].Clone()
            
            case = random.randint(1,2)
            if case == 0:
                #Straight
                geo = self.straightSec.geo.Duplicate()
                endPlane = self.straightSec.planeEnds[0].Clone()
                #currPlane.Rotate(angle, currPlane.Normal, currPlane.Origin)
                xform = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, currPlane)
            if case == 1:
                #Angle
                geo = self.angleSec.geo.Duplicate()
                endPlane = self.angleSec.planeEnds[0].Clone()
                currPlane.Rotate(angle, currPlane.Normal, currPlane.Origin)
                xform = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, currPlane)
            if case == 2:
                #U Turn
                geo = self.uTurnSec.geo.Duplicate()
                endPlane = self.uTurnSec.planeEnds[0].Clone()
                currPlane.Rotate(angle, currPlane.Normal, currPlane.Origin)
                xform = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, currPlane)
            
            geo.Transform(xform)
            endPlane.Transform(xform)
            #print rs.Distance(endPlane.Origin, self.origin)
            
            #Test for intersection
            finished = False
            results = rg.Intersect.Intersection.BrepBrep(geo, self.system.boundary, sc.doc.ModelAbsoluteTolerance)
            if len(results[1]) == 0:
                #It is not intersecting the boundary
                results = rg.Intersect.Intersection.BrepBrep(geo, self.majorBrep, sc.doc.ModelAbsoluteTolerance)
                if len(results[1]) == 0:
                    hittingAnother = False
                    for otherParticle in self.system.particles:
                        if otherParticle is self:
                            continue
                        #It is not intersecting itself
                        results = rg.Intersect.Intersection.BrepBrep(geo, otherParticle.majorBrep, sc.doc.ModelAbsoluteTolerance)
                        if len(results[1]) > 0:
                            #Not intersecting other brep
                            hittingAnother = True
                    if hittingAnother == False:
                        if len(self.breps) > 0:
                            self.majorBrep.Append(self.breps[-1])
                        self.breps.append(geo)
                        
                        self.planes.append(endPlane)
                        finished = True
            if finished:
                #Not intersecting, can leave loop
                break
        
        if self.id:
            sc.doc.Objects.Delete(self.id, True)
        self.id = sc.doc.Objects.AddBrep(self.majorBrep, self.attr)
    
    def UpdateDisplay(self):
        for id in self.tempIDs:
            sc.doc.Objects.Delete(id, True)
    
    def AvoidNeighborPaths(self):
        futureVel = self.vel.Clone()
        futurePos = self.pos.Clone()
        futureVel += self.acc
        futurePos += futureVel
        
        plane0 = rg.Plane(self.pos, futureVel)
        plane1 = rg.Plane(futurePos, futureVel)
        l = futurePos-self.pos
        
        cone = rg.Cone(plane0,self.size*10, self.size*3)
        cone = cone.ToBrep(False)
        
        for neigh in self.system.particles:
            if neigh is self: continue
            if neigh.pipe:
                results = rg.Intersect.Intersection.BrepBrep(cone, neigh.pipe, sc.doc.ModelAbsoluteTolerance)
                if len(results[1]) > 0:
                    #bbox = rg.BoundingBox(results[1][0]) 
                    pt = geo.PointBetweenPoints(results[1][0].PointAtStart, results[1][0].PointAtEnd)
                    collisionVec = futurePos - pt
                    rg.Vector3d.PerpendicularTo(collisionVec, futureVel)
                    collisionVec.Unitize()
                    self.acc += collisionVec
                    #print "Avoided!"
                    #sc.doc.Objects.AddPoint(self.pos)
        
        #cylinder = rg.Cylinder(circ0, l.Length*2)
        #cylinder = cylinder.ToBrep(False, False)
        #self.tempIDs.append(sc.doc.Objects.AddBrep(cone))
    
    def AvoidSelf(self):
        pass
    
    def ChangeDirection(self):
        cases = [0,1,2,3,4,5]
        cases.remove(self.case)
        if self.case%2 == 0:
            #print "{}->{}".format(self.case, self.case+1)
            cases.remove(self.case+1)
        else:
            #print "{}->{}".format(self.case, self.case-1)
            cases.remove(self.case-1)
        
        while True:
            tempCase = random.choice(cases)
            if self.DoesThisIntersect(tempCase) or True:
                break
            else:
                cases.remove(tempCase)
                if len(cases) == 0:
                    print "No remaining cases"
                    self.alive = False
                    break
        
        self.case = tempCase
    
    def DoesThisIntersect(self, case):
        testCase = self.cases[case]
    
    def CreateRectangles(self):
        futureVel = self.vel.Clone()
        futurePos = self.pos.Clone()
        futureVel += self.acc
        futurePos += futureVel
        
        n0 = self.plane.ZAxis
        n1 = futureVel
        vecAngle = rs.VectorAngle(n0, n1)
        cross = rg.Vector3d.CrossProduct(n0, n1)
        
        self.plane.Rotate(math.radians(vecAngle), cross, self.pos)
        self.plane.Origin = self.pos
        self.plane.Rotate(math.radians(1), self.plane.Normal)
        
        pts = [rg.Point3d(self.size/2, self.size, 0), rg.Point3d(self.size/2, -self.size, 0), rg.Point3d(-self.size/2, -self.size, 0), rg.Point3d(-self.size/2, self.size, 0)]
        nurb = rg.NurbsCurve.Create(True, 3, pts)
        
        self.plane = rg.Plane(self.pos, self.vel)
        circ = rg.Circle(self.plane, self.size)
        circ = circ.ToNurbsCurve()
        
        xform = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, self.plane)
        nurb.Transform(xform)
        
        rect = rg.Rectangle3d(self.plane, rg.Interval(-self.size, self.size), rg.Interval(-self.size, self.size))
        rect = rect.ToNurbsCurve()
        #sc.doc.Objects.AddCurve(rect)
        
        self.history.append(circ)
        self.historyPos.append(self.pos)

class Module():
    def __init__(self, size):
        self.planeStart = rg.Plane.WorldXY
        self.geo = None
        self.cylinderGeo = None
        self.angleGeo = None
        self.uTurnGeo = None
        self.geoID = None
        self.size = size
        self.length = size
        self.sec = rg.Rectangle3d(self.planeStart, rg.Interval(-self.size/2, self.size/2), rg.Interval(-self.size/2, self.size/2))
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
        self.geo = rg.Extrusion.Create(self.sec, -self.length, True)
        self.geo = self.geo.ToBrep(False)
        
        pt = rg.Point3d(self.size/2, 0, self.length/2)
        planeEnd = rg.Plane.WorldYZ
        planeEnd.Origin = pt
        self.planeEnds.append(planeEnd)
        
        pt = rg.Point3d(self.size/2, 0, self.length/2)
        planeEnd = rg.Plane.WorldYZ
        planeEnd.Origin = pt
        rotXform = rg.Transform.Rotation(math.radians(180), rg.Vector3d(0,0,1), rg.Point3d(0,0,0))
        planeEnd.Transform(rotXform)
        self.planeEnds.append(planeEnd)
        

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
        display.UpdateParam1('open: ' + str(len(pSystem.nextRoundPlanes)))
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
