"""Genesis V013: distinct hand-split hardwood + cured skins + hand-laid hemp.
Scanned CC0 images are retained for PBR; meshes are authored, not scan geometry.
Each candidate remains unapproved until visual QA."""
from math import sin, cos, pi, exp
import math
_prior_cord=cord
_prior_linen=cord
def wood_piece(label,oak,offset):
    # Physically separate split hardwood logs: semicircular bark outside, torn radial interior.
    N=25; INNER=19; RINGS=58; rad=.235 if oak else .188
    length=(1.35 if oak else 1.53)*(1+.065*offset)
    verts=[];uv=[];faces=[];mat_index=[]
    bark=v4_bark_material();end=v4_endgrain_material()
    for j in range(RINGS):
        t=j/(RINGS-1)
        rr=rad*(1-.16*t+.025*sin(t*8.1+offset))
        curve=.016*sin(2*pi*t+.2*offset)
        for k in range(N+INNER):
            if k<N:
                a=pi*k/(N-1)
                x=rr*cos(a)+.006*sin(3*t+a*9)
                y=-rr*sin(a)*(1+.06*sin(2*pi*t+3*a))
            else:
                h=(k-N+1)/(INNER+1)
                x=rr*(-1+2*h)
                # Longitudinal torn-fiber ridges and fracture valleys.
                y=.017+.020*sin(h*11+t*2.7+offset)+.013*sin(h*31-t*8.0)
                y+=.011*(1 if oak else .65)*sin(h*27+t*17)
            x+=curve
            # Broken/stepped ends, without destroying original axial wood grain.
            end_left=(1-t)**9*(.033*sin(k*5.1+offset)**2)
            end_right=t**10*(.048*sin(k*3.67+.5*offset)**2)
            z=length*(t-.5)+end_left-end_right+.005*sin(k*.8+12*t)
            verts.append((x,y,z))
            uv.append((t*(2.0 if oak else 2.6),k/(N+INNER-1)))
    n=N+INNER
    for j in range(RINGS-1):
        for k in range(n):
            a=j*n+k;b=j*n+(k+1)%n
            faces.append((a,b,b+n,a+n))
            mat_index.append(1 if k<N-1 else 0)
    faces.append(tuple(reversed(range(n))));mat_index.append(2)
    faces.append(tuple((RINGS-1)*n+k for k in range(n)));mat_index.append(2)
    ob=mesh(label,verts,faces,uv=uv,mats=[mat,bark,end],side_indices=mat_index)
    # Endgrain receives independent radial UVs (side grain is NOT projected onto endcaps).
    layer=ob.data.uv_layers.active
    for face in list(ob.data.polygons)[-2:]:
        for li in face.loop_indices:
            vv=ob.data.vertices[ob.data.loops[li].vertex_index].co
            layer.data[li].uv=(.5+vv.x/(2.1*rad),.5+vv.y/(2.1*rad))
    # Horizontal, imperfect pile. Split faces are angled towards three-quarter camera.
    ob.rotation_euler=(.12+.07*offset,1.45+.08*offset,.10*offset)
    ob.location=(.01+.10*offset,.11*offset,.037*offset)
    # Only attached splinters with the same transform as their parent.
    for q in range(9 if oak else 7):
        t=random.uniform(.10,.85)
        z=length*(t-.5)
        x=random.uniform(-rad*.60,rad*.60)
        y=.026+.017*sin((x/rad)*11+t*8+offset)
        L=random.uniform(.13,.28)
        v=[(x,y,z),(x+.006,y+.009,z+.025),
           (x+random.uniform(-.009,.009),y+random.uniform(.013,.040),min(length*.49,z+L)),
           (x-.007,y+.003,min(length*.49,z+L*.8))]
        shard=mesh(label+"_grain_sliver_%02d"%q,v,[(0,1,2),(0,2,3)],mats=[mat])
        shard.location=tuple(ob.location)
        shard.rotation_euler=tuple(ob.rotation_euler)
    return ob

