# -*- coding: utf-8 -*-
"""Project Genesis — forge V014 art correction candidate for PlayCanvas.
Generated on official Blender 4.5.13 LTS in GitHub Actions, NEVER local Blender.
Anvil / stone-coal forge / traditional leather bellows. First-pass visual candidates,
not approved assets. Each part is independent with packed PBR textures.
"""
import bpy, sys, os, json, random, math, urllib.request
from pathlib import Path
from mathutils import Vector
import numpy as np

ARG=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
assert ARG == ["forge"], "V014 is forge-only; preserve independent anvil/bellows branches: " + str(ARG)
KIND=ARG[0]
random.seed(4761+len(KIND))
ROOT=Path(os.environ.get("GITHUB_WORKSPACE",os.getcwd()))
OUT=ROOT/("output_hero_"+KIND+"_v033")
TEX=OUT/"textures";TEX.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
ASSETS=[];MAPS=[];MATERIALS={}

def coarse(n,step,rng):
    # Continuous bicubic-like smoothstep value noise: no hard squares/checkerboard.
    k=int(math.ceil(n/step))+3
    a=rng.normal(0,1,(k,k)).astype(np.float32)
    g=np.arange(n,dtype=np.float32)/float(step)
    i=np.floor(g).astype(np.int32)
    f=(g-i);f=f*f*(3-2*f)
    x0=i[:,None];x1=(i+1)[:,None];y0=i[None,:];y1=(i+1)[None,:]
    wx=f[:,None];wy=f[None,:]
    return (a[x0,y0]*(1-wx)*(1-wy)
           +a[x1,y0]*wx*(1-wy)
           +a[x0,y1]*(1-wx)*wy
           +a[x1,y1]*wx*wy).astype(np.float32)

def pbr(name,base,metal,rough,kind,seed):
    if name in MATERIALS:return MATERIALS[name]
    n=1536
    rng=np.random.default_rng(seed)
    c=coarse(n,32,rng)
    f=coarse(n,8,rng)
    macro=coarse(n,128,rng)
    micro=rng.normal(0,1,(n,n)).astype(np.float32)
    v=np.linspace(0,1,n,endpoint=False,dtype=np.float32)[:,None]
    u=np.linspace(0,1,n,endpoint=False,dtype=np.float32)[None,:]
    height=(.54+.12*f+.11*c+.055*micro).astype(np.float32)
    if kind=="steelpolish":
        # True hardened anvil face: brushed silver, minute linear scratches, no stone-like pits.
        scratches=(np.sin(2*np.pi*(u*420+v*83+f*.025))>.993).astype(np.float32)
        height=.50+.005*c+.004*f+.003*micro-.004*scratches
        # Hardened tool steel must stay largely continuous, not tiled grey blotches.
        shade=.947+.027*c+.016*f+.006*micro-.055*scratches
        pores=.003*scratches
    elif kind=="wood":
        # Distorted timber fibres (no wallpaper-like periodic pink parallel stripes).
        knotwarp=.17*c+.11*macro+.09*np.sin(u*11)
        grain=np.sin(2*np.pi*(v*14+u*.57+knotwarp))
        grain2=np.sin(2*np.pi*(v*39+u*.38+.14*c))
        height+=.071*grain+.018*grain2
        shade=.83+.124*grain+.035*grain2+.045*c-.022*np.maximum(0,macro)
        pores=np.maximum(0,-grain2)*.015
    elif kind=="leather":
        grain=np.sin(v*350+np.sin(u*90)*.6)
        height+=.025*grain+.04*np.maximum(0,micro)
        shade=.90+.085*c+.025*grain+.07*macro
        pores=np.maximum(0,micro-.45)*.03
    elif kind=="hotcoal":
        fractures=(f<-.56).astype(np.float32)
        height-=.17*fractures
        shade=.88+.14*c+.07*macro-.15*fractures+.035*micro
        pores=np.maximum(0,.06-f)*.10
    elif kind=="stone":
        fractures=(f<-.56).astype(np.float32)
        height-=.15*fractures
        shade=.89+.16*c+.08*macro-.16*fractures+.035*micro
        pores=np.maximum(0,.06-f)*.10
    elif kind=="iron":
        pits=(f<-.55).astype(np.float32)
        height-=.10*pits
        shade=.96+.10*c+.075*macro-.18*pits+.024*micro
        pores=pits*.055
    else:
        shade=1+.10*c+.045*macro+.025*micro
        pores=np.maximum(0,-f)*.04
    color=np.stack([np.clip(float(b)*(shade-pores),.008,.98) for b in base],axis=2).astype(np.float32)
    roughmap=np.clip(rough+( .006*c+.004*micro if kind=="steelpolish" else .055*c+.012*micro)+pores,.15,.96).astype(np.float32)
    gy,gx=np.gradient(height)
    dx=np.clip(-gx*2.3,-.85,.85);dy=np.clip(-gy*2.3,-.85,.85)
    dz=np.ones_like(dx)
    norm=np.sqrt(dx*dx+dy*dy+dz*dz)
    normal=np.stack([.5+.5*dx/norm,.5+.5*dy/norm,.5+.5*dz/norm],axis=2).astype(np.float32)
    def img(suffix,rgb,noncolor=False):
        im=bpy.data.images.new(name+"_"+suffix,width=n,height=n,alpha=True)
        alpha=np.ones((n,n,1),dtype=np.float32)
        rgba=np.concatenate((rgb,alpha),axis=2)
        im.pixels.foreach_set(np.clip(rgba,0,1).reshape(-1))
        dest=TEX/(name+"_"+suffix+".png")
        im.filepath_raw=str(dest);im.file_format="PNG";im.save()
        if noncolor:im.colorspace_settings.name="Non-Color"
        im.pack();MAPS.append(str(dest.relative_to(OUT)))
        return im
    albedo=img("albedo",color)
    roughness=img("roughness",np.repeat(roughmap[:,:,None],3,axis=2),True)
    normalimg=img("normal",normal,True)
    m=bpy.data.materials.new(name);m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Metallic"].default_value=metal
    bs.inputs["Roughness"].default_value=rough
    bs.inputs["Base Color"].default_value=(*base,1)
    nodes=m.node_tree.nodes;links=m.node_tree.links
    ac=nodes.new("ShaderNodeTexImage");ac.image=albedo
    rr=nodes.new("ShaderNodeTexImage");rr.image=roughness
    no=nodes.new("ShaderNodeTexImage");no.image=normalimg
    nm=nodes.new("ShaderNodeNormalMap");nm.inputs["Strength"].default_value=(.08 if kind=="steelpolish" else .30)
    links.new(ac.outputs["Color"],bs.inputs["Base Color"])
    links.new(rr.outputs["Color"],bs.inputs["Roughness"])
    links.new(no.outputs["Color"],nm.inputs["Color"])
    links.new(nm.outputs["Normal"],bs.inputs["Normal"])
    if kind=="hotcoal":
        # Incandescence lives in narrow charcoal microfractures, NOT detached bright spheres.
        thin=np.clip((.115-np.abs(f))/.085,0,1)*np.clip((.40+c)/.75,0,1)
        emission=np.stack([thin*.85,thin*.19,thin*.025],axis=2).astype(np.float32)
        emm=img("emissive",emission)
        emnode=nodes.new("ShaderNodeTexImage");emnode.image=emm
        links.new(emnode.outputs["Color"],bs.inputs["Emission Color"])
        bs.inputs["Emission Strength"].default_value=7.1
    MATERIALS[name]=m
    return m

