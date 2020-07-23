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
        self.pn = perlin.SimplexNoise()
        
        for i in range(30):
            self.particles.append(Particle(self))
        
        for item in self.particles:
            item.AssignNeighbors()
        
        #self.m = rg.Mesh()
        #for item in self.particles:
        #    item.CreateMesh()
        
        self.mID = sc.doc.Objects.AddMesh(self.m)
        
    def Update(self, time):
        for particle in self.particles:
            particle.Update(time)
        for particle in self.particles:
            particle.AssignNeighbors()
        
    def DisplayConnections(self):
        for ball in self.balls:
            ball.DisplayConnections()
            ball.DisplaySurfaces()
    
class Particle():
    def __init__(self, system):
        self.system = system
        self.val = None
        
        #Movement
        self.vel = rg.Vector3d(random.uniform(-1,1),random.uniform(-1,1), random.uniform(-1,1))
        self.vel.Unitize()
        self.speed = random.uniform(1, 2)
        self.vel *= self.speed
        self.acc = rg.Vector3d(0,0,0)
        self.size = 2
        self.cone = None
        self.coneID = None
        
        #Color and material
        self.attr = rc.DocObjects.ObjectAttributes()
        self.attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
        self.attr.ObjectColor = color.ColorBetweenColors(drawing.Color.DeepSkyBlue, drawing.Color.LimeGreen, random.uniform(0,1))
        self.attr.MaterialSource = rc.DocObjects.ObjectMaterialSource.MaterialFromObject
        index = sc.doc.Materials.Add()
        self.mat = sc.doc.Materials[index]
        self.mat.DiffuseColor = self.attr.ObjectColor
        self.mat.CommitChanges()
        self.attr.MaterialIndex = index
        
        #Position
        self.pos =  rg.Point3d(random.uniform(5,95), random.uniform(5,95), random.uniform(5,95))
        self.sphere = rg.Sphere(self.pos, 2)
        
        #Bake
        self.ids = []
        self.ids.append(sc.doc.Objects.AddSphere(self.sphere, self.attr))
    
    def AssignNeighbors(self):
        closestObj = None
        distance = None
        for eachOther in self.system.particles:
            if eachOther is self: continue
            d = rs.Distance(eachOther.pos, self.pos)
            if d < distance or distance is None:
                distance = d
                closestObj = eachOther
        
        norm = closestObj.pos - self.pos
        plane = rg.Plane(self.pos, norm)
        
        self.cone = rg.Cone(plane, norm.Length, 2)
        self.cone = self.cone.ToBrep(False)
        if self.coneID:
            sc.doc.Objects.Delete(self.coneID, True)
        self.coneID = sc.doc.Objects.AddBrep(self.cone, self.attr)
    
    def CreateMesh(self):
        if self.neigh0:
            pt0 = self.system.m.Vertices.Add(self.pos)
            pt1 = self.system.m.Vertices.Add(self.neigh0.pos)
            pt2 = self.system.m.Vertices.Add(self.neigh1.pos)
            self.system.m.Faces.AddFace(pt0, pt1, pt2)
        if self.neigh2:
            pt0 = self.system.m.Vertices.Add(self.pos)
            pt1 = self.system.m.Vertices.Add(self.neigh2.pos)
            pt2 = self.system.m.Vertices.Add(self.neigh3.pos)
            self.system.m.Faces.AddFace(pt0, pt1, pt2)
        self.system.m.Vertices.CombineIdentical(True, True)
    
    def Update(self, time):
        self.acc *= 0
        futurePos = self.pos + self.vel
        
        f = 1
        repulsion = 1
        if futurePos.X < self.size * f:
            distanceModifier = util.Remap(futurePos.X, self.size * f, 0, 0, repulsion)
            self.acc += rg.Vector3d(repulsion*distanceModifier,0,0)
        if futurePos.Y < self.size * f:
            distanceModifier = util.Remap(futurePos.Y, self.size * f, 0, 0, repulsion)
            self.acc += rg.Vector3d(0,repulsion*distanceModifier,0)
        if futurePos.Z < self.size * f:
            distanceModifier = util.Remap(futurePos.Z, self.size * f, 0, 0, repulsion)
            self.acc += rg.Vector3d(0,0,repulsion*distanceModifier)
        if futurePos.X > 100-self.size * f:
            distanceModifier = util.Remap(futurePos.X, 100-self.size * f, 100, 0, repulsion)
            self.acc += rg.Vector3d(-repulsion*distanceModifier,0,0)
        if futurePos.Y > 100-self.size * f:
            distanceModifier = util.Remap(futurePos.Y, 100-self.size * f, 100, 0, repulsion)
            self.acc += rg.Vector3d(0,-repulsion*distanceModifier,0)
        if futurePos.Z > 100-self.size * f:
            distanceModifier = util.Remap(futurePos.Z, 100-self.size * f, 100, 0, repulsion)
            self.acc += rg.Vector3d(0,0,-repulsion*distanceModifier)
        
        self.vel += self.acc
        self.pos += self.vel
        self.sphere = rg.Sphere(self.pos, 2)
        
        for id in self.ids:
            sc.doc.Objects.Delete(id, True)
        self.ids.append(sc.doc.Objects.AddSphere(self.sphere, self.attr))
    
    def DisplayConnections(self):
        for id in self.connectionIDs:
            sc.doc.Objects.Delete(id, True)
        
        neighs = self.GetClosest2Neighbors()
        if len(neighs) > 6:
            neighs = neighs[:6]
        
        for neigh in neighs:
            vec = self.pos - neigh.pos
            
            up = rg.Vector3d(0,0,1)
            xvec = rg.Vector3d.CrossProduct(vec, rg.Vector3d(0,0,1))
            yvec = rg.Vector3d.CrossProduct(vec, xvec)
            plane = rg.Plane(self.pos, yvec, xvec)
            
            circ = rg.Circle(plane, .1)
            cylinder = rg.Cylinder(circ, vec.Length)
            cylinder = cylinder.ToBrep(True, True)
            self.connectionIDs.append(sc.doc.Objects.AddBrep(cylinder))
    
    def DisplaySurfaces(self):
        for id in self.srfIDs:
            sc.doc.Objects.Delete(id, True)
        
        neighs = self.GetClosest2Neighbors()
        closestObjs = neighs[:2]
        if len(closestObjs) > 1:
            m = rg.Mesh()
            m.Vertices.Add(self.pos)
            m.Vertices.Add(closestObjs[0].pos)
            m.Vertices.Add(closestObjs[1].pos)
            m.Faces.AddFace(0,1,2)
            #m.Normal.ComputeNormals()
            
            
            self.srfIDs.append(sc.doc.Objects.AddMesh(m, self.attr))
    
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
    pSystem = System()
    
    ################################
    for i in range(numFrames):
        start_time = time.time()
        print "Frame {}".format(i)
        if sc.escape_test(False): anim.Cleanup(); return
        ################################
        #MAIN LOOP
        
        pSystem.Update(i)
        
        #ballSystem.DisplayConnections()
        
        #if i%10 == 0:
        #    ballSystem.balls.append(Ball(ballSystem))
        
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
    
    if int(skNum) > int(os.path.splitext(os.path.basename(__file__))[0]):
        print "!!!!SAVE THE SKETCH WITH A NEW NAME!!!!"
    
    if os.path.isdir(r"D:\Files\Work\LIBRARY\06_RHINO\10_Python\300 DAYS\anim"):
        anim.Create(r"D:\Files\Work\LIBRARY\06_RHINO\10_Python\300 DAYS\anim", frames2Keep = [i/2, i-1])
    else:
        anim.Create(r"C:\Tim\300 Days\anim", frames2Keep = [i/2, i-1])

if __name__ == "__main__":
    main()  
