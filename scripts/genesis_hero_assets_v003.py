# -*- coding: utf-8 -*-
"""Project Genesis — realistic medieval hero asset candidates for PlayCanvas.
Generated on official Blender 4.5.13 LTS in GitHub Actions, NEVER local Blender.
Anvil / stone-coal forge / traditional leather bellows. First-pass visual candidates,
not approved assets. Each part is independent with packed PBR textures.
"""
import bpy, sys, os, json, random, math
from pathlib import Path
from mathutils import Vector
import numpy as np

ARG=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
assert len(ARG)==1 and ARG[0] in ("anvil","forge","bellows"),ARG
KIND=ARG[0]
random.seed(4761+len(KIND))
ROOT=Path(os.environ.get("GITHUB_WORKSPACE",os.getcwd()))
OUT=ROOT/("output_hero_"+KIND+"_v003")
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
        height=.50+.021*c+.012*f+.012*micro-.012*scratches
        shade=.975+.027*c+.016*f+.012*micro-.032*scratches
        pores=.012*scratches
    elif kind=="wood":
        grain=np.sin(2*np.pi*(v*79+u*.91+.18*c+.12*np.sin(u*15)))
        grain2=np.sin(2*np.pi*(v*193+u*.48+.07*f))
        height+=.09*grain+.028*grain2
        shade=.93+.18*grain+.04*grain2+.07*c-.04*np.maximum(0,macro)
        pores=np.maximum(0,-grain2)*.045
    elif kind=="leather":
        grain=np.sin(v*350+np.sin(u*90)*.6)
        height+=.025*grain+.04*np.maximum(0,micro)
        shade=.90+.085*c+.025*grain+.07*macro
        pores=np.maximum(0,micro-.45)*.03
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
    roughmap=np.clip(rough+.09*c+.025*micro+pores,.15,.96).astype(np.float32)
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
    nm=nodes.new("ShaderNodeNormalMap");nm.inputs["Strength"].default_value=(.21 if kind=="steelpolish" else .44)
    links.new(ac.outputs["Color"],bs.inputs["Base Color"])
    links.new(rr.outputs["Color"],bs.inputs["Roughness"])
    links.new(no.outputs["Color"],nm.inputs["Color"])
    links.new(nm.outputs["Normal"],bs.inputs["Normal"])
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
    iron=pbr("anvil_forged_wrought_iron",(.125,.128,.126),.90,.65,"iron",11)
    steel=pbr("anvil_polished_hardened_steel",(.315,.323,.323),.93,.29,"steelpolish",12)
    oak=pbr("anvil_old_oak_base",(.29,.174,.088),.02,.76,"wood",14)
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
    box("Anvil true hardened flat working face",(-.105,0,.753),(.53,.265,.041),steel,.009)
    # Fully modeled rounded horn tapers in 18 forged sections to a real tip.
    rings=[]
    for k in range(19):
        t=k/18
        x=-.365-.51*t
        yr=.124*(1-t)**.87+.002
        zr=.082*(1-t)**1.13+.002
        z=.735-.030*t+.007*math.sin(math.pi*t)
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
    faces.extend([tuple(reversed(range(nv))),tuple((len(rings)-1)*nv+j for j in range(nv))])
    made_mesh("Functional rounded horn with forged draw",verts,faces,steel,.001)
    heel=box("Rectangular heel with real tool holes",(.382,0,.737),(.35,.25,.086),steel,0)
    hard_cut(heel,"Hardy_square_hole_actual_opening",(.467,.015,.74),(.073,.073,.21))
    hard_cut(heel,"Pritchel_round_hole_actual_opening",(.338,-.076,.741),(.01,.01,.21),radius=.019)
    bevel(heel,.008,3)
    # Distinct hammered banding across body; no cartoonized grooves.
    for z in (.30,.615):
        box("Forge upsetting witness band "+str(z),(0,-.139,z),(.52,.012,.010),dark,.003)
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