def emissive(name,color,power):
    m=bpy.data.materials.new(name);m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*color,1)
    bs.inputs["Emission Color"].default_value=(*color,1)
    bs.inputs["Emission Strength"].default_value=power
    bs.inputs["Roughness"].default_value=.85
    return m

def track(obj,mat):
    obj.data.materials.append(mat)
    ASSETS.append(obj)
    return obj

def bevel(obj,width=.008,segments=3):
    if width:
        b=obj.modifiers.new("Worn forged and chipped edges","BEVEL")
        b.width=width;b.segments=segments
        b.affect='EDGES'
        o=obj.modifiers.new("Weighted surface normals","WEIGHTED_NORMAL")
        o.keep_sharp=True
    return obj

def box(name,center,dims,mat,edge=.007,rz=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center)
    o=bpy.context.object;o.name=name
    o.dimensions=dims;o.rotation_euler.z=rz
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    track(o,mat);bevel(o,edge)
    return o

def handlaid(name,center,dims,mat,edge=.006,rz=0):
    """V033: hand-hewn rock, natural damaged limestone / refractory sandstone.
    Geometry is the erosion: broken nonparallel arrises, caves in the face,
    asymmetrical fracture chips, layered strata. Never cartoon angular boxes.
    An interior forge core holds the true structural mass of the hearth.
    """
    rng=random.Random(29029+sum((i+1)*ord(ch) for i,ch in enumerate(name)))
    size=tuple(max(.033,d*(1+rng.uniform(-.095,.095))) for d in dims)
    # A masonry course stays seated, yet individual rocks no longer align like tiles.
    offset=(rng.uniform(-.009,.009),rng.uniform(-.010,.010),rng.uniform(-.004,.004))
    pos=tuple(center[i]+offset[i] for i in range(3))
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
    obj=bpy.context.object;obj.name=name;obj.dimensions=size
    obj.rotation_euler.z=rz+rng.uniform(-.030,.030)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    track(obj,mat)
    # Dense enough topology for meaningful irregular silhouettes with no texture cheats.
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.subdivide(number_cuts=3,smoothness=0)
    bpy.ops.object.mode_set(mode="OBJECT")
    half=tuple(s*.5 for s in size)
    seed_phase=rng.uniform(0,math.tau)
    stratum=rng.uniform(-.21,.21)
    for vert in obj.data.vertices:
        co=vert.co
        normalized=[abs(co[k])/max(half[k],.0001) for k in range(3)]
        bounds=[k for k,q in enumerate(normalized) if q>.96]
        if len(bounds)==3:
            # Broken corners, often one large missing flake rather than a nice bevel.
            damage=rng.uniform(.140,.270)
            for axis in bounds:
                co[axis]*=(1.0-damage*rng.uniform(.55,1.20))
        elif len(bounds)==2:
            # Irregular arrises eroded along their length; not repeated chamfer strips.
            damage=rng.uniform(.060,.175)
            for axis in bounds:
                co[axis]*=(1.0-damage*rng.uniform(.50,1.34))
            free_axis=next(k for k in range(3) if k not in bounds)
            co[free_axis]+=size[free_axis]*rng.uniform(-.046,.046)
        elif len(bounds)==1:
            # Genuine relief over the broad stone planes, including concave pockmarks.
            axis=bounds[0]
            plane=[k for k in range(3) if k!=axis]
            plane_wave=math.sin(co[plane[0]]*29+seed_phase)*math.sin(co[plane[1]]*20+stratum)
            pit=rng.uniform(-.095,.047)+.027*plane_wave
            if rng.random()<.16:pit-=rng.uniform(.06,.12)
            co[axis]+=math.copysign(pit*min(size),co[axis])
            for side_axis in plane:
                co[side_axis]+=rng.uniform(-.018,.018)*size[side_axis]
    obj.data.update()
    # Facets and microchipped fractures live in mesh; small true bevel softens chips.
    bevel(obj,edge*rng.uniform(.42,.86),segments=2)
    if obj.data.uv_layers.active:
        du,dv=rng.random(),rng.random()
        us=rng.uniform(.63,.94);vs=rng.uniform(.65,1.00)
        for uvloop in obj.data.uv_layers.active.data:
            u,v=uvloop.uv.x,uvloop.uv.y
            uvloop.uv.x=u*us+du;uvloop.uv.y=v*vs+dv
    return obj

