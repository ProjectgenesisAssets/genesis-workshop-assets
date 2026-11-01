"""Genesis V019 silhouette differentiation, art-direction after review of 4 actual renders.

The V017 cow/goat rolls shared essentially the same parametric formula at two
scales; the V018 oak/ash split logs similarly shared a cross section. This
pass distinguishes shape, drape, grain stresses and scale WITHOUT inventing
species-specific scans. Approved hemp/linen are not touched.
"""
from math import sin,cos,pi,exp
import math
_prev_wood_018=wood_piece
_prev_hide_017=hide

def wood_piece(label,oak,offset):
    ob=_prev_wood_018(label,oak,offset)
    rings,cols,arc=64,56,33
    if len(ob.data.vertices)!=rings*cols:
        raise RuntimeError("V019 expected a single 64x56 split wood shell")
    for j in range(rings):
        t=j/(rings-1)
        for k in range(cols):
            v=ob.data.vertices[j*cols+k]
            x,y,z=v.co
            if oak:
                # Oak: SHORTER, CHUNKIER, deep irregular bark silhouette.
                # Ridge follows radial grain and broad end-check tears, not a clone
                # of ash with darker color.
                x*=.94
                z=.032+(z-.032)*1.12
                if k<arc:
                    a=-pi/2+pi*k/(arc-1)
                    y*=1.11+.043*sin(a*6.1+t*19.5)
                    z+=.007*sin(t*15.3+a*9.4)
                else:
                    h=(k-arc+1)/(cols-arc+1)
                    y+=.016*exp(-((h-(.31+.08*sin(t*4.5)))/.095)**2)
                    y-=.014*exp(-((h-(.71-.04*sin(t*6.3)))/.06)**2)
                    y+=.0045*sin(7*h+5.1*t)
                    # longitudinal crack near the end: do not add a separate object
                    if t>.76:
                        y-=.010*(t-.76)/.24*exp(-((h-.52)/.10)**2)
            else:
                # Ash: LONG, THIN, springy split with gently ribbon-like tearing.
                # Its bark occupies only a narrow rim in the inventory view.
                x*=1.08
                z=.032+(z-.032)*.80
                if k<arc:
                    y*=.76
                else:
                    h=(k-arc+1)/(cols-arc+1)
                    y+=.0065*sin(3.9*t+6.1*h)
                    y+=.0035*sin(13.4*t-17.2*h)
                    # irregular long continuous split ridge, no oak's coarse gouges
                    y+=.007*exp(-((h-(.57+.06*sin(3.1*t)))/.09)**2)
                    z+=.005*sin(2.7*t+h*2.1)*exp(-((h-.65)/.23)**2)
            v.co=(x,y,z)
    ob.data.update()
    ob.rotation_euler.x=.94 if oak else .04
    ob.rotation_euler.z=-.07 if oak else .10
    ob["species_silhouette_profile"]="chunky, bark-rich, checked ends" if oak else "slender, pale split ribbon, narrow bark rim"
    ob["single_piece_no_overlap"]=True
    return ob

def hide(cow):
    ob=_prev_hide_017(cow)
    width_steps=25;path_steps=192;one_surface=width_steps*path_steps
    if len(ob.data.vertices)!=2*one_surface:
        raise RuntimeError("V019 leather mesh changed; do not deform blind")
    for layer in range(2):
        for j in range(path_steps):
            t=j/(path_steps-1)
            q=max(0.,(t-.73)/.27)
            for i in range(width_steps):
                u=i/(width_steps-1)
                idx=layer*one_surface+j*width_steps+i
                v=ob.data.vertices[idx]
                x,y,z=v.co
                if cow:
                    # Broad heavy bovine roll: upper sheet remains settled, with
                    # widely spaced load-bearing creases rather than sharp goat folds.
                    x*=1.06
                    z+=.009*exp(-((u-.32)/.16)**2)*q
                    z+=.006*exp(-((u-.75)/.12)**2)*q*q
                    y-=.018*q**2*(.45+.55*u)
                    if q>.6:z-=.005*(q-.6)/.4
                else:
                    # Smaller goat hide, *independently shaped*: roll tilted and
                    # upper flap wraps diagonally; one front corner peels slightly
                    # upward. Fine concentrated folds and soft asymmetric edges.
                    x*=.94
                    x+=.19*q*q*(u-.5)
                    y+=.15*q*q*(u-.5)
                    front_corner=max(0.,(u-.60)/.40)**2 * q**3
                    z+=.075*front_corner
                    z+=.012*sin(19*u+3.1*q)*q**2
                    z+=.016*exp(-((u-.36)/.065)**2)*q
                    z+=.013*exp(-((u-.68)/.07)**2)*q
                    if t<=.73:
                        z+=.022*(u-.5)*sin(t*2.6*pi)
                        y+=.018*(u-.5)*sin(t*1.9*pi)
                v.co=(x,y,z)
    ob.data.update()
    ob.rotation_euler.z=.025 if cow else -.31
    ob["physical_style"]="wide heavy flat hanging roll" if cow else "compact diagonal soft roll with corner curl"
    ob["species_identification"]="visual morphology hypothesis only, not scan-verified"
    ob["one_skin_no_duplicates"]=True
    return ob
