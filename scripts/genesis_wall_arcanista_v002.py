# Project Genesis / PlayCanvas - distinct workshop wall geometry trials.
# Executed only by Blender 4.5.13 LTS in public GitHub Actions.
# Experimental, neither the wall nor the V011 door is approved here.
import bpy, math, random, json
from pathlib import Path
from mathutils import Vector
from math import sin, cos, pi
import numpy as np

KIND="arcanista"
VERSION="v004" if KIND=="herrero" else "v002"
SEED=29012026 if KIND=="herrero" else 29022026
rng=random.Random(SEED)
ROOT=Path("output_workshop_wall_"+KIND+"_"+VERSION).resolve()
ROOT.mkdir(parents=True,exist_ok=True)
INPUT=Path("inputs/wall_"+KIND+"_"+VERSION).resolve()
W,H,T=7.875,3.20,.48
DW,DH=1.48,2.43
PREFIX="ASSET_"
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def image(filename,srgb=True):
    a=bpy.data.images.load(str(INPUT/filename),check_existing=True)
    a.colorspace_settings.name="sRGB" if srgb else "Non-Color"
    return a
def darken_scan(filename,filename_out,factors):
    src=image(filename)
    width,height=src.size[:]
    px=np.empty(width*height*4,dtype=np.float32)
    src.pixels.foreach_get(px)
    arr=px.reshape((-1,4))
    for k in range(3):arr[:,k]=np.clip(arr[:,k]*factors[k],0,1)
    result=bpy.data.images.new(filename_out,width=width,height=height,alpha=False,float_buffer=False)
    result.pixels.foreach_set(px)
    result.filepath_raw=str(ROOT/(filename_out+".jpg"))
    result.file_format="JPEG";result.save()
    result.colorspace_settings.name="sRGB"
    return result
stone_tex=darken_scan("stone_albedo_2k.jpg","arcanista_dark_slate_albedo_2k",(.24,.31,.39))
rough_tex=image("stone_rough_2k.jpg",False)
normal_tex=image("stone_normal_2k.png",False)
wood_tex=image("wood_albedo_2k.jpg")
wood_rough=image("wood_rough_2k.jpg",False)
wood_normal=image("wood_normal_2k.png",False)