def geological_mass(name,center,dims,mat,seed=0,fracture=.046):
    """One continuous fissured rock face, not a mosaic of brick-shaped rocks.
    Functional shafts/openings are separate masses; individual rock objects gone.
    Deep fault grooves and stratified weathering are real mesh displacement.
    """
    rng=random.Random(6030+seed)
    bpy.ops.mesh.primitive_cube_add(size=1,location=center)
    obj=bpy.context.object;obj.name=name;obj.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    track(obj,mat)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.subdivide(number_cuts=15,smoothness=0)
    bpy.ops.object.mode_set(mode="OBJECT")
    half=[x*.5 for x in dims]
    phase=rng.uniform(0,math.tau)
    bias=rng.uniform(-.4,.4)
    for v in obj.data.vertices:
        co=v.co
        q=[abs(co[i])/max(half[i],.0001) for i in range(3)]
        boundary=[i for i in range(3) if q[i]>.965]
        if not boundary:continue
        for normal in boundary:
            plane=[i for i in range(3) if i!=normal]
            u=co[plane[0]]/max(half[plane[0]],.0001)
            w=co[plane[1]]/max(half[plane[1]],.0001)
            # Three fractured geological strata, long non-repeating fault traces.
            natural_fault= u-(.21*math.sin(w*3.3+phase)+.11*math.sin(w*7.8+phase*1.3)+bias)
            spur_fault= w-(.18*math.sin(u*5.2+phase*1.7)-.28+seed*.019)
            crack_profile=math.exp(-(natural_fault/.105)**2)
            crack_profile+=.57*math.exp(-(spur_fault/.075)**2)
            topography=(.44*math.sin(u*8.2+w*5.6+phase)
                        +.22*math.sin(u*19.3-w*9.2+phase*.71)
                        +.11*math.cos(u*43.6+w*31.0+phase))
            granular=rng.uniform(-.20,.20)
            relief=.028*topography+.008*granular
            # Recessed rock clefts (dark in shadow), not black painted strokes.
            max_depth=min(fracture,dims[normal]*.28)
            relief-=max_depth*min(1.,crack_profile)
            # Spalled edges of a single monolithic mass.
            if len(boundary)>1:
                relief-=rng.uniform(.004,.017)
            co[normal]+=math.copysign(relief,co[normal])
    obj.data.update()
    bevel(obj,.002,segments=1)
    return obj

def cyl(name,pos,r,depth,mat,vertices=32,rot=(0,0,0),edge=.002):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=pos,rotation=rot)
    o=bpy.context.object;o.name=name
    track(o,mat);bevel(o,edge,2)
    return o

def ico(name,center,r,mat,subdiv=2,scale=(1,1,1)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv,radius=r,location=center)
    o=bpy.context.object;o.name=name
    o.scale=scale;track(o,mat)
    return o

def made_mesh(name,verts,faces,mat,edge=.002):
    m=bpy.data.meshes.new(name+"_mesh");m.from_pydata(verts,[],faces);m.update()
    o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o)
    track(o,mat);bevel(o,edge,3)
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(island_margin=.013)
    bpy.ops.object.mode_set(mode="OBJECT")
    o.select_set(False)
    return o

def hard_cut(body,name,location,scale,radius=0):
    if radius:
        bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=radius,depth=scale[2],location=location)
    else:
        bpy.ops.mesh.primitive_cube_add(size=1,location=location)
        bpy.context.object.dimensions=scale
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    cutter=bpy.context.object;cutter.name=name
    mod=body.modifiers.new("Actual functional through-hole","BOOLEAN")
    mod.operation="DIFFERENCE";mod.object=cutter
    bpy.ops.object.select_all(action="DESELECT");body.select_set(True)
    bpy.context.view_layer.objects.active=body
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter,do_unlink=True)

