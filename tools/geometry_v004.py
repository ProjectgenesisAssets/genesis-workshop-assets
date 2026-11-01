# Genesis V004 sculptural corrections. Executed from asset_v002.py, using its scene helpers.
# Geometry is newly authored; scanned albedo/roughness/normal remain from verified CC0 downloads.
def v4_bark_material():
    m=mat.copy();m.name="CC0_wood_dark_outer_and_bark_relief"
    nt=m.node_tree; n=nt.nodes; l=nt.links; bs=n.get("Principled BSDF")
    noise=n.new("ShaderNodeTexNoise");noise.inputs["Scale"].default_value=68
    noise.inputs["Detail"].default_value=5.0
    bump=n.new("ShaderNodeBump");bump.inputs["Strength"].default_value=.36
    bump.inputs["Distance"].default_value=.017
    l.new(noise.outputs["Fac"],bump.inputs["Height"])
    if bs.inputs["Normal"].is_linked:
        old=bs.inputs["Normal"].links[0].from_socket
        l.new(old,bump.inputs["Normal"])
    l.new(bump.outputs["Normal"],bs.inputs["Normal"])
    original=bs.inputs["Base Color"].links[0].from_socket if bs.inputs["Base Color"].is_linked else None
    if original:
        mul=n.new("ShaderNodeMixRGB");mul.blend_type="MULTIPLY"
        mul.inputs[0].default_value=1
        mul.inputs[2].default_value=(.30,.27,.24,1)
        l.new(original,mul.inputs[1]);l.new(mul.outputs["Color"],bs.inputs["Base Color"])
    return m
def v4_endgrain_material():
    m=mat.copy();m.name="CC0_wood_cut_end_growth_rings"
    n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get("Principled BSDF")
    wave=n.new("ShaderNodeTexWave");wave.wave_type="RINGS"
    wave.inputs["Scale"].default_value=17
    wave.inputs["Distortion"].default_value=2
    noise=n.new("ShaderNodeTexNoise");noise.inputs["Scale"].default_value=4.2
    mix=n.new("ShaderNodeMixRGB");mix.blend_type="MULTIPLY"
    mix.inputs[0].default_value=.32
    mix.inputs[2].default_value=(.48,.40,.32,1)
    if bs.inputs["Base Color"].is_linked:
        before=bs.inputs["Base Color"].links[0].from_socket
        l.new(before,mix.inputs[1])
        l.new(mix.outputs["Color"],bs.inputs["Base Color"])
        rings=n.new("ShaderNodeMixRGB");rings.blend_type="MULTIPLY"
        rings.inputs[0].default_value=.28
        l.new(mix.outputs["Color"],rings.inputs[1])
        l.new(wave.outputs["Color"],rings.inputs[2])
        l.new(rings.outputs["Color"],bs.inputs["Base Color"])
    return m