def pbr(name,alb,rgh,nrm,tint,normal_strength=1.0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    nt=m.node_tree;bs=nt.nodes.get("Principled BSDF")
    al=nt.nodes.new("ShaderNodeTexImage");al.image=alb
    mix=nt.nodes.new("ShaderNodeMixRGB");mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1.0
    mix.inputs[2].default_value=(tint[0],tint[1],tint[2],1)
    nt.links.new(al.outputs["Color"],mix.inputs[1]);nt.links.new(mix.outputs[0],bs.inputs["Base Color"])
    rn=nt.nodes.new("ShaderNodeTexImage");rn.image=rgh
    nt.links.new(rn.outputs["Color"],bs.inputs["Roughness"])
    nn=nt.nodes.new("ShaderNodeTexImage");nn.image=nrm
    nm=nt.nodes.new("ShaderNodeNormalMap");nm.inputs["Strength"].default_value=normal_strength
    nt.links.new(nn.outputs["Color"],nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"],bs.inputs["Normal"])
    return m

if KIND=="herrero":
    rocks=[
        pbr("Quarry basalt / dark warm PBR",stone_tex,rough_tex,normal_tex,(.42,.37,.34),1.1),
        pbr("Basalt - mineral warm variance",stone_tex,rough_tex,normal_tex,(.49,.41,.35),1.1),
        pbr("Soot deposits - char and oxide",stone_tex,rough_tex,normal_tex,(.30,.31,.30),1.1),
    ]
    timber=pbr("Oak / fire seasoned PBR",wood_tex,wood_rough,wood_normal,(.46,.36,.29),1.05)
else:
    rocks=[
        pbr("Metamorphic slate / charcoal-blue PBR",stone_tex,rough_tex,normal_tex,(.30,.37,.43),1.15),
        pbr("Slate / subtle iron blue inclusions",stone_tex,rough_tex,normal_tex,(.38,.45,.49),1.15),
        pbr("Slate / deep fracture",stone_tex,rough_tex,normal_tex,(.21,.27,.32),1.15)
    ]
    timber=pbr("Weathered hidden structural wood PBR",wood_tex,wood_rough,wood_normal,(.30,.31,.30))
iron=bpy.data.materials.new("Oxidized forged iron");iron.use_nodes=True
ib=iron.node_tree.nodes.get("Principled BSDF")
ib.inputs["Base Color"].default_value=(.085,.076,.071,1)
ib.inputs["Metallic"].default_value=.72
ib.inputs["Roughness"].default_value=.68
mortar=bpy.data.materials.new("Recessed stone mortar / dark");mortar.use_nodes=True
mb=mortar.node_tree.nodes.get("Principled BSDF")
mb.inputs["Base Color"].default_value=(.056,.057,.062,1) if KIND=="arcanista" else (.11,.097,.088,1)
mb.inputs["Roughness"].default_value=.93

def cube(name,loc,dims,material,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    ob=bpy.context.object;ob.name=PREFIX+name;ob.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(material)
    if bevel>0:
        mod=ob.modifiers.new("worn corners","BEVEL");mod.width=bevel;mod.segments=2
        ob.modifiers.new("weighted normals","WEIGHTED_NORMAL")
    return ob

def sculpt_block(name,x0,x1,z0,z1,kind=0,depth=None,dist=.030):
    # Eight rounded, individually displaced perimeter points and an uneven face.
    # Unlike the rejected V003 Voronoi tests, blocks follow masonry courses or
    # long geological strata. No hexagonal tessellation or procedural honeycomb.
    wid=x1-x0;hei=z1-z0
    if wid<.065 or hei<.055:return None
    cx=(x0+x1)*.5;cz=(z0+z1)*.5
    spread=min(dist,wid*.055,hei*.055)
    px=[(x0,z0),(cx,z0),(x1,z0),(x1,cz),(x1,z1),(cx,z1),(x0,z1),(x0,cz)]
    ring=[]
    for k,(x,z) in enumerate(px):
        fx=(rng.random()-.5)*spread
        fz=(rng.random()-.5)*spread
        ring.append((x+fx,z+fz))
    front=depth if depth is not None else -.25-rng.uniform(.018,.09)
    verts=[(cx,front-rng.uniform(.008,.04),cz)]
    for x,z in ring:verts.append((x,front+rng.uniform(-.018,.022),z))
    for x,z in ring:verts.append((x,-.085+rng.uniform(-.015,.015),z))
    faces=[(0,1+i,1+((i+1)%8)) for i in range(8)]
    faces.extend([(1+i,9+i,9+((i+1)%8),1+((i+1)%8)) for i in range(8)])
    faces.append(tuple(range(16,8,-1)))
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(PREFIX+name,me);bpy.context.collection.objects.link(ob)
    ob.data.materials.append(rocks[kind%len(rocks)])
    uv=me.uv_layers.new(name="UVMap")
    for pol in me.polygons:
        for li in pol.loop_indices:
            p=me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv=((p.x+W/2)/2.2,p.z/2.15)
    for pol in me.polygons:pol.use_smooth=False
    return ob

# Dark structural core; no blank bright sides or glaring top slab.
for name,x0,x1,z0,z1 in [
    ("left",-W/2,-DW/2,0,H),("right",DW/2,W/2,0,H),
    ("head",-DW/2,DW/2,DH,H)
]:
    cube("Structural_"+name,((x0+x1)/2,.06,(z0+z1)/2),(x1-x0,T,z1-z0),mortar,.009)

def courses(zone,x0,x1,z0,z1):
    z=z0;row=0
    while z < z1-.055:
        h=min(rng.uniform(.32,.59) if KIND=="herrero" else rng.uniform(.69,1.15),z1-z)
        if z1-z-h<.12:h=z1-z
        x=x0;col=0
        while x<x1-.05:
            w=min(rng.uniform(.57,1.36) if KIND=="herrero" else rng.uniform(.86,1.72),x1-x)
            if x1-x-w<.21:w=x1-x
            inset=.022 if KIND=="herrero" else .016
            shade=rng.choices([0,1,2],weights=[7,2,1])[0]
            sculpt_block(zone+"_"+str(row)+"_"+str(col),x+inset/2,x+w-inset/2,
                         z+inset/2,z+h-inset/2,shade,dist=.044 if KIND=="herrero" else .085)
            x+=w;col+=1
        z+=h;row+=1
# The magical facade is a continuous fractured shale mass, not rows of
# rectangular blocks. A compact physically displaced mesh gives large forms.
def geological_panel(label,x0,x1,z0,z1):
    nx=max(6,int((x1-x0)/.15));nz=max(5,int((z1-z0)/.16))
    verts=[];uvs=[];faces=[]
    for iz in range(nz+1):
        z=z0+(z1-z0)*iz/nz
        for ix in range(nx+1):
            x=x0+(x1-x0)*ix/nx
            # Slow, layered geological deformation with micro-fissure relief.
            yy=-.276-.025*sin(2.3*x+1.6*z)*sin(1.3*z-.9*x)
            yy-=.015*sin(13.1*x+4.1*z)*sin(8.7*z+1.2*x)
            verts.append((x,yy,z))
            uvs.append(((x+W/2)/2.2,z/2.15))
    for iz in range(nz):
        for ix in range(nx):
            a=iz*(nx+1)+ix
            faces.append((a,a+1,a+nx+2,a+nx+1))
    me=bpy.data.meshes.new(label);me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(PREFIX+label,me);bpy.context.collection.objects.link(ob)
    ob.data.materials.append(rocks[0])
    uv=me.uv_layers.new(name="UVMap")
    for pol in me.polygons:
        for li in pol.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
        pol.use_smooth=True
    return ob
geological_panel("ContinuousSlabLeft",-W/2,-DW/2,0,H)
geological_panel("ContinuousSlabRight",DW/2,W/2,0,H)
geological_panel("ContinuousSlabAboveDoor",-DW/2,DW/2,DH,H)

def bolt(name,xyz):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.036,location=xyz)
    ob=bpy.context.object;ob.name=PREFIX+name;ob.data.materials.append(iron)
def stone_cap(name,loc,dims):
    o=cube(name,loc,dims,rocks[rng.choice([0,1])],.023)
    o.rotation_euler[1]=rng.uniform(-.016,.016)
    return o

if KIND=="herrero":
    # Articulated wall: chunky quarried foundation, smoke-worn heavy oak,
    # forging hardware. Flat decorative blocks are expressly avoided.
    for side in (-1,1):
        # Edge buttress; stone plinths in staggered stacked sections.
        for i,(z,h) in enumerate([(.28,.54),(.95,.76),(1.83,.82),(2.73,.90)]):
            stone_cap("CornerButtress_%s_%s"%(side,i),(side*(W/2-.14),-.36,z),
                      (.48,.31,h))
        # Door piers exactly OUTSIDE the unchanged DW x DH cutout.
        for i,(z,h) in enumerate([(.26,.51),(.80,.54),(1.40,.65),(2.09,.71)]):
            stone_cap("DoorPier_%s_%s"%(side,i),
                      (side*(DW/2+.16),-.39,z),(.285,.33,h))
        o=cube("OakOuterPost_"+str(side),(side*(W/2-.39),-.39,1.57),(.18,.29,2.94),timber,.016)
        o=cube("IronStrapUpper_"+str(side),(side*(W/2-.39),-.545,2.49),(.27,.06,.20),iron,.008)
        bolt("CornerStrapRivet_"+str(side),(side*(W/2-.39),-.587,2.49))
        o=cube("CornerIronBrace_"+str(side),(side*(W/2-.39),-.55,.52),(.25,.055,.25),iron,.008)
        bolt("LowerRivet_"+str(side),(side*(W/2-.39),-.585,.52))
    # The cap and lintel now have a substantial actual quarry-stone silhouette.
    stone_cap("WeightBearingLintel",(0,-.37,DH+.155),(DW+.74,.44,.29))
    for side in (-1,1):
        stone_cap("LintelSaddle_"+str(side),(side*(DW/2+.37),-.36,DH+.145),(.34,.39,.34))
    oakbeam=cube("TimberTopBrace",(0,-.41,H-.17),(W-.8,.27,.19),timber,.011)
    for side in (-1,1):
        cube("HammeredTopIron_"+str(side),(side*2.5,-.57,H-.17),(.27,.064,.27),iron,.011)
        bolt("TopBolt_"+str(side),(side*2.5,-.611,H-.17))
    # Foundation volumes and stratified stress fractures are physically raised.
    for i in range(19):
        x=-W/2+(i+.5)*W/19
        if abs(x)<DW/2+.28:continue
        stone_cap("Foundation_"+str(i),(x,-.32,.115),(rng.uniform(.28,.47),.29,rng.uniform(.14,.23)))
else:
    # Twin MONOLITHIC tapered piers carved along the accepted V011 doorway:
    # door opening remains full clear width and height.
    for side in (-1,1):
        p=sculpt_block("CutBasaltJamb_"+str(side),
           side*(DW/2+.065) if side==1 else -(DW/2+.48),
           side*(DW/2+.48) if side==1 else -(DW/2+.065),
           .02,DH+.05,kind=0,depth=-.44,dist=.063)
        # Sculpted corner buttress columns, no stacked cube pattern.
        p=sculpt_block("EdgeMonolith_"+str(side),
           W/2-.48 if side==1 else -W/2+.02,
           W/2-.02 if side==1 else -W/2+.48,
           0,H,kind=1,depth=-.38,dist=.095)
    # Connected curved stone lintel, not individual gaps around a doorway.
    # The lower edge remains above the rectangular V011 collision envelope.
    n=28;verts=[];uvs=[]
    for back,yy in ((False,-.49),(True,-.08)):
        for row in (0,1):
            for i in range(n+1):
                t=i/n
                x=-1.26+2.52*t
                inner=DH+.04+.18*sin(pi*t)
                outer=DH+.44+.30*sin(pi*t)
                z=inner if row==0 else outer
                z+=rng.uniform(-.009,.009)
                yy2=yy+(rng.uniform(-.012,.012) if not back else 0)
                verts.append((x,yy2,z))
                uvs.append(((x+W/2)/2.2,z/2.15))
    faces=[]
    # front curved band; its material and grain continue the rock walls.
    for i in range(n):faces.append((i,i+1,(n+1)+i+1,(n+1)+i))
    offset=2*(n+1)
    for i in range(n):faces.append((offset+(n+1)+i,offset+(n+1)+i+1,offset+i+1,offset+i))
    # Close ribbon edges for a genuine solid cross section.
    for row in (0,1):
        p=row*(n+1);q=offset+p
        for i in range(n):
            if row==0:faces.append((p+i,q+i,q+i+1,p+i+1))
            else:faces.append((p+i+1,q+i+1,q+i,p+i))
    faces.append((0,n+1,offset+n+1,offset))
    faces.append((n,offset+n,offset+2*n+1,2*n+1))
    me=bpy.data.meshes.new("ConnectedStonePortal");me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(PREFIX+"ConnectedStonePortal",me)
    bpy.context.collection.objects.link(ob);me.materials.append(rocks[1])
    uv=me.uv_layers.new(name="UVMap")
    for pol in me.polygons:
        for li in pol.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
    # Recessed mineral micro-cracks; no fluorescent cyan tubes on the facade.
    fissure=bpy.data.materials.new("Recessed blue-grey mineral seams")
    fissure.use_nodes=True
    nb=fissure.node_tree.nodes.get("Principled BSDF")
    nb.inputs["Base Color"].default_value=(.027,.051,.063,1)
    nb.inputs["Roughness"].default_value=.98
    nb.inputs["Emission Color"].default_value=(.006,.018,.028,1)
    nb.inputs["Emission Strength"].default_value=.11
    def hairline(label,points):
        cu=bpy.data.curves.new(label,"CURVE")
        cu.dimensions="3D";cu.bevel_depth=.0028;cu.bevel_resolution=1
        spl=cu.splines.new("POLY");spl.points.add(len(points)-1)
        for p,xyz in zip(spl.points,points):p.co=(xyz[0],xyz[1],xyz[2],1)
        ob=bpy.data.objects.new(PREFIX+label,cu)
        bpy.context.collection.objects.link(ob);ob.data.materials.append(fissure)
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True);bpy.context.view_layer.objects.active=ob
        bpy.ops.object.convert(target="MESH")
        bpy.ops.object.select_all(action="DESELECT")
    for side in (-1,1):
        # Follow corner geological seams, sitting just above (in front of)
        # the displaced face. Sparse enough for a readable PBR surface.
        x=side*1.24
        hairline("MineralSeam_"+str(side),
          [(x,-.30,.35),(x+side*.05,-.312,.62),
           (x-side*.02,-.31,.90),(x+side*.07,-.31,1.20)])
    # A tapered, irregular silhouette conceals the square structural core.
    for i in range(9):
        x=-W/2+(i+.5)*W/9
        if abs(x)<1.2:continue
        b=sculpt_block("ShaleRoofCoping_"+str(i),
              x-.42,x+.42,H-.115,H+.035,1,depth=-.32,dist=.05)

# Review scene is excluded from the GLB.
ground=cube("REVIEW_TEMP",(0,0,-.085),(11,8,.07),mortar)
ground.name="REVIEW_Ground"
world=bpy.context.scene.world;world.color=(.19,.21,.25)
def light(n,loc,power,size):
    dat=bpy.data.lights.new(n,"AREA");dat.energy=power;dat.shape='DISK';dat.size=size
    ob=bpy.data.objects.new(n,dat);bpy.context.collection.objects.link(ob)
    ob.location=loc;ob.rotation_euler=(Vector((0,0,1.4))-ob.location).to_track_quat("-Z","Y").to_euler()
light("REVIEW_Key",(-4,-6,7),1250,5)
light("REVIEW_Fill",(6,-3,4),720,6)
light("REVIEW_Rim",(0,3,5),1000,4)
bpy.ops.object.camera_add(location=(9,-13,6))
cam=bpy.context.object;cam.name="REVIEW_Camera";cam.data.type='ORTHO'
sc=bpy.context.scene;sc.camera=cam
sc.render.engine='CYCLES';sc.cycles.samples=40
bpy.context.view_layer.cycles.use_denoising=True
sc.render.resolution_x=1400;sc.render.resolution_y=900;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'
sc.view_settings.view_transform='AgX'
sc.render.film_transparent=False

# Convert ALL curves prior to selection and export? Filaments were converted.
objects=[ob for ob in sc.objects if ob.name.startswith(PREFIX) and ob.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for ob in objects:ob.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
basename="genesis_wall_"+KIND+"_"+VERSION
bpy.ops.export_scene.gltf(filepath=str(ROOT/(basename+".glb")),export_format='GLB',
                           use_selection=True,export_texcoords=True,export_normals=True)
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/(basename+".blend")))