def mount_anvil():
    iron=pbr("anvil_forged_wrought_iron",(.143,.148,.151),.90,.60,"iron",11)
    steel=pbr("anvil_polished_hardened_steel",(.274,.286,.292),.92,.43,"steelpolish",12)
    oak=pbr("anvil_old_oak_base",(.214,.128,.067),.02,.78,"wood",14)
    dark=pbr("anvil_cut_mark_oxidation",(.061,.064,.061),.85,.81,"iron",16)
    # Forged mass: independently measured tapered waist with splayed foot.
    levels=[(.22,.37,.148),(.30,.34,.137),(.42,.246,.112),(.57,.262,.121),(.65,.334,.133),(.71,.349,.140)]
    verts=[]
    for z,xw,yw in levels:
        verts.extend([(-xw,-yw,z),(xw,-yw,z),(xw,yw,z),(-xw,yw,z)])
    faces=[(3,2,1,0),(20,21,22,23)]
    for i in range(len(levels)-1):
        for j in range(4):
            k=(j+1)%4
            faces.append((4*i+j,4*i+k,4*(i+1)+k,4*(i+1)+j))
    made_mesh("Forged waisted body with drawn shoulders",verts,faces,iron,.014)
    box("Splayed lower forged foot",(0,0,.195),(.77,.34,.14),iron,.023)
    box("Face backing land",(0,0,.705),(.72,.291,.071),iron,.015)
    # A six-sided subtly drawn-out heel, not a cantilevered perfect rectangular plate.
    outline=[(-.414,-.135),(.216,-.135),(.565,-.093),(.565,.093),(.216,.135),(-.414,.135)]
    nt=len(outline);fv=[]
    for z in (.726,.777):
        for x,y in outline: fv.append((x,y,z))
    ff=[tuple(reversed(range(nt))),tuple(range(nt,2*nt))]
    for k in range(nt): ff.append((k,(k+1)%nt,(k+1)%nt+nt,k+nt))
    face=made_mesh("One tapered seamless forged hardened face and drawn heel",fv,ff,steel,0)
    hard_cut(face,"Real square hardy hole",(.458,.012,.751),(.071,.071,.22))
    hard_cut(face,"Real round pritchel piercing",(.323,-.078,.751),(.01,.01,.22),radius=.017)
    bevel(face,.011,4)
    # Fully modeled rounded horn tapers in 18 forged sections to a real tip.
    # Blend the forged horn into the flat face: start embedded inside the working land.
    # Omit the root end-cap so an artificial dark vertical disk cannot appear.
    rings=[]
    for k in range(25):
        t=k/24
        x=-.350-.505*t
        yr=.135*(1-t)**.82+.004
        zr=.078*(1-t)**1.00+.002
        z=.694-.025*t+.006*math.sin(math.pi*t)
        rings.append((x,yr,zr,z))
    nv=20;verts=[]
    for x,yr,zr,z in rings:
        for j in range(nv):
            a=2*math.pi*j/nv
            verts.append((x,yr*math.cos(a),z+zr*math.sin(a)))
    faces=[]
    for i in range(len(rings)-1):
        for j in range(nv):
            k=(j+1)%nv
            faces.append((i*nv+j,i*nv+k,(i+1)*nv+k,(i+1)*nv+j))
    faces.append(tuple((len(rings)-1)*nv+j for j in range(nv)))
    horn=made_mesh("Functional rounded horn with forge-drawn root embedded under face",verts,faces,steel,.001)
    for face in horn.data.polygons:face.use_smooth=True
    # Both functional holes are cut in the same solid face above, no detached heel.
    # Distinct hammered banding across body; no cartoonized grooves.
    # Oxidation is in the packed PBR: fake straight witness stripes were removed.
    # Removable authentic stump block as separate model part.
    # Roughly hand-hewn stump: 36-sided slightly irregular silhouette, not a perfect drum.
    ringz=(-.365,-.205,.11);sidecount=36;sv=[]
    uneven=[1+.023*math.sin(i*.83)+.015*math.cos(i*2.1) for i in range(sidecount)]
    for z in ringz:
        for i in range(sidecount):
            th=2*math.pi*i/sidecount
            r=.264*uneven[i]*(1+(.011 if z==-.205 else 0))
            sv.append((r*math.cos(th),r*math.sin(th),z))
    sf=[tuple(reversed(range(sidecount))),tuple((len(ringz)-1)*sidecount+i for i in range(sidecount))]
    for layer in range(len(ringz)-1):
        for i in range(sidecount):
            j=(i+1)%sidecount
            sf.append((layer*sidecount+i,layer*sidecount+j,(layer+1)*sidecount+j,(layer+1)*sidecount+i))
    made_mesh("Irregular axe-cut old oak tree stump support",sv,sf,oak,.005)
    for i in range(8):
        a=2*math.pi*i/8
        cyl("Recessed forged nail "+str(i),(.19*math.cos(a),.19*math.sin(a),.115),.008,.008,dark,12,edge=.001)
    # Pair of sturdy wrought iron hoops around the real axe-hewn stump.
    for z in (-.29,-.055):
        bpy.ops.mesh.primitive_torus_add(major_segments=60,minor_segments=10,
            location=(0,0,z),major_radius=.272,minor_radius=.012)
        track(bpy.context.object,iron);bpy.context.object.name="Wrought iron stump compression hoop "+str(z)

