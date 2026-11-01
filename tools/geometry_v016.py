"""Project Genesis V016: physically motivated leather crease lines and linen winding drift.
Preserve V015 hardwoods (their visual realism improved), prior art and source provenance."""
from math import sin, cos, pi, exp
import math
_previous_wood_v015=wood_piece
_previous_hide_v015=hide
_previous_cord_v015=cord

def hide(cow):
    result=_previous_hide_v015(cow)
    name="cowhide" if cow else "goatskin"
    layers=[o for o in objects if name+"_curved_tanned_pelt_" in o.name]
    if len(layers)!=2:raise RuntimeError("Expected two independent natural-hide pieces")
    for i,ob in enumerate(layers):
        # Fold ridges converge near two physical stress points rather than periodic waves.
        # Both front and underside receive the same displacement, preserving thickness.
        for v in ob.data.vertices:
            x,y,z=v.co
            axis=.70*x+.71*y
            near=exp(-((x+.02)/(.65 if cow else .50))**2)
            if cow:
                main=.075*exp(-((axis-(.06-.03*i))/.13)**2)*near
                hollow=-.022*exp(-((axis+.145)/.10)**2)
                diagonal=.025*exp(-((.38*x-.92*y-.08)/.12)**2)
                edge=.021*exp(-((y+.45)/.14)**2)*sin(10*x+.8*i)
                z+=main+hollow+diagonal+edge
            else:
                # Goatskin: noticeably thinner and with shorter, more closely grouped folds.
                main=.050*exp(-((axis-(.07-.05*i))/.072)**2)
                second=.034*exp(-((axis+.18)/.068)**2)
                elbow=.020*exp(-((.9*x-.43*y+.16)/.07)**2)
                wav=.011*sin(17*x+11*y+i)*exp(-(x/.48)**2)
                z+=main+second+elbow+wav
            v.co.z=z
        if i==1:
            # Open the stacked hide to reveal a convincing curved lower edge.
            ob.rotation_euler.z+=.23 if cow else -.16
            ob.location.x+=.055 if cow else -.078
            ob.location.y+=.023
        ob.data.update()
    return result

def cord(hemp):
    item=_previous_cord_v015(hemp)
    if not hemp:
        # Hand-wound flax is irregular over the *axis* and the material should
        # read as fine natural thread, not a rigid corrugated plastic cylinder.
        for ob in objects:
            if "hand_wound_natural_linen_thread" not in ob.name:continue
            for v in ob.data.vertices:
                x,y,z=v.co
                phase=math.atan2(z,y)
                warp=.0018*sin(67*x+4.9*phase)+.0007*sin(123*x+2.3*phase)
                v.co.x+=warp
                v.co.y+=.0013*sin(x*58+phase*3.5)
                v.co.z+=.0011*sin(x*49+phase*4.1)
            ob.data.update()
    return item