def wood_piece(label,oak,offset):
    bark=v4_bark_material()
    endgrain=v4_endgrain_material()
    rings=64;ext=19;inside=13;n=ext+inside
    length=1.18 if oak else 1.37
    rad=.265 if oak else .213
    verts=[];faces=[];uv=[];face_mats=[]
    bend=random.uniform(-.04,.04)
    for j in range(rings):
        t=j/(rings-1)
        taper=1-.17*t+.05*sin(t*6.8+offset)
        # Broken ends follow fiber grain rather than a planar saw-cut.
        for i in range(n):
            if i<ext:
                angle=-1.22+2.44*i/(ext-1)
                outer=rad*taper*(1+.065*sin(5*angle+1.1*t)+.025*sin(12*angle-5*t))
                x=outer*cos(angle)
                y=outer*sin(angle)
            else:
                frac=(i-ext+1)/(inside+1)
                y=rad*taper*(1.0-2*frac)*.94
                crack=.038*sin(t*11+frac*5.3)+.019*sin(t*21-frac*13)
                # Long tears and raised fibrous contours.
                x=.018+crack+(.024 if oak else .014)*sin(frac*12+t*4.8)
            longitudinal=.012*sin(t*18+0.7*i)+.004*sin(t*38+i*2.1)
            broken=(1-t)**7*.038*(.5+.5*sin(i*7.73+offset)**2)
            broken-=t**9*.075*(.4+.6*sin(i*3.71)**2)
            z=length*(t-.5)+longitudinal+broken
            verts.append((x+bend*sin(t*5),y,z))
            uv.append((t*2.8,(i/(n-1))*.99))
    for j in range(rings-1):
        for i in range(n):
            a=j*n+i;b=j*n+(i+1)%n
            faces.append((a,b,b+n,a+n))
            face_mats.append(1 if i<ext-1 else 0)
    faces.append(tuple(reversed(range(n))));face_mats.append(2)
    faces.append(tuple((rings-1)*n+i for i in range(n)));face_mats.append(2)
    ob=mesh(label,verts,faces,uv=uv,mats=[mat,bark,endgrain],side_indices=face_mats)
    # Set cut-end planar UVs so ring pattern is radial, not projected from sidegrain.
    lay=ob.data.uv_layers.active
    for face in list(ob.data.polygons)[-2:]:
        for li in face.loop_indices:
            co=ob.data.vertices[ob.data.loops[li].vertex_index].co
            lay.data[li].uv=(.5+co.x/(2*rad),.5+co.y/(2*rad))
    # Pieces nest in a firewood stack with two distinct orientations.
    ob.rotation_euler=(.05*offset,1.41+.085*offset,.13*offset)
    ob.location=(.055*offset,.19*offset,.038*offset)
    # Thin slivers at fracture margins; no costly full fiber cylinders.
    for j in range(17 if oak else 13):
        u=random.uniform(.1,.87);z=length*(u-.5)
        y=random.uniform(-rad*.77,rad*.77)
        x=.017+.024*sin(u*11+(y/rad)*4)
        span=random.uniform(.11,.32) if oak else random.uniform(.17,.39)
        v=[(x,y,z),(x+.008,y+.006,z+.018),
           (x+random.uniform(.002,.032),y+.008,z+span),
           (x-.006,y-.004,z+span*.82)]
        spl=mesh(label+"_split_fiber_%02d"%j,v,[(0,1,2),(0,2,3)],mats=[mat])
        spl.location=tuple(ob.location);spl.rotation_euler=tuple(ob.rotation_euler)
    return ob
def hide(cow):
    # Folded cured hides, a layered irregular pelt rather than a flat radial star.
    pieces=2 if cow else 2
    width=1.28 if cow else 1.18
    height=.91 if cow else .88
    rim_mat=mat.copy()
    rim_mat.name="natural_hide_cut_edge"
    for idx in range(pieces):
        nphi=64;nr=24;verts=[];faces=[];uv=[]
        thickness=.024 if cow else .013
        for layer in range(2):
            for j in range(nr):
                r=.012+.988*j/(nr-1)
                for i in range(nphi):
                    a=2*pi*i/nphi
                    # Lobe pattern and asymmetry of a trimmed natural pelt
                    outline=1+.07*sin(3*a+.3*idx)+.045*sin(7*a+1.3)+.024*cos(11*a+idx)
                    x=width*.51*r*outline*cos(a)
                    y=height*.53*r*outline*sin(a)
                    x+=.10*r*r*sin(2*a+idx)
                    # Fold runs diagonally, supported by a soft roll along one edge.
                    fold_axis=x*.91+y*.43
                    fold=.10*math.exp(-((fold_axis-.02)/(.15 if cow else .11))**2)
                    waves=(.023 if cow else .032)*sin(9*x+5*y+idx)*sin(3.4*y)
                    curl=.075*(r**9)*sin(a*2.4+idx*.9)**2
                    z=.09+fold+waves+curl+.04*sin(2.0*y+idx)
                    if idx: z-=.035
                    if layer: z-=thickness
                    verts.append((x+.14*idx,y-.11*idx,z))
                    uv.append((.5+x/(width*1.6),.5+y/(height*1.6)))
        top=nr*nphi
        for layer in range(2):
            base=layer*top
            for j in range(nr-1):
                for i in range(nphi):
                    k=(i+1)%nphi
                    a=base+j*nphi+i;b=base+j*nphi+k
                    c=base+(j+1)*nphi+k;d=base+(j+1)*nphi+i
                    faces.append((a,b,c,d) if layer==0 else (d,c,b,a))
        for i in range(nphi):
            j=(i+1)%nphi;a=(nr-1)*nphi+i;b=(nr-1)*nphi+j
            faces.append((a,b,top+b,top+a))
        ob=mesh(("bovine" if cow else "goat")+"_folded_hide_"+str(idx),verts,faces,uv,mats=[mat,rim_mat])
        ob.rotation_euler=(.06*idx,.10*idx,-.07*idx)
    return ob