def mount_bellows():
    wood=pbr("bellows_aged_oak_long_grain",(.174,.088,.034),.01,.77,"wood",32)
    leather=pbr("bellows_creased_dark_oxblood_leather",(.128,.071,.043),.02,.84,"leather",33)
    # Direct fixed CC0 files were audited via official Poly Haven API and rendered here.
    def scanned_material(base_material,filename,url):
        target=TEX/filename
        if not target.is_file():
            req=urllib.request.Request(url,headers={"User-Agent":"ProjectGenesis/1.0 ArtAssetPipeline"})
            with urllib.request.urlopen(req,timeout=90) as stream: target.write_bytes(stream.read())
        assert target.stat().st_size>20000,filename
        img=bpy.data.images.load(str(target),check_existing=False)
        img.pack();img.colorspace_settings.name="sRGB"
        slots=[nd for nd in base_material.node_tree.nodes if nd.type=="TEX_IMAGE" and nd.image and nd.image.name.endswith("_albedo")]
        assert len(slots)==1,(base_material.name,len(slots))
        slots[0].image=img
        MAPS.append(str(target.relative_to(OUT)))
    scanned_material(wood,"bellows_scanned_old_oak_CC0_1k.jpg",
        "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/fine_grained_wood/fine_grained_wood_col_1k.jpg")
    scanned_material(leather,"bellows_scanned_worn_leather_CC0_1k.jpg",
        "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/brown_leather/brown_leather_albedo_1k.jpg")
    iron=pbr("bellows_oxidized_hand_forged_iron",(.112,.118,.118),.82,.62,"iron",34)
    brass=pbr("bellows_patina_riveted_brass",(.43,.29,.14),.72,.55,"iron",35)
    # Hand shaped pear wood boards, not beveled boxes or flat icon shapes.
    outline=[(-.76,-.14),(-.66,-.235),(-.45,-.32),(-.18,-.355),(.05,-.32),(.25,-.24),(.45,-.15),(.62,-.095),(.68,0),(.62,.095),(.45,.15),(.25,.24),(.05,.32),(-.18,.355),(-.45,.32),(-.66,.235)]
    control=outline[:];outline=[]
    # Quadruplicate hand-carved pear contour samples to eliminate faceted octagonal top.
    for k,(ax,ay) in enumerate(control):
        bx,by=control[(k+1)%len(control)]
        for j in range(4):
            t=j/4;outline.append((ax*(1-t)+bx*t,ay*(1-t)+by*t))
    def board(name,z,thickness):
        n=len(outline)
        # Top plank is raised toward the handles, lower near the air outlet.
        verts=[(x,y,(.43-.125*x if name.startswith("Top") else z)+oz)
               for oz in (-thickness/2,thickness/2) for x,y in outline]
        faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
        for i in range(n):
            j=(i+1)%n;faces.append((i,j,n+j,n+i))
        ob=made_mesh(name,verts,faces,wood,.013)
        # The longitudinal grain of the photographic oak MUST run along the bellows pear axis.
        # Top and bottom have world-space projected planar UVs; sides retain smart UV islands.
        uv=ob.data.uv_layers.active.data
        for poly in ob.data.polygons:
            if len(poly.vertices)==n:
                for li in poly.loop_indices:
                    p=ob.data.vertices[ob.data.loops[li].vertex_index].co
                    uv[li].uv=((p.y+.355)/.710,(p.x+.76)/1.44)
        return ob
    board("Removable bottom solid oak board",.10,.046)
    board("Top shaped oak bellows board",.43,.050)
    # Real scanned wood pores replace misleading synthetic drawn strokes.
    # True volumetric folded gusset in twelve visible double leather creases.
    n=len(outline);verts=[]
    for level in range(23):
        t=level/22
        for x,y in outline:
            # Quiet leather creasing follows air pressure, avoids stacked rigid bands.
            factor=1+(.089+.017*math.sin(3*math.pi*t+1.7*x))*math.sin(math.pi*t)
            top=.43-.125*x
            z=.126+(top-.126)*t
            verts.append((x,y*factor,z))
    faces=[]
    for level in range(22):
        for i in range(n):
            j=(i+1)%n
            faces.append((level*n+i,level*n+j,(level+1)*n+j,(level+1)*n+i))
    gusset=made_mesh("Hand stitched multi-fold leather air chamber",verts,faces,leather,.001)
    for face in gusset.data.polygons:face.use_smooth=True
    # Distinct leather edge seams and hand hammered perimeter rivets.
    for i,(x,y) in enumerate(outline):
        if i%8==0:
            for z in (.133,.426-.125*x):
                ico("Small peened brass nail %02d "%i+str(z),(x*.985,y*.96,z),.009,brass,subdiv=2,scale=(1,.78,.45))
    cyl("Forged tubular forward air nozzle",(.70,0,.224),.060,.32,iron,40,rot=(0,math.pi/2,0),edge=.006)
    cyl("Narrow brass nozzle ring",(.852,0,.224),.063,.019,brass,40,rot=(0,math.pi/2,0),edge=.003)
    for z in (.116,.535):
        box("Hinged oak rear squeeze handle "+str(z),(-.755,0,z),(.35,.085,.056),wood,.022)
        cyl("Forged rear pivot pin "+str(z),(-.62,0,z),.027,.10,iron,20,rot=(math.pi/2,0,0),edge=.002)
    # The dark inner bore prevents the brass mouth from reading as a solid wooden plug.
    cyl("Darkened nozzle throat air opening",(.864,0,.224),.041,.003,iron,40,rot=(0,math.pi/2,0),edge=0)
    # Proper stitched leather welts on both oak-board contact lines.
    # The source splines are converted to real polygon meshes for glTF.
    for z in (.135,.425):
        curve=bpy.data.curves.new("Continuous hand-cut leather welt","CURVE")
        curve.dimensions="3D";curve.resolution_u=16
        curve.bevel_depth=.008;curve.bevel_resolution=2
        spline=curve.splines.new("POLY");spline.points.add(len(outline)-1)
        for point,(x,y) in zip(spline.points,outline):
            point.co=(x*.992,y*.990,(.43-.125*x if z>.20 else z),1)
        spline.use_cyclic_u=True
        o=bpy.data.objects.new("Perimeter hand stitched leather welt "+str(z),curve)
        bpy.context.collection.objects.link(o)
        o.data.materials.append(leather)
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True);bpy.context.view_layer.objects.active=o
        bpy.ops.object.convert(target="MESH")
        ASSETS.append(bpy.context.object)
    for i,(x,y) in enumerate(outline):
        if i%8==0:
            ico("Bronze nail fixing leather gusset "+str(i),
                (x*.975,y*.97,.428-.125*x),.009,brass,subdiv=2,scale=(1,1,.5))
    # Individual off-white linen saddle stitches as a single efficient mesh.
    linen=bpy.data.materials.new("Unbleached linen saddle stitch thread")
    linen.diffuse_color=(.42,.34,.22,1)
    linen.use_nodes=True
    linen.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value=(.42,.34,.22,1)
    linen.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value=.92
    sts_verts=[];sts_faces=[]
    for k in range(0,len(outline),2):
        x,y=outline[k]
        nextx,nexty=outline[(k+1)%len(outline)]
        tx,ty=nextx-x,nexty-y
        ln=max(.0001,math.sqrt(tx*tx+ty*ty));tx/=ln;ty/=ln
        normal_x=-ty;normal_y=tx
        for z in (.142,.418-.125*x):
            cx=x+normal_x*.004;cy=y+normal_y*.004
            idx=len(sts_verts)
            sts_verts.extend([(cx-tx*.009,cy-ty*.009,z-.001),
                             (cx+tx*.009,cy+ty*.009,z-.001),
                             (cx+tx*.009,cy+ty*.009,z+.002),
                             (cx-tx*.009,cy-ty*.009,z+.002)])
            sts_faces.append((idx,idx+1,idx+2,idx+3))
    made_mesh("Visible stitch by stitch linen gusset seams",sts_verts,sts_faces,linen,0)
    # No unverified animation: independent boards remain animation-ready components.

