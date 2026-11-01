"""Project Genesis V015 — irregular natural forms, not uniform periodic geometry.
Uses approved CC0-PBR source pipeline. All new geometry is authored and needs human review."""
from math import sin, cos, pi, exp
import math
from mathutils import Vector
_previous_wood=wood_piece
_previous_cord=cord

def wood_piece(label,oak,offset):
    ob=_previous_wood(label,oak,offset)
    # V014 had periodic 3-D gouges that resembled a machine-milled washboard.
    # Dampen them while retaining long tear valleys and separate, localized splinters.
    ring_count=58; ring_vertices=44; exterior=25
    if len(ob.data.vertices)!=ring_count*ring_vertices:
        raise RuntimeError("Unexpected hardwood topology; preserving source rather than guessing")
    for j in range(ring_count):
        t=j/(ring_count-1)
        along=.017*sin(t*10.7+.6*offset)+.011*sin(t*25.3+2*offset)
        for k in range(exterior,ring_vertices):
            h=(k-exterior+1)/(ring_vertices-exterior+1)
            vert=ob.data.vertices[j*ring_vertices+k]
            # Reduced regular periodic amplitude, slowly drifting fibrous clefts.
            original=vert.co.y
            natural=.014*sin(h*6.4+t*3.9+offset)
            natural+=.008*sin(h*19.6-t*7.5)
            natural+=.006*sin(h*38.3+t*2.1)
            wedge=.012*(h-.5)*sin(5.3*t+offset)
            vert.co.y=.018+(original-.017)*.30+natural+along+wedge
            # Irregular rift margins rather than perfectly straight scallop edges.
            vert.co.x+=.003*sin(t*16+3.5*h)+.0027*sin(t*29-h*14)
    ob.data.update()
    # V014 showed nearly only the split grain; retain roughly 30% of bark in the view.
    # Apply local-axis adjustment through quaternion to avoid accidental end-on logs.
    from mathutils import Quaternion
    ob.rotation_quaternion=ob.rotation_quaternion @ Quaternion((0,0,1),-.68)
    for child in objects:
        if child.name.startswith(label+"_grain_sliver"):
            child.rotation_mode="QUATERNION"
            child.rotation_quaternion=ob.rotation_quaternion.copy()
    return ob

def hide(cow):
    # Hand-trimmed piece with irregular contour and tension folds.
    # Front/back and narrow edge are separate surfaces of one watertight mesh.
    # A second, partially folded hide makes the inventory material identifiable.
    segments=72
    radial=22
    wide=1.48 if cow else 1.14
    tall=1.17 if cow else 1.06
    thickness=.018 if cow else .008
    for piece in range(2):
        verts=[];uv=[];faces=[]
        for layer in range(2):
            for j in range(radial):
                r=.014+.986*j/(radial-1)
                for i in range(segments):
                    a=2*pi*i/segments
                    # Natural cuts have broad lobes and gentle asymmetric nicks, not a rectangle.
                    outline=1+.050*sin(3*a+.8*piece)
                    outline+=.033*sin(5*a-1.6+piece*.3)+.021*sin(9*a+.5)
                    outline+=.009*sin(17*a+piece*2.4)
                    x=(wide*.5)*r*outline*cos(a)
                    y=(tall*.5)*r*outline*sin(a)
                    x+=r**3*(.038*sin(2*a+1.1)+.018*sin(7*a+piece))
                    y+=r**3*(.027*sin(5*a+.7)+.015*sin(11*a+piece))
                    u=(x/wide)+.5;v=(y/tall)+.5
                    # Fold source has an oblique stress line, which fades towards the center.
                    axis=x*.79+y*.48
                    fold_line=(.057 if cow else .072)*exp(-((axis-(.10-.06*piece))/
                           (.18 if cow else .105))**2)
                    broad=(.060 if cow else .033)*sin(x*4.6+2.1*y+piece*.8)
                    micro=(.009 if cow else .020)*sin(11*x+14*y+piece*.4)*sin(6*y)
                    edge_curl=(.050 if cow else .067)*r**9*(.5+.5*sin(2*a+.6*piece))
                    z=.029+broad+fold_line+micro+edge_curl+(.06 if piece==0 else -.025)
                    # Nonuniform contact: the far edge curls and overlaps the other skin.
                    z+=.041*exp(-((x-.35*wide)/(.23*wide))**2)*r**3
                    if layer:z-=thickness*(1+.12*sin(5*a+piece))
                    verts.append((x+(.085 if piece else -.065),
                                  y+(-.075 if piece else .035),z))
                    uv.append((u,v))
        N=radial*segments
        for layer in range(2):
            base=layer*N
            for j in range(radial-1):
                for i in range(segments):
                    q=(i+1)%segments
                    a=base+j*segments+i
                    b=base+j*segments+q
                    c=b+segments;d=a+segments
                    faces.append((a,d,c,b) if layer==0 else (b,c,d,a))
        # Stitch outer perimeter in real geometry; keep it visibly thin.
        for i in range(segments):
            q=(i+1)%segments
            a=(radial-1)*segments+i;b=(radial-1)*segments+q
            faces.append((a,N+a,N+b,b))
        faces.append(tuple(range(segments)))
        faces.append(tuple(N+i for i in reversed(range(segments))))
        ob=mesh(("cowhide" if cow else "goatskin")+"_curved_tanned_pelt_"+str(piece),
                verts,faces,uv=uv,mats=[mat])
        ob.rotation_euler=(.015 if cow else .06,0,(-.10 if piece else .13))
    return ob

def cord(hemp):
    item=_previous_cord(hemp)
    if hemp:
        # Soft localized deformations, not random stray fibers.
        for ob in objects:
            if "natural_hemp_three_strand_coil" not in ob.name:continue
            for v in ob.data.vertices:
                x,y,z=v.co
                a=math.atan2(y,x);rr=math.hypot(x,y)
                deviation=.0035*sin(4.3*a+rr*17)
                deviation+=.002*sin(12.3*a+rr*3)
                v.co.x+=deviation*cos(a)
                v.co.y+=deviation*sin(a)
            ob.data.update()
    else:
        # Tiny tension irregularities: actual linen strand remains slender.
        for ob in objects:
            if "hand_wound_natural_linen_thread" not in ob.name:continue
            for v in ob.data.vertices:
                x,y,z=v.co
                ripple=.0013*sin(52*x+6*math.atan2(z,y))
                v.co.y+=ripple
                v.co.z+=ripple*.62
            ob.data.update()
    return item
