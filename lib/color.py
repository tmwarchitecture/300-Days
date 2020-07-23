import System.Drawing as drawing
import random
import util
import Rhino as rc
import geometry as geo
from colorsys import rgb_to_hls, hls_to_rgb
import scriptcontext as sc
import rhinoscriptsyntax as rs


#Random
def GetRandomNamedColor():
    """Randomly selects a windows color from System.Drawing.Color
    Excludes white and black
    
    returns:
        color
    """
    cnames = {
    'aliceblue':            '#F0F8FF',
    'antiquewhite':         '#FAEBD7',
    'aqua':                 '#00FFFF',
    'aquamarine':           '#7FFFD4',
    'azure':                '#F0FFFF',
    'beige':                '#F5F5DC',
    'bisque':               '#FFE4C4',
    'black':                '#000000',
    'blanchedalmond':       '#FFEBCD',
    'blue':                 '#0000FF',
    'blueviolet':           '#8A2BE2',
    'brown':                '#A52A2A',
    'burlywood':            '#DEB887',
    'cadetblue':            '#5F9EA0',
    'chartreuse':           '#7FFF00',
    'chocolate':            '#D2691E',
    'coral':                '#FF7F50',
    'cornflowerblue':       '#6495ED',
    'cornsilk':             '#FFF8DC',
    'crimson':              '#DC143C',
    'cyan':                 '#00FFFF',
    'darkblue':             '#00008B',
    'darkcyan':             '#008B8B',
    'darkgoldenrod':        '#B8860B',
    'darkgray':             '#A9A9A9',
    'darkgreen':            '#006400',
    'darkkhaki':            '#BDB76B',
    'darkmagenta':          '#8B008B',
    'darkolivegreen':       '#556B2F',
    'darkorange':           '#FF8C00',
    'darkorchid':           '#9932CC',
    'darkred':              '#8B0000',
    'darksalmon':           '#E9967A',
    'darkseagreen':         '#8FBC8F',
    'darkslateblue':        '#483D8B',
    'darkslategray':        '#2F4F4F',
    'darkturquoise':        '#00CED1',
    'darkviolet':           '#9400D3',
    'deeppink':             '#FF1493',
    'deepskyblue':          '#00BFFF',
    'dimgray':              '#696969',
    'dodgerblue':           '#1E90FF',
    'firebrick':            '#B22222',
    'floralwhite':          '#FFFAF0',
    'forestgreen':          '#228B22',
    'fuchsia':              '#FF00FF',
    'gainsboro':            '#DCDCDC',
    'ghostwhite':           '#F8F8FF',
    'gold':                 '#FFD700',
    'goldenrod':            '#DAA520',
    'gray':                 '#808080',
    'green':                '#008000',
    'greenyellow':          '#ADFF2F',
    'honeydew':             '#F0FFF0',
    'hotpink':              '#FF69B4',
    'indianred':            '#CD5C5C',
    'indigo':               '#4B0082',
    'ivory':                '#FFFFF0',
    'khaki':                '#F0E68C',
    'lavender':             '#E6E6FA',
    'lavenderblush':        '#FFF0F5',
    'lawngreen':            '#7CFC00',
    'lemonchiffon':         '#FFFACD',
    'lightblue':            '#ADD8E6',
    'lightcoral':           '#F08080',
    'lightcyan':            '#E0FFFF',
    'lightgoldenrodyellow': '#FAFAD2',
    'lightgreen':           '#90EE90',
    'lightgray':            '#D3D3D3',
    'lightpink':            '#FFB6C1',
    'lightsalmon':          '#FFA07A',
    'lightseagreen':        '#20B2AA',
    'lightskyblue':         '#87CEFA',
    'lightslategray':       '#778899',
    'lightsteelblue':       '#B0C4DE',
    'lightyellow':          '#FFFFE0',
    'lime':                 '#00FF00',
    'limegreen':            '#32CD32',
    'linen':                '#FAF0E6',
    'magenta':              '#FF00FF',
    'maroon':               '#800000',
    'mediumaquamarine':     '#66CDAA',
    'mediumblue':           '#0000CD',
    'mediumorchid':         '#BA55D3',
    'mediumpurple':         '#9370DB',
    'mediumseagreen':       '#3CB371',
    'mediumslateblue':      '#7B68EE',
    'mediumspringgreen':    '#00FA9A',
    'mediumturquoise':      '#48D1CC',
    'mediumvioletred':      '#C71585',
    'midnightblue':         '#191970',
    'mintcream':            '#F5FFFA',
    'mistyrose':            '#FFE4E1',
    'moccasin':             '#FFE4B5',
    'navajowhite':          '#FFDEAD',
    'navy':                 '#000080',
    'oldlace':              '#FDF5E6',
    'olive':                '#808000',
    'olivedrab':            '#6B8E23',
    'orange':               '#FFA500',
    'orangered':            '#FF4500',
    'orchid':               '#DA70D6',
    'palegoldenrod':        '#EEE8AA',
    'palegreen':            '#98FB98',
    'paleturquoise':        '#AFEEEE',
    'palevioletred':        '#DB7093',
    'papayawhip':           '#FFEFD5',
    'peachpuff':            '#FFDAB9',
    'peru':                 '#CD853F',
    'pink':                 '#FFC0CB',
    'plum':                 '#DDA0DD',
    'powderblue':           '#B0E0E6',
    'purple':               '#800080',
    'red':                  '#FF0000',
    'rosybrown':            '#BC8F8F',
    'royalblue':            '#4169E1',
    'saddlebrown':          '#8B4513',
    'salmon':               '#FA8072',
    'sandybrown':           '#FAA460',
    'seagreen':             '#2E8B57',
    'seashell':             '#FFF5EE',
    'sienna':               '#A0522D',
    'silver':               '#C0C0C0',
    'skyblue':              '#87CEEB',
    'slateblue':            '#6A5ACD',
    'slategray':            '#708090',
    'snow':                 '#FFFAFA',
    'springgreen':          '#00FF7F',
    'steelblue':            '#4682B4',
    'tan':                  '#D2B48C',
    'teal':                 '#008080',
    'thistle':              '#D8BFD8',
    'tomato':               '#FF6347',
    'turquoise':            '#40E0D0',
    'violet':               '#EE82EE',
    'wheat':                '#F5DEB3',
    'white':                '#FFFFFF',
    'whitesmoke':           '#F5F5F5',
    'yellow':               '#FFFF00',
    'yellowgreen':          '#9ACD32'}
    while True:
        color = drawing.Color.FromName(random.choice(list(cnames)))
        if color == drawing.Color.White or color == drawing.Color.Black: continue
        return  color