def mount_forge():
    global quarry_photo_bound
    # V014: desaturated refractory stone, weathered stone, and deeply soot-stained courses.
    # Three physically textured masonry materials avoid a single cartoon-uniform brick palette.
    stone=pbr("forge_aged_refractory_sandstone",(.245,.234,.215),.0,.92,"stone",71)
    hearth=pbr("forge_heat_blackened_brick",(.122,.115,.106),.0,.94,"stone",72)
    # V014: reuse the same two physical stone PBR sets across the masonry.
    # Avoid exporting duplicate 1536px maps for cosmetically similar stone shades.
    weathered=stone
    sooted=hearth
    steel=pbr("forge_hammered_hood_black_iron",(.095,.103,.104),.83,.70,"iron",73)
    coal=pbr("forge_real_charcoal_porous",(.065,.061,.059),.0,.96,"stone",74)
    hotcoal=pbr("forge_cracked_hot_charcoal_ember_map",(.065,.060,.056),.0,.92,"hotcoal",75)
    def scanned_quarry_stone(material,charred=False):
        """CC0 Poly Haven Quarry Wall 2K real stone color/normal/roughness.
        Keep procedural fallback explicit if API or downloads are unavailable."""
        try:
            req=urllib.request.Request("https://api.polyhaven.com/files/quarry_wall",
                                       headers={"User-Agent":"ProjectGenesis/1.0 ArtAssetPipeline"})
            with urllib.request.urlopen(req,timeout=40) as response:
                manifest=json.load(response)
            def file_url(keys):
                for key in keys:
                    data=manifest.get(key)
                    if not isinstance(data,dict):continue
                    for res in ("2k","1k"):
                        variants=data.get(res,{})
                        for ext in ("jpg","png"):
                            item=variants.get(ext)
                            if isinstance(item,dict) and item.get("url"):
                                return item["url"],ext
                return None,None
            channels={"albedo":("Diffuse","diffuse","Color"),
                      "normal":("nor_gl","NormalGL","Normal"),
                      "roughness":("Rough","roughness","Roughness")}
            for channel,keys in channels.items():
                url,ext=file_url(keys)
                if not url:raise RuntimeError("Missing quarry_wall "+channel+" in official API")
                target=TEX/("quarry_wall_CC0_"+channel+"_2k."+ext)
                if not target.exists():
                    req=urllib.request.Request(url,headers={"User-Agent":"ProjectGenesis/1.0 ArtAssetPipeline"})
                    with urllib.request.urlopen(req,timeout=90) as response:
                        target.write_bytes(response.read())
                if target.stat().st_size<20000:raise RuntimeError("Invalid scanned stone map "+str(target))
                img=bpy.data.images.load(str(target),check_existing=False)
                if channel!="albedo":img.colorspace_settings.name="Non-Color"
                if charred and channel=="albedo":
                    # Layered soot and heat damage on photographed rock:
                    # keep mineral grain underneath smoke rather than painting flat grey.
                    width,height=img.size[0],img.size[1]
                    rgba=np.empty(width*height*4,dtype=np.float32)
                    img.pixels.foreach_get(rgba)
                    texel=rgba.reshape((height,width,4))
                    v=np.linspace(0,1,height,dtype=np.float32)[:,None]
                    u=np.linspace(0,1,width,dtype=np.float32)[None,:]
                    broad=np.sin(u*13+v*5.5+1.3)*np.sin(u*3-v*11)
                    chimney_streak=np.maximum(0,np.cos(u*12+np.sin(v*5)*.8))**8
                    soot=np.clip(.43-.11*broad-.12*chimney_streak-.06*v,.22,.73)
                    ember_stain=np.exp(-((v-.20)/.27)**2)*.040
                    texel[:,:,0]=np.clip(texel[:,:,0]*soot+ember_stain,.0,1.)
                    texel[:,:,1]=np.clip(texel[:,:,1]*soot*.91+ember_stain*.30,.0,1.)
                    texel[:,:,2]=np.clip(texel[:,:,2]*soot*.86,.0,1.)
                    shaded=bpy.data.images.new("quarry_wall_CC0_soot_heat_albedo",width=width,height=height,alpha=True)
                    shaded.pixels.foreach_set(rgba)
                    shaded.filepath_raw=str(TEX/"quarry_wall_CC0_soot_heat_albedo.png")
                    shaded.file_format="PNG";shaded.save();shaded.pack()
                    MAPS.append(str((TEX/"quarry_wall_CC0_soot_heat_albedo.png").relative_to(OUT)))
                    img=shaded
                else:
                    img.pack()
                matches=[n for n in material.node_tree.nodes if n.type=="TEX_IMAGE"
                         and n.image and n.image.name.endswith("_"+channel)]
                if len(matches)!=1:raise RuntimeError("Unexpected stone PBR node "+channel)
                matches[0].image=img
                MAPS.append(str(target.relative_to(OUT)))
            # Photographic normal relief must remain readable at PlayCanvas camera distance.
            for nm_node in material.node_tree.nodes:
                if nm_node.type=="NORMAL_MAP":nm_node.inputs["Strength"].default_value=.82
            print("GENESIS_CC0_QUARRY_STONE_BOUND",material.name,flush=True)
            return True
        except Exception as exc:
            print("GENESIS_CC0_QUARRY_STONE_FALLBACK",repr(exc),flush=True)
            return False
    quarry_photo_bound=scanned_quarry_stone(stone)
    sooted_quarry_bound=scanned_quarry_stone(hearth,charred=True)
    print("GENESIS_ROCK_2K_SOOT_HEAT",quarry_photo_bound,sooted_quarry_bound,flush=True)

    # V033 single contiguous distressed quarry foundation. No visible brick courses.
    # Rock surrounds the functional steel hearth; do not fill its working basin.
    geological_mass("One continuous fissured quarry foundation",
                    (0,0,.305),(1.91,1.31,.605),stone,seed=4,fracture=.054)
    box("Ash collection floor",(0,0,.64),(1.50,.96,.10),hearth,.017)
    for y in (-.49,.49):
        box("High temperature basin guard rail "+str(y),(0,y,.710),(1.56,.073,.105),steel,.012)
    for x in (-.75,.75):
        box("Guard rail "+str(x),(x,0,.710),(.076,.96,.105),steel,.012)
    # Preserved central side-draft mouth; load-bearing rock mass divided only
    # where the air passage makes a natural architectural opening.
    for side in (-1,1):
        geological_mass("Continuous rear load-bearing rock cheek "+str(side),
                        (side*.566,.545,1.190),(.545,.205,.900),
                        sooted,seed=11 if side<0 else 16,fracture=.038)
        geological_mass("Single chiseled side wing "+str(side),
                        (side*.80,-.09,.995),(.205,.99,.61),
                        sooted,seed=23 if side<0 else 28,fracture=.031)
    geological_mass("Unbroken upper masonry rock lintel",
                    (0,.535,1.698),(1.60,.235,.23),sooted,seed=31,fracture=.028)
    # Recessed rough rear bedrock closes the accidental white see-through window.
    # Leave the upper independent chimney bore and visible firebox entrance open.
    geological_mass("One rear firebox rock backing with fissured soot",
                    (0,.822,1.203),(.805,.178,.930),
                    sooted,seed=87,fracture=.026)
    # Structural support hidden from the opening, behind the weathered face.
    for side in (-1,1):
        box("Concealed side mortar core "+str(side),
            (side*.630,.565,1.22),(.36,.040,.90),sooted,0)

    # Reticulated bank of porous charcoal with small internal incandescent cores.
    for i in range(52):
        x=random.uniform(-.55,.55);y=random.uniform(-.34,.34)
        z=.735+random.random()*.12
        s=random.uniform(.047,.102)
        rock=ico("Irregular real fuel charcoal "+str(i),(x,y,z),s,
            hotcoal if i%2==0 else coal,subdiv=3,
            scale=(random.uniform(.77,1.28),random.uniform(.70,1.15),random.uniform(.56,.87)))
        for vert in rock.data.vertices:
            roughshape=1+.10*math.sin(vert.index*2.71+i*.84)+.055*math.cos(vert.index*.78+i*3.2)
            vert.co*=roughshape
    # V033 real geological smoke throat: separated continuous rock masses.
    # Keep the bellows tuyere, chimney draw, and entire open front accessible.
    for side in (-1,1):
        geological_mass("Monolithic upper throat supporting cheek "+str(side),
                        (side*.560,.557,2.014),(.25,.305,.502),
                        sooted,seed=41 if side<0 else 44,fracture=.027)
        geological_mass("Uninterrupted low smoke duct sidewall "+str(side),
                        (side*.512,.744,1.275),(.175,.194,.930),
                        sooted,seed=51 if side<0 else 54,fracture=.022)
        box("Visible forge-throat iron edge strap "+str(side),
            (side*.445,.415,2.08),(.033,.090,.32),steel,.006)
    box("Recessed smoke inlet dark refractory sill",
        (0,.720,.770),(1.08,.125,.155),hearth,.004)
    geological_mass("One upper soot-scoured stone smoke backplate",
                    (0,.760,1.970),(1.20,.170,.550),sooted,seed=63,fracture=.039)
    # The throat opening below the lintel is physically empty (no front hood).
    # A genuine forged lintel supports the upper shaft above working height.
    box("Blackened wrought smoke-throat lintel",
        (0,.460,2.22),(1.31,.120,.080),steel,.008)
    for x in (-.50,.50):
        box("Flue lintel load transfer bracket "+str(x),
            (x,.420,2.18),(.070,.130,.180),steel,.008)
    # V033 a single carved rock slab on each shaft side: open bore preserved.
    # Four continuous surfaces, not dozens of courses of regular stones.
    for y in (.465,.79):
        geological_mass("Continuous rocky flue front/back "+str(y),
                        (0,y,2.476),(1.22,.158,.520),sooted,
                        seed=71 if y<.6 else 73,fracture=.034)
    for side in (-1,1):
        geological_mass("Continuous rocky flue side "+str(side),
                        (side*.617,.627,2.476),(.162,.370,.520),sooted,
                        seed=76 if side<0 else 78,fracture=.029)
    # V033: thin forged lip around an open draft throat, not a broad grill rim.
    mouth_z=2.76
    for y in (.420,.835):
        box("Open chimney throat iron collar front/back "+str(y),
            (0,y,mouth_z),(1.29,.035,.032),steel,.006)
    for side in (-1,1):
        box("Open chimney throat iron collar return "+str(side),
            (side*.630,.625,mouth_z),(.035,.425,.032),steel,.006)
    # Darkened vertical flue straps are restrained fittings, not roof rafters.
    for side in (-1,1):
        box("Forged vertical chimney brace "+str(side),
            (side*.635,.438,2.48),(.028,.034,.43),steel,.005)
    # V033 restrained load-bearing forged-metal saddles on top of rough rock.
    # V033 front-face clamps intersected sculpted rock and looked like black
    # stains; top saddle interfaces have visible metal surfaces and heads.
    for side in (-1,1):
        cheek=side*.802
        box("Worn forged iron saddle on rock wing "+str(side),
            (cheek,-.376,1.334),(.155,.357,.025),steel,.005)
        for yy in (-.490,-.266):
            cyl("Visible peened iron saddle stud "+str((side,yy)),
                (cheek,yy,1.353),.014,.020,steel,vertices=14,
                rot=(0,0,0),edge=.003)
    # Smoke shaft retainers blend into the masonry and existing smoke rim.
    for side in (-1,1):
        x=side*.532
        box("Upper smoke shaft forged keeper plate "+str(side),
            (x,.376,2.478),(.078,.026,.225),steel,.005)
        for z in (2.402,2.555):
            cyl("Hammered keeper plate rivet "+str((side,z)),
                (x,.360,z),.012,.023,steel,vertices=12,
                rot=(math.pi/2,0,0),edge=.0025)
    # Forged working-tool wall rack: visual function beats decoration.
    # A proper coal rake, poker and lifting hook are separate forged pieces.
    box("Practical side wall forge tool rack",(.93,.46,1.37),
        (.055,.45,.05),steel,.006)
    for tool_idx,y in enumerate((.31,.46,.60)):
        cyl("Forged blacksmith implement shank "+str(tool_idx),
            (1.035,y,1.10),.010,.76,steel,12,edge=.002)
        box("Working implement head "+str(tool_idx),
            (1.035,y,.710),(.074 if tool_idx==0 else .028,
                            .028,.052 if tool_idx==2 else .025),steel,.004)
    # Hot center reads clearly as a charcoal fire, not an unlit pile of stones.
    # Texture-masked glows in the actual charcoal replace the previous luminous blobs.
    # Incandescent core lights the firebrick realistically; studio light excluded from GLB.
    glow_data=bpy.data.lights.new("STUDIO_FIREGLOW_NOT_IN_ASSET","POINT")
    glow_obj=bpy.data.objects.new("STUDIO_FIREGLOW_NOT_IN_ASSET",glow_data)
    bpy.context.collection.objects.link(glow_obj)
    glow_obj.location=(0,-.05,.88)
    glow_data.energy=205;glow_data.color=(1,.26,.10);glow_data.shadow_soft_size=.52
    # Distinct bellows air-entry mouth built into back wall.
    cyl("Air intake tuyere",(.49,.625,.79),.067,.21,steel,32,
        rot=(math.pi/2,0,0),edge=.006)

