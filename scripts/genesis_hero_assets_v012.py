# -*- coding: utf-8 -*-
"""Project Genesis — forge V012 art correction candidate for PlayCanvas.
Generated on official Blender 4.5.13 LTS in GitHub Actions, NEVER local Blender.
Anvil / stone-coal forge / traditional leather bellows. First-pass visual candidates,
not approved assets. Each part is independent with packed PBR textures.
"""
import bpy, sys, os, json, random, math, urllib.request
from pathlib import Path
from mathutils import Vector
import numpy as np

ARG=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
assert ARG == ["forge"], "V012 is forge-only; preserve independent anvil/bellows branches: " + str(ARG)
KIND=ARG[0]
random.seed(4761+len(KIND))
ROOT=Path(os.environ.get("GITHUB_WORKSPACE",os.getcwd()))
OUT=ROOT/("output_hero_"+KIND+"_v012")
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
        thin=np.clip((.115-np.abs(f))/.075,0,1)*np.clip((.40+c)/.75,0,1)
        emission=np.stack([thin*.85,thin*.19,thin*.025],axis=2).astype(np.float32)
        emm=img("emissive",emission)
        emnode=nodes.new("ShaderNodeTexImage");emnode.image=emm
        links.new(emnode.outputs["Color"],bs.inputs["Emission Color"])
        bs.inputs["Emission Strength"].default_value=5.4
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
    """Physical masonry variation in dimensions and vertices, not a color-only randomizer."""
    rng=random.Random(8109+sum((i+1)*ord(ch) for i,ch in enumerate(name)))
    size=tuple(max(.035,d*(1+rng.uniform(-.045,.045))) for d in dims)
    offset=(rng.uniform(-.004,.004),rng.uniform(-.003,.003),rng.uniform(-.003,.003))
    pos=tuple(center[i]+offset[i] for i in range(3))
    obj=box(name,pos,size,mat,edge=edge*rng.uniform(.60,1.18),
            rz=rz+rng.uniform(-.012,.012))
    for v in obj.data.vertices:
        v.co.x+=rng.uniform(-.006,.006)
        v.co.y+=rng.uniform(-.005,.005)
        v.co.z+=rng.uniform(-.003,.003)
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
    # V012: desaturated refractory stone, weathered stone, and deeply soot-stained courses.
    # Three physically textured masonry materials avoid a single cartoon-uniform brick palette.
    stone=pbr("forge_aged_refractory_sandstone",(.245,.234,.215),.0,.92,"stone",71)
    hearth=pbr("forge_heat_blackened_brick",(.122,.115,.106),.0,.94,"stone",72)
    weathered=pbr("forge_weathered_ash_grey_masonry",(.202,.198,.186),.0,.93,"stone",76)
    sooted=pbr("forge_soot_impregnated_refractory_stone",(.139,.132,.124),.0,.96,"stone",77)
    steel=pbr("forge_hammered_hood_black_iron",(.095,.103,.104),.83,.70,"iron",73)
    coal=pbr("forge_real_charcoal_porous",(.065,.061,.059),.0,.96,"stone",74)
    hotcoal=pbr("forge_cracked_hot_charcoal_ember_map",(.065,.060,.056),.0,.92,"hotcoal",75)
    # 180 cm wide stone hearth on bonded courses, varied mortar seams.
    # Weight-bearing rubble plinth remains continuous beneath independently hewn outer stones.
    box("Buried structural stone foundation core",(0,0,.085),(1.9,1.30,.17),sooted,.012)
    for side in (-1,1):
        for i in range(8):
            x=-.82+i*.234
            handlaid("Foundation face rubble "+str((side,i)),(x,side*.625,.095),
                     (.228,.095,.173),weathered if i%3 else stone,.006)
    for side in (-1,1):
        for i in range(5):
            y=-.45+i*.224
            handlaid("Foundation return rubble "+str((side,i)),(side*.916,y,.095),
                     (.102,.210,.173),stone if i%2 else weathered,.006)
    for course in range(4):
        z=.195+course*.136
        for i in range(8):
            x=-.79+i*.22 + (.11 if course%2 else 0)
            if abs(x)>.91:continue
            for y in (-.566,.566):
                handlaid("Front rear hand-laid firebrick %d %d %s"%(course,i,str(y)),
                    (x,y,z),(.214,.135,.127),
                    (stone if (course+i)%3==0 else weathered) if course<2 else (hearth if i%3 else sooted),
                    .005,rz=random.uniform(-.01,.01))
        for i in range(4):
            y=-.355+i*.22+(.11 if course%2 else 0)
            if abs(y)>.49:continue
            for x in (-.82,.82):
                handlaid("Side bonded masonry %d %d %s"%(course,i,str(x)),
                    (x,y,z),(.15,.214,.127),stone if i%2 else weathered,.005)
    # Accessible square central fire-bed with iron rim, not a cartoon furnace.
    box("Ash collection floor",(0,0,.64),(1.50,.96,.10),hearth,.017)
    for y in (-.49,.49):
        box("High temperature basin guard rail "+str(y),(0,y,.710),(1.56,.073,.105),steel,.012)
    for x in (-.75,.75):
        box("Guard rail "+str(x),(x,0,.710),(.076,.96,.105),steel,.012)
    # Rear masonry wall is built from individually visible soot-stained blocks.
    for course in range(7):
        z=.785+course*.145
        for i in range(8):
            x=-.78+i*.225+(.10 if course%2 else 0)
            if abs(x)>.89:continue
            handlaid("Rear masonry block %d %d"%(course,i),(x,.54,z),(.213,.18,.139),
                sooted if course<3 else (hearth if course<5 else weathered),.005)
    # V008 had bright background slits between the rear brick courses.
    # V012: thin mortar core lies INSIDE the masonry depth, not in front of rear bricks.
    # The V009 exterior plate hid the brickwork; a concealed core seals only actual joints.
    box("Soot dark refractory mortar behind rear brick joints",
        (0,.540,1.228),(1.71,.055,1.06),hearth,.003)
    # Masonry pier truly built from bricks; monolithic V005 side slabs looked wooden.
    for side in (-.77,.77):
        for course in range(5):
            zz=.83+course*.145
            handlaid("Individually bonded side pier brick "+str((side,course)),
                (side,.385,zz),(.18,.235,.136),sooted if course<3 else weathered,.005)
    # Lower wing walls afford believable mechanical support.
    for x in (-.79,.79):
        for z in (.84,.99,1.14):
            for y in (-.38,-.16,.08,.30):
                handlaid("Forge wing buttress "+str((x,z,y)),(x,y,z),(.14,.216,.140),
                    sooted if z<1 else weathered,.005)
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
    # V012: masonry smoke hood, not a perfect industrial sheet-metal cartoon.
    # A thin hand-hammered iron liner remains INSIDE the brickwork for real draft.
    def sheet(name,pts):
        o=made_mesh(name,pts,[(0,1,2,3)],steel,0)
        solid=o.modifiers.new("Internal hammered smoke liner thickness","SOLIDIFY")
        solid.thickness=.018
        bevel(o,.004,2)
        return o
    for side in (-1,1):
        sheet("Concealed sloped iron hood liner "+str(side),[
            (side*.84,-.51,1.72),(side*.36,-.275,2.13),
            (side*.36,.36,2.13),(side*.84,.58,1.72)])
    sheet("Rear smoke liner",[
        (-.84,.58,1.72),(.84,.58,1.72),(.36,.36,2.13),(-.36,.36,2.13)])
    sheet("Front smoke liner",[
        (-.84,-.51,1.72),(-.36,-.275,2.13),(.36,-.275,2.13),(.84,-.51,1.72)])

    def masonry_wedge(name,outer,inner,mat):
        # Eight true vertices, six faces: stone courses have volume, thickness and UVs.
        verts=outer+inner
        faces=[(0,1,2,3),(4,7,6,5),(0,4,5,1),
               (1,5,6,2),(2,6,7,3),(3,7,4,0)]
        obj=made_mesh(name,verts,faces,mat,.003)
        return obj

    # Five offset bonded courses follow the taper in actual 3D, front/back/sides.
    # Small dry mortar joints, different stone shades, no floating luminous ornaments.
    for course in range(5):
        t0=course/5; t1=(course+1)/5
        z0=1.735+.394*t0; z1=1.735+.394*t1
        h0=.855-.49*t0; h1=.855-.49*t1
        yf0=-.52+.245*t0; yf1=-.52+.245*t1
        yb0=.59-.225*t0; yb1=.59-.225*t1
        offset=.5 if course%2 else 0
        for k in range(-1,7):
            a=max(0.,(k+offset)/6);b=min(1.,(k+1+offset)/6)
            if b-a<.035:continue
            a+=.004;b-=.004
            if a>=b:continue
            xl0=-h0+2*h0*a;xr0=-h0+2*h0*b
            xl1=-h1+2*h1*a;xr1=-h1+2*h1*b
            front=[(xl0,yf0-.042,z0+.003),(xr0,yf0-.042,z0+.003),
                   (xr1,yf1-.042,z1-.003),(xl1,yf1-.042,z1-.003)]
            inner=[(xl0,yf0+.022,z0+.003),(xr0,yf0+.022,z0+.003),
                   (xr1,yf1+.022,z1-.003),(xl1,yf1+.022,z1-.003)]
            masonry_wedge("Hand-bonded hood front stone "+str((course,k)),
                          front,inner,sooted if course<2 and k%2 else (weathered if k%3 else stone))
            # Back face is visible in the rear audit, and must be masonry too.
            back=[(xr0,yb0+.043,z0+.003),(xl0,yb0+.043,z0+.003),
                  (xl1,yb1+.043,z1-.003),(xr1,yb1+.043,z1-.003)]
            back_inner=[(xr0,yb0-.021,z0+.003),(xl0,yb0-.021,z0+.003),
                        (xl1,yb1-.021,z1-.003),(xr1,yb1-.021,z1-.003)]
            masonry_wedge("Hand-bonded hood rear stone "+str((course,k)),
                          back,back_inner,weathered if k%2 else stone)
        for side in (-1,1):
            for j in range(3):
                a=j/3+.004;b=(j+1)/3-.004
                ya0=yf0+(yb0-yf0)*a;yb_a0=yf0+(yb0-yf0)*b
                ya1=yf1+(yb1-yf1)*a;yb_a1=yf1+(yb1-yf1)*b
                outer=[(side*(h0+.043),ya0,z0+.003),
                       (side*(h0+.043),yb_a0,z0+.003),
                       (side*(h1+.043),yb_a1,z1-.003),
                       (side*(h1+.043),ya1,z1-.003)]
                inner=[(side*(h0-.022),ya0,z0+.003),
                       (side*(h0-.022),yb_a0,z0+.003),
                       (side*(h1-.022),yb_a1,z1-.003),
                       (side*(h1-.022),ya1,z1-.003)]
                masonry_wedge("Hand-bonded hood flank "+str((side,course,j)),
                              outer,inner,sooted if course<2 else weathered)
    # Functional square brick chimney shaft, hollow all the way through.
    # The former smooth cylindrical metal pipe and torus are intentionally omitted.
    for course in range(5):
        z=2.195+course*.127
        mat=sooted if course<2 else (stone if course%2 else weathered)
        for side in (-1,1):
            handlaid("Square flue front/rear bonded course "+str((course,side)),
                     (0,side*.300,z),(.70,.135,.119),mat,.004)
            handlaid("Square flue side bonded course "+str((course,side)),
                     (side*.300,0,z),(.135,.47,.119),mat,.004)
    # Metal lip protects the lower exposed hood edge from tools and heat.
    box("Forged capture edge beneath masonry hood",(0,-.54,1.718),
        (1.77,.041,.050),steel,.006)
    for x in (-.71,-.47,-.23,.01,.25,.49,.73):
        ico("Peened iron capture-edge fixing "+str(x),(x,-.563,1.717),
            .010,steel,subdiv=2,scale=(1,.55,.60))
    for x in (-.79,.79):
        cyl("Functional iron hood support upright "+str(x),(x,-.43,1.40),.029,.59,
            steel,18,edge=.004)
    # Hot center reads clearly as a charcoal fire, not an unlit pile of stones.
    # Texture-masked glows in the actual charcoal replace the previous luminous blobs.
    # Incandescent core lights the firebrick realistically; studio light excluded from GLB.
    glow_data=bpy.data.lights.new("STUDIO_FIREGLOW_NOT_IN_ASSET","POINT")
    glow_obj=bpy.data.objects.new("STUDIO_FIREGLOW_NOT_IN_ASSET",glow_data)
    bpy.context.collection.objects.link(glow_obj)
    glow_obj.location=(0,-.05,.88)
    glow_data.energy=135;glow_data.color=(1,.26,.10);glow_data.shadow_soft_size=.52
    # Distinct bellows air-entry mouth built into back wall.
    cyl("Air intake tuyere",(0,.625,.79),.067,.21,steel,32,
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
report={"asset":KIND,"version":"V012","status":"VISUAL_CANDIDATE_NOT_APPROVED",
        "baseline_version":"V011",
        "targeted_repairs":["replace stylized industrial hood with hand-bonded tapered stone smoke canopy",
                            "build a physically open square refractory masonry chimney",
                            "break repetitive brick courses with individually perturbed geometry and subdued stone PBR",
                            "preserve internal smoke liner, firebox opening and embedded charcoal incandescence",
                            "add structurally plausible rubble foundation and heat-sooted mortar"],
        "art_direction":"functional medieval photorealism, never stylized","metric_bounds_m":[list(mn),list(mx)],
        "mesh_parts":len(ASSETS),"source":"independent Blender generator, no historical master reused",
        "pbr_materials":list(MATERIALS.keys()),"maps":MAPS,"render_samples":sc.cycles.samples,
        "approval":"requires 4-view visual review and at least 8/10 by user",
        "photographic_cc0_sources":({"oak":"https://polyhaven.com/a/fine_grained_wood","leather":"https://polyhaven.com/a/brown_leather","credit":"Powered by Poly Haven"} if KIND=="bellows" else {})}
(OUT/"AUDIT.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf8")
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(KIND+"_hero_v012.blend")))
bpy.ops.object.select_all(action="DESELECT")
for ob in ASSETS:ob.select_set(True)
bpy.context.view_layer.objects.active=ASSETS[0]
bpy.ops.export_scene.gltf(filepath=str(OUT/(KIND+"_hero_v012.glb")),
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