def hide(cow):
    # Multiple naturally folded, curved hides without the artificial mountain-shaped folds.
    # Closed thickness, coherent continuous cut edge and per-piece independent silhouette.
    nx=43;ny=38
    width=1.47 if cow else 1.09
    height=1.19 if cow else .96
    thickness=.018 if cow else .009
    out_last=None
    for layer in range(2):
        verts=[];uv=[];faces=[]
        for j in range(ny):
            v=j/(ny-1)
            for i in range(nx):
                u=i/(nx-1)
                x=width*(u-.5)
                y=height*(v-.5)
                # The cut edges are irregular, but the folds respond to gravity.
                x+=(.025 if cow else .041)*sin(10*v+layer*1.4)*abs(2*u-1)**5
                y+=.045*sin(8*u+layer)*abs(2*v-1)**5
                bend=(.070 if cow else .045)*sin(u*5.5+v*.7+layer*.9)
                ridge=(.084 if cow else .060)*exp(-((u-(.38+.09*sin(v*4+layer)))/.13)**2)
                small=(.009 if cow else .021)*sin(15*u+10*v+layer)*sin(v*6)
                edgecurl=(.04 if cow else .075)*(abs(2*v-1)**8)
                z=.035+bend+ridge+small+edgecurl
                # Lift one corner slightly so the material reads as a draped, heavy hide.
                z+=(.05 if cow else .07)*exp(-((u-.88)/.17)**2)*v*v
                xx=x+(.065 if layer==1 else -.045)
                yy=y+(.065 if layer==1 else -.055)
                zz=z+(.005 if layer==1 else .095)
                verts.append((xx,yy,zz))
                uv.append((u,v))
        top=len(verts)
        for x,y,z in list(verts):
            verts.append((x,y,z-thickness))
        uv+=list(uv)
        for j in range(ny-1):
            for i in range(nx-1):
                a=j*nx+i
                faces.append((a,a+1,a+1+nx,a+nx))
                faces.append((top+a+nx,top+a+nx+1,top+a+1,top+a))
        for j in range(ny-1):
            a=j*nx;faces.append((a,a+nx,top+a+nx,top+a))
            a=j*nx+(nx-1);faces.append((a,top+a,top+a+nx,a+nx))
        for i in range(nx-1):
            a=i;faces.append((a,top+a,top+a+1,a+1))
            a=(ny-1)*nx+i;faces.append((a,a+1,top+a+1,top+a))
        ob=mesh(("bovine" if cow else "goat")+"_natural_fold_"+str(layer),
                verts,faces,uv=uv,mats=[mat])
        # Distinct poses: goat is thinner/narrower, bovine spreads wider.
        ob.rotation_euler.z=(.14 if cow else -.18)*(2*layer-1)
        out_last=ob
    return out_last

def cord(hemp):
    item=_prior_cord(hemp)
    if hemp:
        # Natural tension in the hand-laid spiral, warp the *existing true helices* coherently.
        for ob in objects:
            if "natural_hemp_three_strand_coil" not in ob.name:continue
            for vv in ob.data.vertices:
                x,y,z=vv.co
                a=math.atan2(y,x);r=math.hypot(x,y)
                vv.co.x+=.009*sin(a*4.1+r*3.3)*cos(a)
                vv.co.y+=.009*sin(a*4.1+r*3.3)*sin(a)
                vv.co.z+=.0025*sin(a*8.1)
            ob.data.update()
    else:
        # A bobbin winds on the same axis, but subtle hand-thread slubs should be visible.
        for ob in objects:
            if "hand_wound_natural_linen_thread" not in ob.name:continue
            for vv in ob.data.vertices:
                x,y,z=vv.co
                dv=.0015*sin(x*87+math.atan2(z,y)*4.7)
                vv.co.y+=dv
                vv.co.z+=dv*.4
            ob.data.update()
    return item