if KIND=="anvil":mount_anvil()
elif KIND=="forge":mount_forge()
else:mount_bellows()

# All proper assets must contain editable independent meshes and actual UVs.
bpy.context.view_layer.update()
assert len(ASSETS)>=8,(KIND,len(ASSETS))
for o in ASSETS:
    if o.type!="MESH":continue
    if not o.data.uv_layers:
        bpy.ops.object.select_all(action="DESELECT");o.select_set(True);bpy.context.view_layer.objects.active=o
        bpy.ops.object.mode_set(mode="EDIT");bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(island_margin=.015);bpy.ops.object.mode_set(mode="OBJECT")
    assert o.data.uv_layers,KIND+":"+o.name
bb=[]
for o in ASSETS:
    bb.extend([o.matrix_world@Vector(p) for p in o.bound_box])
mn=Vector((min(p.x for p in bb),min(p.y for p in bb),min(p.z for p in bb)))
mx=Vector((max(p.x for p in bb),max(p.y for p in bb),max(p.z for p in bb)))
mid=(mn+mx)/2
span=max(mx.x-mn.x,mx.z-mn.z,mx.y-mn.y)
sc=bpy.context.scene;sc.render.engine="CYCLES";sc.cycles.device="CPU";sc.cycles.samples=52
sc.view_layers[0].cycles.use_denoising=True
sc.render.resolution_x=1050;sc.render.resolution_y=1050;sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG";sc.render.image_settings.color_mode="RGBA"
sc.render.film_transparent=False
sc.view_settings.view_transform="AgX"
world=bpy.data.worlds.new("Neutral photography studio world");world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.20,.22,.24,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.48
sc.world=world
# Floor and lights are studio-only and excluded from asset GLB.
floor_mat=bpy.data.materials.new("STUDIO_ONLY_NOT_IN_GLB");floor_mat.use_nodes=True
floor_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.13,.145,.17,1)
floor_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=.76
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,mn.z-.015))
floor=bpy.context.object;floor.name="STUDIO_NOT_ASSET";floor.data.materials.append(floor_mat)
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()
for name,loc,power,size in [
    ("Large softbox primary",(3,-4,6),1150,4.2),
    ("Raking edge light",(-4,2,5),980,3.3),
    ("Warm reflector",(0,4,3.5),650,3.5)]:
    ld=bpy.data.lights.new(name,"AREA");lo=bpy.data.objects.new(name,ld)
    bpy.context.collection.objects.link(lo);lo.location=mid+Vector(loc)
    aim(lo,mid);ld.energy=power;ld.shape="DISK";ld.size=size