#Gradients
def GetGradient(number = -1):
    """
    0 - Argon
    1 - Instagram
    2 - Fabled Sunset
    3 - Piglet
    4 - Pale RGB
    5 - White hot
    6 - Blue to Yellow
    7 - Makeup
    8 - Pink Sands
    9 - Fade to black
    10 - Zhestkov
    """
    if number == -1:
        col1 = GetRandomNamedColor()
        while True:
            col2 = GetRandomNamedColor()
            if col2 != col1: break
        while True:
            col3 = GetRandomNamedColor()
            if col3 != col1 and col3 != col2: break
        while True:
            col4 = GetRandomNamedColor()
            if col4 != col1 and col4 != col2 and col4 != col3: break
        return [col1, col2, col3, col4]
    
    gradients = []
    #0 - Argon
    gradients.append(['#03001e', '#7303c0', '#ec38bc', '#fdeff9'])
    #1 - Instagram
    gradients.append(['#833ab4', '#fd1d1d', '#fcb045'])
    #2 - Fabled Sunset
    gradients.append(['#231557', '#44107A', '#FF1361', '#FFF800'])
    #3 - Piglet
    gradients.append(['#ee9ca7', '#ffdde1'])
    #4 - Pale RGB
    gradients.append(['#A8E6CE', '#DCEDC2', '#FFD3B5', '#FFAAA6', '#FF8C94'])
    #5 - White hot
    gradients.append(['#E1F5C4', '#EDE574', '#F9D423', '#FC913A', '#FF4E50'])
    #6 - Blue to Yellow
    gradients.append(['#3f51b1', '#5a55ae', '#7b5fac', '#8f6aae', '#a86aa4' , '#cc6b8e' , '#f18271', '#f3a469', '#f7c978'])
    #7 - Makeup
    gradients.append(['#F7DFD4', '#EABCAC', '#E2B091', '#874E4C', '#472426'])
    #8 - Pink Sands
    gradients.append(['#4bbcf4', '#61c0bf', '#bbded6', '#ffb6b9', '#fae3d9'])
    #9 - Fade to black
    gradients.append(['#ffffff', '#1f1f1f'])
    #10 - Zhestkov
    gradients.append(['#040005','#580078', '#e028d4', '#ff8fd4', '#fff5fb'])
    
    
    return gradients[number]

