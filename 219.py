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
        self.m = rg.Mesh()
        self.mID = None
        #self.pn = perlin.SimplexNoise()
        
        self.boundary = rg.Box(rg.Plane.WorldXY, rg.Interval(0,100), rg.Interval(0,100), rg.Interval(0,100))
        self.boundary = self.boundary.ToBrep()
        for i in range(6):
            self.particles.append(Particle(self))
        
        self.straightSec = None
        self.angleSec = None
        
    def Update(self, time):
        numToAdd = 0
        particlesToRemove = []
        for particle in self.particles:
            if particle.alive:
                particle.Update2(time)
            else:
                particlesToRemove.append(particle)
                numToAdd += 1
        
        for particle in particlesToRemove:
            self.particles.remove(particle)
        
        for i in range(0, numToAdd):
            self.particles.append(Particle(self))
                #particle.UpdateDisplay()
        #for particle in self.particles:
        #    particle.AssignNeighbors()
    
    def AddParticle(self):
        self.particles.append(Particle(self))
        self.particles[-1].pos = self.particles[0].pos
        self.particles[-1].vel = self.particles[0].vel
        self.particles[-1].history = self.particles[0].history
        self.particles[-1].plane = self.particles[0].plane
    
    def DisplayConnections(self):
        for ball in self.balls:
            ball.DisplayConnections()
            ball.DisplaySurfaces()

class Cluster():
    def __init__(self, system):
        self.system = system

