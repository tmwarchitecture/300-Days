import math
import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import Rhino as rc
import scriptcontext as sc

def Remap(OldValue0, OldMin, OldMax, NewMin, NewMax):
    """
    Remap(OldValue, OldMin, OldMax, NewMin, NewMax)
    """
    OldValue = float(OldValue0)
    if OldValue > OldMax:
        OldValue = OldMax
    elif OldValue < OldMin:
        OldValue = OldMin
    OldRange = (OldMax - OldMin)
    NewRange = (NewMax - NewMin)
    NewValue = (((OldValue - OldMin) * NewRange) / OldRange) + NewMin
    return NewValue

def Constrain(value, d0=0, d1=1):
    """Ensures values are kept between d0 and d1
    value: float
    returns:
        value
    """
    if value < d0:
        value = d0
    if value > d1:
        value = d1
    return value

def AngleABC(a, b, c):
    """AngleABC(a, b, c). As if A-B-C made a polyline, measures the clockwise angle
    parameters:
        a (pt): first pt
        b (pt): elbow between A and C.
        c (pt): last point
    returns:
        clockwise angle in degrees
    """
    vec1 = rs.VectorCreate(a, b)
    vec2 = rs.VectorCreate(c, b)
    inner = rs.VectorAngle(vec1, vec2)
    det = vec1[0]*vec2[1]-vec1[1]*vec2[0]
    if det<0: return inner
    else: return 360-inner

#Easing functions
def smoothStop(t, n = 2):
    """
    smoothly decelerates to the power of n
    t is 0.0 -> 1.0
    """
    return 1-(1-t)**n

def smoothStart(t, n = 2):
    """
    smoothly accelerates to the power of n
    t is 0.0 -> 1.0
    """
    return t**n

def crossfade2(t):
    """
    smooth step t to the power of 2.
    t is 0.0 -> 1.0
    For power > 2, use crossfadeN.
    
    """
    a = smoothStart(t, 2)
    b = smoothStop(t, 2)
    return (1-t)*a + (t)*b

def crossfadeN(t, n):
    """
    smooth step t to the power of n.
    t is 0.0 -> 1.0
    This is a hacked version done by myself.
    For n=2, use crossfade2, it's faster.
    
    """
    if t<.5:
        return smoothStart(t*2, n)*.5
    else:
        return (smoothStop((t-.5)*2, n)*.5)+.5

def BasicAttr():
    """
    ie:
        self.attr = BasicAttr()
    """
    attr = rc.DocObjects.ObjectAttributes()
    attr.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
    attr.MaterialSource = rc.DocObjects.ObjectMaterialSource.MaterialFromObject
    return attr

def SetMaterialToColor(attr):
    """
    Assigns attributes material to the current attribute color.
    Creates new material.
    
    ie:
        SetMaterialToColor(self.attr)
    """
    index = sc.doc.Materials.Add()
    mat = sc.doc.Materials[index]
    mat.DiffuseColor = attr.ObjectColor
    mat.CommitChanges()
    attr.MaterialIndex = index