def mount_bellows():
    wood=pbr("bellows_aged_oak_long_grain",(.285,.153,.064),.01,.71,"wood",32)
    leather=pbr("bellows_creased_dark_oxblood_leather",(.168,.079,.049),.02,.79,"leather",33)
    iron=pbr("bellows_oxidized_hand_forged_iron",(.112,.118,.118),.82,.62,"iron",34)
    brass=pbr("bellows_patina_riveted_brass",(.43,.29,.14),.72,.55,"iron",35)
    # Hand shaped pear wood boards, not beveled boxes or flat icon shapes.
    outline=[(-.76,-.14),(-.66,-.235),(-.45,-.32),(-.18,-.355),(.05,-.32),(.25,-.24),(.45,-.15),(.62,-.095),(.68,0),(.62,.095),(.45,.15),(.25,.24),(.05,.32),(-.18,.355),(-.45,.32),(-.66,.235)]
    def board(name,z,thickness):
        n=len(outline);verts=[(x,y,z+oz) for oz in (-thickness/2,thickness/2) for x,y in outline]
        faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
        for i in range(n):
            j=(i+1)%n;faces.append((i,j,n+j,n+i))
        return made_mesh(name,verts,faces,wood,.013)
    board("Removable bottom solid oak board",.10,.046)
    board("Top shaped oak bellows board",.35,.050)
    # True volumetric folded gusset in twelve visible double leather creases.
    n=len(outline);verts=[]
    for level,z in enumerate((.126,.168,.212,.254,.299,.325)):
        factor=1 + (.085 if level in (1,3) else -.048)
        for x,y in outline:
            verts.append((x,y*factor,z))
    faces=[]
    for level in range(5):
        for i in range(n):
            j=(i+1)%n
            faces.append((level*n+i,level*n+j,(level+1)*n+j,(level+1)*n+i))
    made_mesh("Hand stitched multi-fold leather air chamber",verts,faces,leather,.001)
    # Distinct leather edge seams and hand hammered perimeter rivets.
    for i,(x,y) in enumerate(outline):
        if i%2==0:
            for z in (.133,.317):
                ico("Small peened brass nail %02d "%i+str(z),(x*.985,y*.96,z),.013,brass,subdiv=2,scale=(1,.78,.45))
    cyl("Forged tubular forward air nozzle",(.70,0,.224),.060,.32,iron,40,rot=(0,math.pi/2,0),edge=.006)
    cyl("Narrow brass nozzle ring",(.852,0,.224),.063,.019,brass,40,rot=(0,math.pi/2,0),edge=.003)
    for z in (.116,.36):
        box("Hinged oak rear squeeze handle "+str(z),(-.755,0,z),(.35,.085,.056),wood,.022)
        cyl("Forged rear pivot pin "+str(z),(-.62,0,z),.027,.10,iron,20,rot=(math.pi/2,0,0),edge=.002)
    # The dark inner bore prevents the brass mouth from reading as a solid wooden plug.\n    cyl("Darkened nozzle throat air opening",(.864,0,.224),.041,.003,iron,40,rot=(0,math.pi/2,0),edge=0)\n    # Proper stitched leather welts on both oak-board contact lines.
    # The source splines are converted to real polygon meshes for glTF.
    for z in (.135,.321):
        curve=bpy.data.curves.new("Continuous hand-cut leather welt","CURVE")
        curve.dimensions="3D";curve.resolution_u=16
        curve.bevel_depth=.008;curve.bevel_resolution=2
        spline=curve.splines.new("POLY");spline.points.add(len(outline)-1)
        for point,(x,y) in zip(spline.points,outline):
            point.co=(x*.992,y*.990,z,1)
        spline.use_cyclic_u=True
        o=bpy.data.objects.new("Perimeter hand stitched leather welt "+str(z),curve)
        bpy.context.collection.objects.link(o)
        track(o,leather)
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True);bpy.context.view_layer.objects.active=o
        bpy.ops.object.convert(target="MESH")
    for i,(x,y) in enumerate(outline):
        if i%2==0:
            ico("Bronze nail fixing leather gusset "+str(i),
                (x*.975,y*.97,.326),.009,brass,subdiv=2,scale=(1,1,.5))
    # No unverified animation: independent boards remain animation-ready components.

