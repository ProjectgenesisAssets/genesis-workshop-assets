# Genesis V005: linen is wound onto a real wooden bobbin, not a featureless ring.
# Preserve the V004 human-facing shapes for oak, ash, leather and hemp.
_v004_cord = cord
def linen_bobbin():
    wood=bpy.data.materials.new("turned_hardwood_bobbin")
    wood.use_nodes=True
    bs=wood.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(.20,.115,.058,1)
    bs.inputs["Roughness"].default_value=.84
    # A physical wooden support is useful and avoids an unreadable free-floating thin thread.
    def turned(name,rad,start,end):
        rings=9;segments=36;v=[];uv=[];faces=[]
        for j in range(rings):
            t=j/(rings-1);x=start+(end-start)*t
            r=rad*(1+.022*sin(t*pi*2.5))
            for k in range(segments):
                a=2*pi*k/segments
                v.append((x,r*cos(a),r*sin(a)))
                uv.append((t,k/segments))
        for j in range(rings-1):
            for k in range(segments):
                a=j*segments+k;b=j*segments+(k+1)%segments
                faces.append((a,b,b+segments,a+segments))
        faces.append(tuple(reversed(range(segments))))
        faces.append(tuple((rings-1)*segments+k for k in range(segments)))
        return mesh(name,v,faces,uv=uv,mats=[wood])
    turned("hardwood_spool_core",.077,-.255,.255)
    turned("hardwood_spool_left_flange",.136,-.302,-.258)
    turned("hardwood_spool_right_flange",.136,.258,.302)
    # 3-ply real geometry with 36 separate turns, each a fine thread rather than one cable.
    turns=36;steps=46;sides=6
    r=.0060;R=.089
    v=[];uv=[];faces=[]
    for winding in range(turns):
        start=len(v)
        x=-.235+.47*winding/(turns-1)
        # slight crossing and tension perturbation, coherent with hand winding.
        for j in range(steps):
            a=2*pi*j/(steps-1)
            xx=x+.002*sin(3*a+winding*.67)
            rr=R+.0022*sin(5*a+winding*.28)
            yy=rr*cos(a);zz=rr*sin(a)
            # Tube cross-section around the wrapped center-line.
            radial=Vector((0,cos(a),sin(a)))
            along=Vector((1,0,0))
            for k in range(sides):
                t=2*pi*k/sides
                p=Vector((xx,yy,zz))+r*(cos(t)*radial+sin(t)*along)
                v.append(tuple(p))
                uv.append((j/(steps-1)*1.7,k/sides))
        for j in range(steps-1):
            for k in range(sides):
                a=start+j*sides+k;b=start+j*sides+(k+1)%sides
                faces.append((a,b,b+sides,a+sides))
    mesh("hand_wound_natural_linen_thread_36_turns",v,faces,uv=uv,mats=[mat])
    # Visible free thread end, gracefully falling away from the spool.
    nr=90;ns=6;v=[];faces=[];uv=[]
    for j in range(nr):
        t=j/(nr-1)
        xx=.227+.12*t+.038*sin(t*pi)
        yy=.10+.18*t
        zz=.017+.085*cos(t*pi*.9)
        for k in range(ns):
            a=2*pi*k/ns
            v.append((xx+.004*cos(a),yy+.004*sin(a),zz+.003*sin(a)))
            uv.append((t*2,k/ns))
    for j in range(nr-1):
        for k in range(ns):
            a=j*ns+k;b=j*ns+(k+1)%ns
            faces.append((a,b,b+ns,a+ns))
    mesh("linen_loose_tail",v,faces,uv=uv,mats=[mat])
    return objects[-1]
def cord(hemp):
    if hemp: return _v004_cord(True)
    return linen_bobbin()