def GradientOfColors(colors, t, degree=1):
    """
    parameters:
        colors [list]: list of colors or hex
    returns:
        color
    """
    if degree == 3 and len(colors) < 4:
        degree = 2
    pts = []
    for color in colors:
        if IsHex(color):
            rgb = hex_to_rgb(color)
            r = rgb[0]
            g = rgb[1]
            b = rgb[2]
        else:
            r = color.R
            g = color.G
            b = color.B
        pts.append(rc.Geometry.Point3d(r, g, b))
    crv = rc.Geometry.NurbsCurve.Create(False, degree, pts)
    samplePt = crv.PointAtNormalizedLength(t)
    r = util.Constrain(samplePt.X, 0, 255)
    g = util.Constrain(samplePt.Y, 0, 255)
    b = util.Constrain(samplePt.Z, 0, 255)
    return drawing.Color.FromArgb(255, r, g, b)


#Interpolate Colors
def ColorBetweenColors(col1, col2, t = .5):
    """
    colorBetweenColors(col1, col2, t)
    input:
        col1 = rc point
        col2 = rc point
        t = normalized pt between col1 and col2
    return:
        new color point
    """
    r = util.Remap(t, 0, 1, col1.R, col2.R)
    g = util.Remap(t, 0, 1, col1.G, col2.G)
    b = util.Remap(t, 0, 1, col1.B, col2.B)
    return drawing.Color.FromArgb(255, r,g,b)


#Modify Colors
def ChangeBrightness(col, adjustment = 10):
    """
    parameters:
        col (color)
        adjustment (number): + to brighten, - to darken
    return:
        (color)
    """
    r = util.Constrain(col.R + adjustment, 0, 255)
    g = util.Constrain(col.G + adjustment, 0, 255)
    b = util.Constrain(col.B + adjustment, 0, 255)
    return drawing.Color.FromArgb(255,r,g,b)

def ReddenColor(color, correctionFactor):
    red = color.R
    green = color.G
    blue = color.B
    red += correctionFactor
    green += correctionFactor
    blue += correctionFactor
    if red < 0 or red > 255 or green < 0 or green > 255 or blue < 0 or blue > 255:
        return None
    return drawing.Color.FromArgb(color.A, 255,green, blue)

def WalkColor(color, amount):
    """Randomly changes the RGB by a maximum random Amount
    parameters:
        color (color)
        amount (int or float):  maximum random deviation
    returns:
        color
    
    This shold be changed so the amount = a random vector of length. This way it guarentees a distances covered by the step.
    """
    rAmount = random.uniform(-amount ,amount)
    red = util.Constrain(color.R + rAmount,100, 220)
    gAmount = random.uniform(-amount ,amount)
    green = util.Constrain(color.G + gAmount, 100, 220)
    bAmount = random.uniform(-amount ,amount)
    blue = util.Constrain(color.B + bAmount, 100, 220)
    return drawing.Color.FromArgb(color.A, red, green, blue)

def ChangeColorBrightness(col, factor):
    """
    parameters:
        col (color): color to adjust
        factor (float): multiply brightness. (.9 darkens, 1.1 brightens)
    returns:
        (color): new Color object
    """
    r = col.R
    g = col.G
    b = col.B
    h, l, s = rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    l = max(min(l * factor, 1.0), 0.0)
    r, g, b = hls_to_rgb(h, l, s)
    return drawing.Color.FromArgb(255, int(r * 255), int(g * 255), int(b * 255))

#Utility
def hex_to_rgb(value):
    """converts hex to RGB
    parameters:
        value (str): eg. '#3d72b4'
    returns:
        (tuple): r,g,b
    """
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def IsHex(value):
    """checks if first character is a '#'
    """
    try:
        valStr = str(value)
        if valStr[0] == '#':
            return True
        else:
            return False
    except:
        return False



if __name__ == "__main__":
    attr0 = rc.DocObjects.ObjectAttributes()
    attr0.ColorSource = rc.DocObjects.ObjectColorSource.ColorFromObject
    attr0.ObjectColor = drawing.Color.White
    
    id0 =  rs.coerceguid("fc9f0f50-68f7-483b-88ef-55c7e38c3bab")
    id1 =  rs.coerceguid("e4fb7017-3d8b-4ae0-8a50-8be50ad38476")
    id2 =  rs.coerceguid("dae1b0b6-0c67-4659-956d-196e38c93898")
    attr0.ObjectColor = GetRandomNamedColor()
    attr1 = attr0.Duplicate()
    attr2 = attr0.Duplicate()
    for i in range(100):
        attr1.ObjectColor = ChangeColorBrightness(attr1.ObjectColor, 1.1)
        attr2.ObjectColor = ChangeColorBrightness(attr2.ObjectColor, .9)
        
        
        sc.doc.Objects.ModifyAttributes(id0, attr0, True)
        sc.doc.Objects.ModifyAttributes(id1, attr1, True)
        sc.doc.Objects.ModifyAttributes(id2, attr2, True)
        sc.doc.Views.Redraw()
        rs.Sleep(10)
