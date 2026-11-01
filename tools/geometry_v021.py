"""V021 linen: remove the staple-like over-flange arc (V020) and tuck the short end
onto the last real thread wraps. Independent candidate; no game integration.
"""
import math
from mathutils import Vector
_old_v020_cord=cord
def _v021_catmull(a,b,c,d,t):
    return .5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*(t*t)+(-a+3*b-3*c+d)*(t*t*t))

def cord(hemp):
    result=_old_v020_cord(hemp)
    if hemp:return result
    yarn=next((o for o in objects if o.name=="hand_wound_natural_linen_thread_36_turns"),None)
    tail=next((o for o in objects if o.name=="linen_loose_tail"),None)
    if not yarn or not tail:raise RuntimeError("V021 needs actual V020 yarn and end")
    # Remove V020's obsolete staple tip and fray. Keep only real spool/winding/tail.
    for old in list(objects):
        if old.name=="V020_flax_cut_closed_surface" or old.name.startswith("V020_short_attached_linen_cut_fiber_"):
            objects.remove(old)
            bpy.data.objects.remove(old,do_unlink=True)
    turns,steps,sides=36,46,6
    nring=90
    if len(yarn.data.vertices)!=turns*steps*sides or len(tail.data.vertices)!=nring*sides:
        raise RuntimeError("V021 winding topology mismatch")
    last=(turns*steps-1)*sides
    root=sum((yarn.data.vertices[last+k].co.copy() for k in range(sides)),Vector((0,0,0)))/sides
    # Tuck free yarn along the existing upper wraps instead of projecting a handle
    # above the flange. Each point is very close to the underlying winding surface.
    points=[
        root,
        root+Vector((-.007,-.002,+.008)),
        root+Vector((-.022,-.003,+.010)),
        root+Vector((-.039,-.005,+.008)),
        root+Vector((-.055,-.005,+.004)),
    ]
    centers=[]
    for j in range(nring):
        z=(len(points)-1)*j/(nring-1)
        index=min(int(z),len(points)-2)
        t=z-index
        centers.append(_v021_catmull(points[max(index-1,0)],points[index],
                                    points[index+1],points[min(index+2,len(points)-1)],t))
    for j,p in enumerate(centers):
        tangent=(centers[min(j+1,nring-1)]-centers[max(j-1,0)]).normalized()
        side=tangent.cross(Vector((0,0,1)))
        if side.length<.05:side=tangent.cross(Vector((0,1,0)))
        side.normalize()
        up=tangent.cross(side).normalized()
        t=j/(nring-1)
        radius=(.0046-.0013*t)*(1+.04*math.sin(t*11))
        for k in range(sides):
            phi=2*math.pi*k/sides
            tail.data.vertices[j*sides+k].co=p+radius*(math.cos(phi)*side+math.sin(phi)*up)
    tail.data.update()
    end=centers[-1]
    # The terminal cut is real geometry, not a hollow cap or one oversized hair.
    perimeter=[tail.data.vertices[(nring-1)*sides+k].co.copy() for k in range(sides)]
    mesh("V021_tucked_linen_cross_section",list(map(tuple,perimeter))+[tuple(end)],
         [(i,(i+1)%sides,sides) for i in range(sides)],
         uv=[(.5+.4*math.cos(2*math.pi*i/sides),.5+.4*math.sin(2*math.pi*i/sides)) for i in range(sides)]+[(.5,.5)],
         mats=[mat])
    direction=(centers[-1]-centers[-4]).normalized()
    for i in range(5):
        angle=2*math.pi*i/5
        radial=Vector((math.cos(angle),math.sin(angle),.14*math.sin(angle+.5))).normalized()
        source=end+radial*.0018-direction*.0005
        length=.0035+.0014*(i%3)
        tangent=(direction+.2*radial).normalized()
        axis=tangent.cross(Vector((0,0,1)))
        if axis.length<.05:axis=Vector((1,0,0))
        axis.normalize()
        up=tangent.cross(axis).normalized()
        vert=[];uv=[];faces=[]
        ring_count=4;edges=5
        for j in range(ring_count):
            t=j/(ring_count-1)
            p=source+tangent*length*t+radial*.0005*t*t
            radius=.00048*(1-.70*t)
            for k in range(edges):
                ang=2*math.pi*k/edges
                vert.append(tuple(p+radius*(math.cos(ang)*axis+math.sin(ang)*up)))
                uv.append((t,i/5+k/edges/5))
        for j in range(ring_count-1):
            for k in range(edges):
                a=j*edges+k;b=j*edges+(k+1)%edges
                faces.append((a,b,b+edges,a+edges))
        mesh("V021_short_tucked_cut_fiber_%02d"%i,vert,faces,uv=uv,mats=[mat])
    # Mechanical proximity check against existing photographic yarn geometry.
    last_distance=min((end-v.co).length for v in yarn.data.vertices)
    sample_gaps=[]
    for j in range(0,nring,10):
        center=centers[j]
        sample_gaps.append(min((center-v.co).length for v in yarn.data.vertices))
    root_error=(centers[0]-root).length
    if root_error>0.000001:raise RuntimeError("V021 free end detached")
    if last_distance>0.018:raise RuntimeError("V021 cut tip is still visibly floating")
    if max(sample_gaps)>0.022:raise RuntimeError("V021 tail floats above the wound yarn")
    if max(p.x for p in centers)>.256:raise RuntimeError("V021 tail unexpectedly intersects flange")
    globals()["_v021_root"]=tuple(root)
    globals()["_v021_tip"]=tuple(end)
    globals()["_v021_attachment_report"]={
      "root_gap_m":root_error,
      "cut_to_wound_surface_vertex_m":last_distance,
      "max_centerline_nearest_winding_vertex_m":max(sample_gaps),
      "never_crosses_flange":True,
      "attached_short_cut_fibers":5,
      "free_tail_length_m":sum((centers[i]-centers[i-1]).length for i in range(1,nring)),
      "visual_approval":False
    }
    return result