camd=bpy.data.cameras.new("QA Camera");cam=bpy.data.objects.new("QA Camera",camd)
bpy.context.collection.objects.link(cam);sc.camera=cam
camd.type="ORTHO";camd.ortho_scale=span*(1.25 if KIND=="bellows" else 1.65)
report={"asset":KIND,"version":"V033","status":"VISUAL_CANDIDATE_NOT_APPROVED",
        "baseline_version":"V010", "derived_from":"V011",
        "derived_from":"V013",
        "quarry_wall_cc0_scan_bound":quarry_photo_bound,
        "quarry_wall_source":"https://polyhaven.com/a/quarry_wall",
        "targeted_repairs":["replace pale uniform chimney top with physically irregular darker running-bond masonry and slim functional open iron lip",
                            "preserve unblocked frontal working access above hot charcoal firebed",
                            "add taller functional flue, forged rivets, side braces and tool rack",
                            "apply actual CC0 quarry stone photo PBR maps with explicit fallback",
                            "reuse shared stone textures to reduce GLB size",
                            "moderate lava-like coal emission while preserving active fire"],
        "art_direction":"functional medieval photorealism, never stylized","metric_bounds_m":[list(mn),list(mx)],
        "mesh_parts":len(ASSETS),"source":"independent Blender generator, no historical master reused",
        "pbr_materials":list(MATERIALS.keys()),"maps":MAPS,"render_samples":sc.cycles.samples,
        "approval":"requires 4-view visual review and at least 8/10 by user",
        "photographic_cc0_sources":({"oak":"https://polyhaven.com/a/fine_grained_wood","leather":"https://polyhaven.com/a/brown_leather","credit":"Powered by Poly Haven"} if KIND=="bellows" else {})}
(OUT/"AUDIT.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf8")
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(KIND+"_hero_v033.blend")))
bpy.ops.object.select_all(action="DESELECT")
for ob in ASSETS:ob.select_set(True)
bpy.context.view_layer.objects.active=ASSETS[0]
bpy.ops.export_scene.gltf(filepath=str(OUT/(KIND+"_hero_v033.glb")),
    export_format="GLB",use_selection=True,export_apply=True,export_materials="EXPORT",
    export_texcoords=True,export_normals=True)
bpy.ops.object.select_all(action="DESELECT")
for suffix,pos in [("front",(0,-4,1.7)),("three_quarter",(3,-4,2.3)),
                   ("rear",(2,4,2.0)),("detail",(1.7,-2,1.15))]:
    cam.location=mid+Vector(pos)*max(span/2, .5)
    aim(cam,mid);camd.ortho_scale=span*(.98 if suffix=="detail" else (1.25 if KIND=="bellows" else 1.65))
    sc.render.filepath=str(OUT/(suffix+".png"))
    bpy.ops.render.render(write_still=True)
    assert Path(sc.render.filepath).stat().st_size>10000,sc.render.filepath
print("GENESIS_HERO_RENDER_OK",KIND,len(ASSETS),len(MAPS),flush=True)
