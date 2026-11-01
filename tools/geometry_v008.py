"""Genesis V008 art direction: thick split firewood, distinct hide drape, imperfect hand-wound fibers.
Requires mesh(), mat, objects, K, random, bpy, math, Vector from asset_v008.py.
Everything here is generated geometry; no photographic-geometry claims."""
from math import sin,cos,pi,exp
_old_hide_v007=hide
_old_cord_v007=cord
def wood_piece(label,oak,offset):
    # A half-log (thick arched bark side and deeply torn radial plane), not a wavy plank.
    length=(1.36 if oak else 1.51)*(1+.065*offset)
    radius=.246 if oak else .185
    nring=54;exterior=19;split=16;n=exterior+split
    verts=[];uv=[];faces=[];matids=[]
    bark=v4_bark_material()
    endgrain=v4_endgrain_material()
    for j in range(nring):
        t=j/(nring-1)
        r=radius*(1-.12*t+.033*sin(t*7+offset))
        for i in range(n):
            if i<exterior:
                theta=pi*i/(exterior-1)
                x=r*cos(theta)
                y=-r*sin(theta)
                x+=.009*sin(10*t+theta*4+.8*offset)
                y+=.008*sin(17*t+theta*9)
            else:
                h=(i-exterior+1)/(split+1)
                x=r*(-1+2*h)
                # Characteristic longitudinal tear: waves travel parallel to wood grain.
                y=.035+.014*sin(h*17+2*t)+.020*sin(t*10+h*7+offset)
                y+=.015*(1 if oak else .60)*sin(h*34-9*t)
            # Randomness of breakage remains *localized to the two broken ends*.
            edge_break=(1-t)**8*(.021+.028*sin(i*3.47+offset)**2)
            edge_break-=t**8*(.027+.05*sin(i*5.41+offset)**2)
            z=length*(t-.5)+edge_break+.004*sin(t*25+i*.6)
            verts.append((x,y,z))
            uv.append((t*2.15,i/(n-1)))
    for j in range(nring-1):
        for i in range(n):
            a=j*nring*0+j*n+i
            b=j*n+(i+1)%n
            faces.append((a,b,b+n,a+n))
            matids.append(1 if i<exterior-1 else 0)
    faces.append(tuple(reversed(range(n))));matids.append(2)
    faces.append(tuple((nring-1)*n+i for i in range(n)));matids.append(2)
    ob=mesh(label,verts,faces,uv=uv,mats=[mat,bark,endgrain],side_indices=matids)
    lay=ob.data.uv_layers.active
    for face in list(ob.data.polygons)[-2:]:
        for li in face.loop_indices:
            co=ob.data.vertices[ob.data.loops[li].vertex_index].co
            lay.data[li].uv=(.5+co.x/(radius*2.3),.5+co.y/(radius*2.3))
    # Separate pieces enough to read their actual thickness in a small inventory icon.
    ob.rotation_euler=(.06*offset,1.43+.10*offset,.08*offset)
    ob.location=(offset*.075,offset*.14,offset*.047)
    # Ragged splinters lift from the split surface; small groups, varied alignment.
    for q in range(14 if oak else 11):
        z=random.uniform(-length*.40,length*.39)
        x=random.uniform(-radius*.68,radius*.68)
        y=.046+.020*sin(z*10+x*12+offset)
        h=random.uniform(.085,.31)
        wobble=random.uniform(-.013,.013)
        blade=[(x,y,z),
               (x+.008,y+.013,z+.036),
               (x+wobble,y+random.uniform(.025,.058),min(length*.49,z+h)),
               (x-.009,y+.005,z+min(h*.84,.25))]
        shard=mesh(label+"_split_sliver_%02d"%q,blade,[(0,1,2),(0,2,3)],mats=[mat])
        shard.location=tuple(ob.location)
        shard.rotation_euler=tuple(ob.rotation_euler)
    return ob

def hide(cow):
    # Prior physical hide mesh retained; sculpt each overlapping pelt differently.
    first=len(objects)
    result=_old_hide_v007(cow)
    skins=[o for o in objects[first:] if "folded_hide" in o.name]
    for index,ob in enumerate(skins):
        for v in ob.data.vertices:
            x,y,z=v.co
            if cow:
                # Weight makes wider, shallow creases close to the resting edge.
                crease=.024*exp(-((y+.10)/.11)**2)*sin(x*16+index)
                z+=crease+.009*sin(11*x+4*y)*sin(9*y)
                x+=.018*sin(4*y+index)*max(0,abs(x)-.15)
            else:
                # Thin goat pelt bunches into narrow folds and has a distinct narrow silhouette.
                x*=.79
                y*=1.12
                z+=.020*sin(22*x+10*y+index)*exp(-((y-.06)/.33)**2)
                z+=.015*sin(30*y+5*x)
                if index==1:
                    x+=.085
            v.co=(x,y,z)
        ob.data.update()
        if not cow and index==1:
            ob.rotation_euler.z+=.19
        if cow and index==1:
            ob.rotation_euler.z-=.12
    return result

def cord(hemp):
    result=_old_cord_v007(hemp)
    if hemp:
        # A real cord is manually coiled: local kinks and uneven tension.
        for ob in objects:
            if "natural_hemp_three_strand_coil" not in ob.name:continue
            for v in ob.data.vertices:
                x,y,z=v.co
                a=math.atan2(y,x);radius=math.hypot(x,y)
                drift=.005*sin(a*5.2)+.008*sin(a*2.1+.8*radius)
                v.co.x+=drift*cos(a)
                v.co.y+=drift*sin(a)
                v.co.z+=.006*sin(4*a+radius*20)
            ob.data.update()
    else:
        # Bobbin thread: controlled variations from human winding, without bulky plastic cable.
        for ob in objects:
            if "hand_wound_natural_linen_thread" not in ob.name:continue
            for v in ob.data.vertices:
                x,y,z=v.co
                a=math.atan2(z,y)
                v.co.x+=.0018*sin(a*6.3+x*88)+.0008*sin(a*13+x*70)
                drift=.0018*sin(x*70+a*2.9)
                v.co.y+=drift*cos(a)
                v.co.z+=drift*sin(a)
            ob.data.update()
    return result
