"""V017 targeted fiber refinement. Preserve V016 approved-for-iteration silhouettes.
No fake scans, no gameplay changes, no automatic quality approval.
"""
import math,random
from mathutils import Vector
_prev_cord_v016=cord
def cord(hemp):
    start_count=len(objects)
    result=_prev_cord_v016(hemp)
    if hemp:
        coil=next((o for o in objects[start_count:]
                   if "natural_hemp_three_strand_coil" in o.name),None)
        if coil is None:
            raise RuntimeError("V017: expected V016 true three-ply hemp geometry")
        steps,sides=460,7
        expected=3*steps*sides
        if len(coil.data.vertices)!=expected:
            raise RuntimeError("V017: hemp vertex layout mismatch; refusing blind edit")
        # Physical fibers remain directly anchored to real strand vertices, never floating.
        for part in range(3):
            for i,j in enumerate((8,25,59,93,145,188,247,294,351,414,452)):
                idx=(part*steps+j)*sides+(part+i+j)%sides
                p=coil.data.vertices[idx].co.copy()
                prev=coil.data.vertices[idx-sides].co.copy()
                tangent=(p-prev).normalized()
                sideways=Vector((-tangent.y,tangent.x,.15)).normalized()
                length=.010+.003*((i*7+part)%5)
                end=p+tangent*length+sideways*length*.55
                width=.0015
                blade=[tuple(p),tuple(p+sideways*width),tuple(end)]
                mesh("V017_surface_attached_hemp_fiber_%02d_%02d"%(part,i),
                     blade,[(0,1,2)],mats=[mat])
        return result
    winding=next((o for o in objects[start_count:]
                  if "hand_wound_natural_linen_thread_36_turns" in o.name),None)
    if winding is None:
        raise RuntimeError("V017: expected V016 fine linen wound on actual wooden spool")
    # 36 separate turns. Preserve the thin cross-section and vary axial placement
    # and tension a small amount without making the thread look like a thick cable.
    turns,steps,sides=36,46,6
    if len(winding.data.vertices)!=turns*steps*sides:
        raise RuntimeError("V017: linen winding vertex layout mismatch")
    for turn in range(turns):
        axial=.0038*math.sin(turn*1.61)+.0019*math.sin(turn*3.31)
        for j in range(steps):
            phase=2*math.pi*j/(steps-1)
            tension=.0015*math.sin(phase*3.2+turn*.41)
            for k in range(sides):
                index=(turn*steps+j)*sides+k
                v=winding.data.vertices[index]
                x,y,z=v.co
                v.co.x=x+axial+tension
                rr=math.hypot(y,z)
                warp=1+.018*math.sin(phase*2.2+turn*.63)
                v.co.y=y*warp
                v.co.z=z*warp
    winding.data.update()
    tail=next((o for o in objects[start_count:] if o.name.startswith("linen_loose_tail")),None)
    if tail is not None:
        nr,ns=90,6
        if len(tail.data.vertices)!=nr*ns:
            raise RuntimeError("V017: linen loose-end vertex layout mismatch")
        for j in range(nr):
            t=j/(nr-1)
            cx=sum(tail.data.vertices[j*ns+k].co.x for k in range(ns))/ns
            cy=sum(tail.data.vertices[j*ns+k].co.y for k in range(ns))/ns
            cz=sum(tail.data.vertices[j*ns+k].co.z for k in range(ns))/ns
            taper=1-.67*max(0,(t-.67)/.33)
            for k in range(ns):
                v=tail.data.vertices[j*ns+k]
                x,y,z=v.co
                v.co=(cx+(x-cx)*taper+.016*t*t,
                      cy+(y-cy)*taper+.025*math.sin(math.pi*t),
                      cz+(z-cz)*taper-.073*t*t)
        tail.data.update()
    return result