def mount_forge():
    stone=pbr("forge_sooted_old_firebrick",(.315,.265,.215),.01,.84,"stone",71)
    hearth=pbr("forge_heat_blackened_brick",(.125,.110,.102),.0,.91,"stone",72)
    steel=pbr("forge_hammered_hood_black_iron",(.095,.103,.104),.83,.70,"iron",73)
    coal=pbr("forge_real_charcoal_porous",(.065,.061,.059),.0,.96,"stone",74)
    ember=emissive("Forge_glowing_hot_charcoal",(.67,.075,.008),1.3)
    # 180 cm wide stone hearth on bonded courses, varied mortar seams.
    box("Crushed stone foundation",(0,0,.085),(1.9,1.30,.17),stone,.022)
    for course in range(4):
        z=.195+course*.136
        for i in range(8):
            x=-.79+i*.22 + (.11 if course%2 else 0)
            if abs(x)>.91:continue
            for y in (-.566,.566):
                box("Front rear hand-laid firebrick %d %d %s"%(course,i,str(y)),
                    (x,y,z),(.214,.135,.127),stone if course<2 else hearth,.011,rz=random.uniform(-.01,.01))
        for i in range(4):
            y=-.355+i*.22+(.11 if course%2 else 0)
            if abs(y)>.49:continue
            for x in (-.82,.82):
                box("Side bonded masonry %d %d %s"%(course,i,str(x)),
                    (x,y,z),(.15,.214,.127),stone,.010)
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
            box("Rear masonry block %d %d"%(course,i),(x,.54,z),(.213,.18,.139),
                hearth if course<4 else stone,.011)
    # Lower wing walls afford believable mechanical support.
    for x in (-.79,.79):
        for z in (.84,.99,1.14):
            for y in (-.38,-.16,.08,.30):
                box("Forge wing buttress "+str((x,z,y)),(x,y,z),(.14,.216,.140),
                    hearth if z<1 else stone,.009)
    # Reticulated bank of porous charcoal with small internal incandescent cores.
    for i in range(52):
        x=random.uniform(-.55,.55);y=random.uniform(-.34,.34)
        z=.735+random.random()*.12
        s=random.uniform(.047,.102)
        ico("Irregular real fuel charcoal "+str(i),(x,y,z),s,coal,subdiv=1,
            scale=(random.uniform(.75,1.3),random.uniform(.70,1.18),random.uniform(.65,.94)))
        if i%6==0:
            ico("Faint translucent ember glints between charcoal "+str(i),(x,y,z+.029),s*.37,
                ember,subdiv=2,scale=(.81,.86,.48))
    # Hand hammered trapezoidal smoke capture hood: sloping SHEETS not a cubic box.
    # Plate thickness physically modeled using Solidify; front opening stays clear.
    def sheet(name,pts):
        o=made_mesh(name,pts,[(0,1,2,3)],steel,0)
        solid=o.modifiers.new("Realistic hand-forged sheet thickness","SOLIDIFY")
        solid.thickness=.027
        bevel(o,.005,3)
        return o
    for side in (-1,1):
        sheet("Sloped side of smoke-collector funnel "+str(side),[
            (side*.84,-.51,1.72),(side*.36,-.275,2.13),
            (side*.36,.36,2.13),(side*.84,.58,1.72)])
    sheet("Soot-black rear sheet of chimney funnel",[
        (-.84,.58,1.72),(.84,.58,1.72),(.36,.36,2.13),(-.36,.36,2.13)])
    box("Front capture lip",(0,-.51,1.725),(1.77,.049,.066),steel,.012)
    box("Top forged collar beneath flue",(0,.065,2.13),(.80,.72,.077),steel,.009)
    pipe=cyl("Hollow soot-black chimney exhaust flue",(0,.07,2.42),.265,.62,
             steel,vertices=48,edge=0)
    hard_cut(pipe,"True empty internal chimney bore",(0,.07,2.42),(.0,.0,.82),radius=.210)
    bevel(pipe,.007,3)
    # Actual open torus collar: previous V002 cylindrical band sealed the chimney.
    bpy.ops.mesh.primitive_torus_add(major_segments=48,minor_segments=12,
        location=(0,.07,2.72),major_radius=.253,minor_radius=.025)
    o=bpy.context.object;o.name="OPEN chimney lip torus with unobstructed draft"
    track(o,steel)
    for x in (-.79,.79):
        cyl("Permanently riveted side hood upright "+str(x),(x,-.43,1.40),.032,.59,
            steel,18,edge=.004)
    # Hot center reads clearly as a charcoal fire, not an unlit pile of stones.
    for ix in range(4):
        x=-.28+ix*.185
        ico("Deep glowing core between coal pieces "+str(ix),(x,.07,.773),
            .031,ember,subdiv=2,scale=(1.15,1,.35))
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
sc=bpy.context.scene;sc.render.engine="CYCLES";sc.cycles.device="CPU";sc.cycles.samples=40
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
report={"asset":KIND,"version":"V003","status":"VISUAL_CANDIDATE_NOT_APPROVED",
        "art_direction":"functional medieval photorealism, never stylized","metric_bounds_m":[list(mn),list(mx)],
        "mesh_parts":len(ASSETS),"source":"independent Blender generator, no historical master reused",
        "pbr_materials":list(MATERIALS.keys()),"maps":MAPS,"render_samples":sc.cycles.samples,
        "approval":"requires 4-view visual review and at least 8/10 by user"}
(OUT/"AUDIT.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf8")
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(KIND+"_hero_v003.blend")))
bpy.ops.object.select_all(action="DESELECT")
for ob in ASSETS:ob.select_set(True)
bpy.context.view_layer.objects.active=ASSETS[0]
bpy.ops.export_scene.gltf(filepath=str(OUT/(KIND+"_hero_v003.glb")),
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