class Particle():
    def __init__(self, system):
        self.system = system
        self.val = None
        self.history = []
        self.historyPos = []
        self.pipeIDs = []
        self.pipe = None
        self.pipes = []
        self.alive = True
        self.length = 4
        self.turned = False
        self.prevVel = None
        self.prevPlane = None
        
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
        self.vel = rg.Vector3d(random.uniform(-1,1),random.uniform(-1,1), random.uniform(-.2,.2))
        self.vel.Unitize()
        self.tempVel = self.vel.Clone()
        self.speed = self.length
        self.vel *= self.speed
        self.acc = rg.Vector3d(0,0,0)
        self.size = 1
        self.cone = None
        self.coneID = None
        self.rotAngle = 0
        
        #Color and Material
        self.attr = rc.DocObjects.ObjectAttributes()
        self.attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        self.grad = color.GetGradient(random.randint(0,9))
        #col = drawing.Color.AliceBlue
        self.attr.MaterialSource = rc.DocObjects.ObjectMaterialSource.MaterialFromObject
        self.attr.ObjectColor = color.GradientOfColors(self.grad, 0)
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = self.attr.ObjectColor
        self.mat.CommitChanges()
        self.attr.MaterialIndex = index
        
        #Position
        #self.pos =  rg.Point3d(random.uniform(5,95), random.uniform(5,95), random.uniform(5,95))
        self.pos =  rg.Point3d(50, 50, 50)
        self.plane = rg.Plane(self.pos, self.vel)
        
        #Bake
        self.tempIDs = []
        self.ids = []
        self.coneIDs = []
    
    def Update2(self, time):
        self.prevPlane = self.plane
        
        self.attr.ObjectColor = color.GradientOfColors(self.grad, util.Remap(time, 0, 150, 0, 1))
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = self.attr.ObjectColor
        self.mat.CommitChanges()
        self.attr.MaterialIndex = index
        
        
        safety = 0
        while True:
            safety += 1
            case = random.randint(0,1)
            if case == 0:
                #Straight
                geo = self.system.straightSec.geo.Duplicate()
                endPlane = self.system.straightSec.planeEnd.Clone()
                xform = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, self.prevPlane)
            if case == 1:
                #Angle
                geo = self.system.angleSec.geo.Duplicate()
                endPlane = self.system.angleSec.planeEnd.Clone()
                self.prevPlane.Rotate(math.radians(random.uniform(0,360)), self.prevPlane.Normal, self.prevPlane.Origin)
                xform = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, self.prevPlane)
            
            geo.Transform(xform)
            results = rg.Intersect.Intersection.BrepBrep(geo, self.system.boundary, sc.doc.ModelAbsoluteTolerance)
            if safety > 20:
                print "SAFETY"
                self.alive = False
                break
            if len(results[1]) == 0:
                break
        
        
        endPlane.Transform(xform)
        if self.alive:
            sc.doc.Objects.AddBrep(geo, self.attr)
        
        self.plane = endPlane
    
    def Update(self, time):
        self.attr.ObjectColor = color.GradientOfColors(self.grad, util.Remap(time, 0, 150, 0, 1))
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = self.attr.ObjectColor
        self.mat.CommitChanges()
        self.attr.MaterialIndex = index
        
        
        prevTurn = self.turned
        self.turned = False
        self.prevVel = self.vel.Clone()
        self.prevPlane = self.plane.Clone()
        
        #Should I change?
        futurePos = self.pos + self.vel
        hitBoundary = False
        f = 2
        
        possibleCases = [0,1,2,3,4,5]
        if futurePos.X < self.size * f:
            hitBoundary = True
            possibleCases.remove(1)
        if futurePos.Y < self.size * f:
            hitBoundary = True
            possibleCases.remove(3)
        if futurePos.Z < self.size * f:
            hitBoundary = True
            possibleCases.remove(5)
        if futurePos.X > 100-self.size * f:
            hitBoundary = True
            possibleCases.remove(0)
        if futurePos.Y > 100-self.size * f:
            hitBoundary = True
            possibleCases.remove(2)
        if futurePos.Z > 100-self.size * f:
            hitBoundary = True
            possibleCases.remove(4)
        
        #self.AvoidNeighborPaths()
        #self.AvoidSelf()
        
        if hitBoundary == True:
            self.turned = True
            self.case = random.choice(possibleCases)
        
        if hitBoundary == False:
            if time%random.randint(6, 10) == 0 and prevTurn == False:
                self.turned = True
                self.ChangeDirection()
        
        self.vel = self.cases[self.case]*self.length
        self.CreateRectangles()
        
        if self.turned:
            pass
            #prevVel
            #jog = self.vel
            self.vel += self.prevVel
        
        self.pos += self.vel
        
        if len(self.history) > 20 and 1 == 2:
            self.history = self.history[-20:]
        if len(self.historyPos) > 30:
            self.historyPos.pop(0)
    
    def UpdateDisplay(self):
        for id in self.tempIDs:
            sc.doc.Objects.Delete(id, True)
        
        if self.turned:
            centerPt = self.prevPlane.Origin.Clone()
            centerPt += self.vel
            centerPlane = rg.Plane(centerPt, self.pos, self.prevPlane.Origin)
            circ = rg.Circle(centerPlane, self.size*self.length)
            arc = rg.Arc(circ, math.pi*.5)
            arc = arc.ToNurbsCurve()
            newPlane = self.prevPlane.Clone()
            tempVel = self.prevVel.Clone()
            tempCenter = self.prevPlane.Origin.Clone()
            tempCenter += tempVel
            newPlane.Origin = tempCenter
            circ = rg.Circle(newPlane, self.size)
            circ = circ.ToNurbsCurve()
            sweep = rg.SweepOneRail()
            if arc and circ:
                breps = sweep.PerformSweep(arc, circ)
                for brep in breps:
                    sc.doc.Objects.AddBrep(brep, self.attr)
        else:
            geo = self.system.straightSec.geo.Duplicate()
            xform = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, self.prevPlane)
            geo.Transform(xform)
            sc.doc.Objects.AddBrep(geo, self.attr)
        
        for id in self.ids:
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
        
        #pts = [rg.Point3d(self.size/2, self.size, 0), rg.Point3d(self.size/2, -self.size, 0), rg.Point3d(-self.size/2, -self.size, 0), rg.Point3d(-self.size/2, self.size, 0), rg.Point3d(self.size/2, self.size, 0)]
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
    def __init__(self):
        self.planeStart = rg.Plane.WorldXY
        self.planeEnd = None
        self.geo = None
        self.geoID = None
        self.size = 1
        self.sec = rg.Circle(self.planeStart, self.size)
        self.sec.ToNurbsCurve()
    
    def CreateCylinder(self):
        pt = rg.Point3d(0,0,self.size*4)
        self.planeEnd = rg.Plane.WorldXY
        self.planeEnd.Origin = pt
        
        self.geo = rg.Cylinder(self.sec, self.size*4)
        self.geo = self.geo.ToBrep(False, False)
    
    def CreateAngle(self):
        pt = rg.Point3d(0,0,self.size*4)
        pt += rg.Vector3d(self.size*4, 0, 0)
        self.planeEnd = rg.Plane.WorldYZ
        self.planeEnd.Origin = pt
        
        centerPt = rg.Point3d(self.size*4, 0, 0)
        origin = rg.Point3d(0,0,0)
        
        centerPlane = rg.Plane(centerPt, origin, pt)
        circ = rg.Circle(centerPlane, self.size*4)
        arc = rg.Arc(circ, math.pi*.5)
        arc = arc.ToNurbsCurve()
        
        circ = rg.Circle(origin, self.size)
        circ = circ.ToNurbsCurve()
        sweep = rg.SweepOneRail()
        self.geo = sweep.PerformSweep(arc, circ)[0]

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
    pSystem.straightSec = Module()
    pSystem.straightSec.CreateCylinder()
    pSystem.angleSec = Module()
    pSystem.angleSec.CreateAngle()
    
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
        #display.UpdateParam1('ang: ' + str(pSystem.particles[0].val))
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