def cord(hemp):
    # Compact 3-ply rope with touching strands; natural coil/linen skein silhouette.
    loops=2.7 if hemp else 4.35
    steps=460 if hemp else 620
    sides=7 if hemp else 6
    radius=.0142 if hemp else .0064
    core=.0088 if hemp else .0042
    twists=23 if hemp else 32
    vertices=[];faces=[];uv=[]
    def center(t):
        a=2*pi*loops*t
        if hemp:
            rr=.115+.38*t
            x=rr*cos(a)+.013*sin(7*a)
            y=.85*rr*sin(a)+.009*cos(11*a)
            z=.032+.009*sin(2*a)
            if t>.92:
                d=(t-.92)/.08;x+=.19*d;y-=.13*d
        else:
            # Wound skein of fine linen thread with small variation in each wrap.
            rr=.39+.012*sin(8*t)
            x=rr*cos(a)+.004*sin(29*t)
            y=.56*rr*sin(a)+.012*sin(11*t)
            z=.034+.014*t+.007*sin(a*3)
            if t>.97:
                d=(t-.97)/.03;x+=.10*d;y-=.07*d
        return Vector((x,y,z))
    for part in range(3):
        base=len(vertices)
        for j in range(steps):
            t=j/(steps-1)
            pos=center(t)
            tangent=(center(min(1,t+.0002))-center(max(0,t-.0002))).normalized()
            side=Vector((-tangent.y,tangent.x,0))
            up=tangent.cross(side).normalized()
            helix=2*pi*(twists*t+part/3)
            pos+=core*(cos(helix)*side+sin(helix)*up)
            for i in range(sides):
                ang=2*pi*i/sides
                rad=radius*(1+.025*sin(j*.33+i)+.048*sin(27*t+part))
                q=pos+rad*(cos(ang)*side+sin(ang)*up)
                vertices.append(tuple(q))
                uv.append((t*16,i/sides))
        for j in range(steps-1):
            for i in range(sides):
                a=base+j*sides+i;b=base+j*sides+(i+1)%sides
                c=base+(j+1)*sides+(i+1)%sides;d=base+(j+1)*sides+i
                faces.append((a,b,c,d))
    result=mesh("natural_hemp_three_strand_coil" if hemp else "fine_flax_fiber_skein",vertices,faces,uv)
    # Short flyaway fibers follow the actual coil surface, without long geometric spikes.
    for j in range(24 if hemp else 12):
        t=random.uniform(.04,.99)
        pos=center(t)
        a=random.uniform(0,2*pi)
        length=random.uniform(.017,.045) if hemp else random.uniform(.008,.021)
        x,y,z=pos
        x+=core*cos(a);y+=core*sin(a)
        vv=[(x,y,z),(x+length*cos(a),y+length*sin(a),z+length*.16),
            (x+length*cos(a+.13),y+length*sin(a+.13),z+length*.17)]
        mesh("frayed_natural_fibril_%02d"%j,vv,[(0,1,2)])
    return result