def camera(position,target,scale):
    cam.location=position
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.ortho_scale=scale
shots=[
 ("front",(0,-15,4),(0,0,1.57),9.0),
 ("three_quarter",(9,-13,6.1),(0,0,1.55),9.8),
 ("side",(11,-5,5.5),(0,0,1.55),9.3),
 ("detail",(-1.7,-3.8,3.15),(-1,0,2.05),4.4)]
for label,p,t,s in shots:
    camera(p,t,s);sc.render.filepath=str(ROOT/(label+".png"));bpy.ops.render.render(write_still=True)
audit=dict(asset=basename,status="EXPERIMENTAL_NOT_APPROVED",profession=KIND,
           width_m=W,height_m=H,door_cutout_m=[DW,DH],
           current_door_geometry="V011 not modified",
           geometry="Irregular hewn masonry" if KIND=="herrero" else "Metamorphic slate slabs with carved arch",
           textures="PolyHaven scanned PBR 2K CC0, base/normal/rough",
           visual_review="PENDING",texture_resolution=2048,
           mesh_count=len(objects),triangles=sum(len(p.vertices)-2 for ob in objects for p in ob.data.polygons),
           glb_bytes=(ROOT/(basename+".glb")).stat().st_size,
           previews=[q[0] for q in shots],seed=SEED)
(ROOT/"AUDIT.json").write_text(json.dumps(audit,indent=2))
print("GENESIS_WALL_COMPLETE",json.dumps(audit))
