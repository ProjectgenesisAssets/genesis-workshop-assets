"""Genesis V019 — linen free end, physically cut instead of needle-shaped.
Preserves the V018 bobbin/winding and scanned CC0 PBR. Only the thread end is changed.
"""
import math
from mathutils import Vector
_v018_cord=cord
def cord(hemp):
    result=_v018_cord(hemp)
    if hemp:return result
    tail=next((o for o in objects if o.name.startswith("linen_loose_tail")),None)
    if tail is None:raise RuntimeError("V019: cannot locate attached linen loose tail")
    rings=90;sides=6
    if len(tail.data.vertices)!=rings*sides:
        raise RuntimeError("V019: tail topology changed; refusing blind corrections")
    # Shorter drooping continuation: V018 ended in an unrealistically long needle.
    # Endpoint radius remains real instead of collapsing to a cone.
    for j in range(rings):
        t=j/(rings-1)
        curve=t*.86
        xc=.227+.12*curve+.038*math.sin(math.pi*curve)+.016*curve*curve
        yc=.10+.18*curve+.025*math.sin(math.pi*curve)
        zc=.017+.085*math.cos(math.pi*.9*curve)-.073*curve*curve
        # Thread's main diameter stays fairly constant, with tiny natural slubs.
        r=.0036*(1+.07*math.sin(t*21.3))*(1-.10*max(0,(t-.92)/.08))
        for i in range(sides):
            phi=2*math.pi*i/sides
            vertex=tail.data.vertices[j*sides+i]
            vertex.co=(xc+r*math.cos(phi),
                       yc+r*math.sin(phi),
                       zc+.81*r*math.sin(phi))
    tail.data.update()
    # Close the actual tube at its cut; visible end isn't a hollow black hole.
    tip=[tail.data.vertices[(rings-1)*sides+k].co.copy() for k in range(sides)]
    center=sum(tip,Vector((0,0,0)))/sides
    capverts=[tuple(v) for v in tip]+[tuple(center)]
    mesh("V019_real_linen_cut_cross_section",capverts,
         [(i,(i+1)%sides,sides) for i in range(sides)],
         uv=[(.5+.4*math.cos(2*math.pi*k/sides),
              .5+.4*math.sin(2*math.pi*k/sides)) for k in range(sides)]+[(.5,.5)],
         mats=[mat])
    # 7 rooted fibers: short, separated, varied lengths and splay. Genuine geometry,
    # each anchored on the actual cut perimeter. Never a spike or disjoint hairs.
    tangent=center-(sum([tail.data.vertices[(rings-4)*sides+k].co.copy()
                         for k in range(sides)],Vector((0,0,0)))/sides)
    tangent.normalize()
    for k in range(7):
        phi=2*math.pi*k/7
        radial=Vector((math.cos(phi),math.sin(phi),.27*math.sin(phi+.4)))
        radial.normalize()
        root=center+radial*.0020
        L=.008+.0035*(k%3)+.0020*math.sin(k*2.1)
        direction=(tangent+radial*(.20+.06*(k%2))).normalized()
        fiber=[]
        uv=[]
        Ns=5;segs=4
        for j in range(segs):
            q=j/(segs-1)
            pos=root+direction*L*q+radial*(.0014*q*q)
            radius=.00063*(1-q*.65)
            sideways=direction.cross(Vector((0,0,1))).normalized()
            if sideways.length<.1:sideways=Vector((1,0,0))
            other=direction.cross(sideways).normalized()
            for i in range(Ns):
                a=2*math.pi*i/Ns
                fiber.append(tuple(pos+radius*(math.cos(a)*sideways+math.sin(a)*other)))
                uv.append((q,k/7+i/Ns/7))
        faces=[]
        for j in range(segs-1):
            for i in range(Ns):
                a=j*Ns+i;b=j*Ns+(i+1)%Ns
                faces.append((a,b,b+Ns,a+Ns))
        mesh("V019_attached_flax_fiber_%02d"%k,fiber,faces,uv=uv,mats=[mat])
    return result
