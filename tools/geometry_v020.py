"""V020 linen — fix floating strand by tracing a connected path over the flange.
The thread exits the actual outermost winding, clears the spool rim and then
rests close to the outer flange face. Preserve the V019 fibers and 4K CC0 PBR.
No fake geometry scan claims or game integration.
"""
import math
from mathutils import Vector
_previous_v019_cord=cord

def _catmull(p0,p1,p2,p3,t):
    return .5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*(t*t)
                 +(-p0+3*p1-3*p2+p3)*(t*t*t))

def cord(hemp):
    result=_previous_v019_cord(hemp)
    if hemp: return result
    yarn=next((o for o in objects if o.name=="hand_wound_natural_linen_thread_36_turns"),None)
    loose=next((o for o in objects if o.name=="linen_loose_tail"),None)
    if yarn is None or loose is None:
        raise RuntimeError("V020 missing original wound yarn or loose end")
    turns,steps,sides=36,46,6
    if len(yarn.data.vertices)!=turns*steps*sides or len(loose.data.vertices)!=90*6:
        raise RuntimeError("V020 refusing unknown topology")
    # Remove V019's loose-tip geometry BEFORE moving the physical end.
    # Otherwise old fibers remain visibly floating at the abandoned position.
    for old in list(objects):
        if old.name=="V019_real_linen_cut_cross_section" or old.name.startswith("V019_attached_flax_fiber_"):
            objects.remove(old)
            bpy.data.objects.remove(old,do_unlink=True)
    # Reorient the winding around its cylindrical axis, keeping all individual turns.
    # The actual terminal loop comes to the top/front, rather than a back-facing seam.
    spin=1.74
    cs,sn=math.cos(spin),math.sin(spin)
    for vert in yarn.data.vertices:
        y,z=vert.co.y,vert.co.z
        vert.co.y=cs*y-sn*z
        vert.co.z=sn*y+cs*z
    yarn.data.update()
    terminal=(turns*steps-1)*sides
    root=sum((yarn.data.vertices[terminal+k].co.copy() for k in range(sides)),Vector((0,0,0)))/sides
    # Exact anchor, not arbitrary world coordinates; no visible gap is permitted.
    # The flange body spans x~.258 to .302 and has r<=.139. Route OVER its rim.
    points=[
      root,
      Vector((root.x+.009,root.y-.010,root.z+.036)),
      Vector((.253,-.027,.153)),
      Vector((.274,-.029,.158)),
      Vector((.305,-.034,.161)),
      Vector((.308,-.045,.147)),
      Vector((.308,-.052,.122)),
    ]
    nring=90;nside=6
    centers=[]
    for j in range(nring):
        z=j/(nring-1)*(len(points)-1)
        index=min(int(z),len(points)-2)
        t=z-index
        centers.append(_catmull(points[max(index-1,0)],points[index],
                                points[index+1],points[min(index+2,len(points)-1)],t))
    # Ensure there is no path through the thickness of either wooden flange:
    # require a gap sufficient for the thread's own cross-section.
    min_rim_clear=10.0
    for p in centers:
        r=math.hypot(p.y,p.z)
        if .259<=p.x<=.302:
            margin=r-.139-.0046
            min_rim_clear=min(min_rim_clear,margin)
            if margin < -.0002:
                raise RuntimeError("V020 thread intersects the wooden flange: "+str(margin))
    # Orient each tube ring using the local curve tangent; no flattened spike.
    for j,p in enumerate(centers):
        tangent=(centers[min(j+1,nring-1)]-centers[max(j-1,0)]).normalized()
        lateral=tangent.cross(Vector((0,0,1)))
        if lateral.length<.1: lateral=tangent.cross(Vector((0,1,0)))
        lateral.normalize()
        up=tangent.cross(lateral).normalized()
        t=j/(nring-1)
        radius=(.00455-.00105*t)*(1+.045*math.sin(t*13.2))
        for k in range(nside):
            phi=2*math.pi*k/nside
            q=p+radius*(math.cos(phi)*lateral+math.sin(phi)*up)
            loose.data.vertices[j*nside+k].co=q
    loose.data.update()
    # Close the cut section and add only 5 short, slightly bent, anchored fibers.
    # No long hairs that read as a second levitating string.
    end=centers[-1]
    tangent=(centers[-1]-centers[-4]).normalized()
    ring=[loose.data.vertices[(nring-1)*nside+k].co.copy() for k in range(nside)]
    vertices=[tuple(p) for p in ring]+[tuple(end)]
    uvs=[(.5+.4*math.cos(2*math.pi*k/nside),.5+.4*math.sin(2*math.pi*k/nside)) for k in range(nside)]+[(.5,.5)]
    mesh("V020_flax_cut_closed_surface",vertices,
         [(k,(k+1)%nside,nside) for k in range(nside)],uv=uvs,mats=[mat])
    for i in range(5):
        a=2*math.pi*i/5
        normal=Vector((math.cos(a),math.sin(a),.17*math.sin(a+.8))).normalized()
        start=end+normal*.0019-tangent*.00065
        length=.0058+.0021*(i%3)
        direction=(tangent+.17*normal).normalized()
        bend=(tangent+.34*normal).normalized()
        sections=4;sides=5
        vv=[];uv=[];ff=[]
        axis=direction.cross(Vector((0,0,1))).normalized()
        if axis.length<.05:axis=Vector((1,0,0))
        perpendicular=direction.cross(axis).normalized()
        for j in range(sections):
            t=j/(sections-1)
            p=start+direction*length*t+bend*.0008*(t*t)
            rad=.00058*(1-.75*t)
            for k in range(sides):
                ang=2*math.pi*k/sides
                vv.append(tuple(p+rad*(math.cos(ang)*axis+math.sin(ang)*perpendicular)))
                uv.append((t,(i+k/sides)/5))
        for j in range(sections-1):
            for k in range(sides):
                x=j*sides+k;y=j*sides+(k+1)%sides
                ff.append((x,y,y+sides,x+sides))
        mesh("V020_short_attached_linen_cut_fiber_%02d"%i,vv,ff,uv=uv,mats=[mat])
    anchor_err=(centers[0]-root).length
    if anchor_err > 0.000001:
        raise RuntimeError("V020 thread root not attached: "+str(anchor_err))
    if not (.302 < end.x < .317):
        raise RuntimeError("V020 tip is not resting near the outer flange")
    if end.x-.302 > .012:
        raise RuntimeError("V020 thread visibly floating beyond flange")
    globals()["_v020_physical_report"]={
      "root_gap_m":anchor_err,
      "flange_min_clearance_m":min_rim_clear,
      "outside_flange_face_gap_m":end.x-.302,
      "route_length_m":sum((centers[i]-centers[i-1]).length for i in range(1,len(centers))),
      "free_fibers":5,
      "crosses_flange_without_intersection":True,
    }
    return result
