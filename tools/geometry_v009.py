"""Genesis V009 studio art pass: show split grain, make hide folds asymmetric and naturalize fiber ends."""
from math import sin,cos,pi,exp
_v008_wood_piece=wood_piece
_v008_hide=hide
_v008_cord=cord
def wood_piece(label,oak,offset):
    ob=_v008_wood_piece(label,oak,offset)
    # Correct camera-facing cross section: prominently expose split wood (not only round bark).
    # A quarter twist reveals the torn upper face at 3/4 inventory viewing angle.
    ob.rotation_euler.x=.93+.11*offset
    # All splinter shards must follow the parent rotation.
    for child in objects:
        if child.name.startswith(label+"_split_sliver"):
            child.rotation_euler=tuple(ob.rotation_euler)
    # Readable non-planar cut end with coherent growth rings, retained in the endgrain shader.
    return ob
def hide(cow):
    first=len(objects)
    result=_v008_hide(cow)
    parts=[o for o in objects[first:] if "folded_hide" in o.name]
    for idx,ob in enumerate(parts):
        # Tension distributes folds toward contact points; no perfectly repeated pair of sheets.
        for v in ob.data.vertices:
            x,y,z=v.co
            edge=min(1.0,abs(x)/(.67 if cow else .46))
            rim=min(1.0,abs(y)/(.52 if cow else .56))
            if cow:
                z+=.018*exp(-((x-.25)/.18)**2)*sin(13*y+idx)
                y+=.019*edge*sin(7*x+idx*2.1)
                z+=.018*rim**3*sin(x*15+2*y)
            else:
                z+=.035*exp(-((x+.18)/.16)**2)*sin(21*y+3*x)
                y+=.026*edge*sin(17*x+idx)
                x+=.029*rim*sin(11*y+idx)
            v.co=(x,y,z)
        ob.data.update()
        if idx==1:
            ob.location.y-=.035 if cow else .056
            ob.rotation_euler.z+=(0.08 if cow else -.19)
    return result
def cord(hemp):
    first=len(objects)
    result=_v008_cord(hemp)
    if hemp:
        # Uneven ends with isolated elementary flax/hemp fibers, not a perfect geometric screw.
        # Small branching frays are part of the GLB mesh, including at inventory scale.
        r=.55
        for i in range(9):
            a=.13*i+1.3
            x=.52+.009*sin(i*2.7);y=-.12+.008*cos(i*2.4);z=.05+.008*sin(i*4)
            length=.025+.012*(i%3)
            dx=length*cos(a);dy=length*sin(a)
            pts=[(x,y,z),(x+dx,y+dy,z+.018),
                 (x+1.02*dx+.002,y+1.01*dy,z+.020)]
            mesh("hemp_open_end_fibril_%02d"%i,pts,[(0,1,2)],mats=[mat])
    else:
        # A linen thread on a wooden spool must remain fine; a small axial warp makes
        # wound turns organic rather than manufactured plastic ridges.
        for ob in objects[first:]:
            if not "hand_wound_natural_linen" in ob.name:continue
            for v in ob.data.vertices:
                v.co.y*=.985
                v.co.z*=.985
            ob.data.update()
    return result
