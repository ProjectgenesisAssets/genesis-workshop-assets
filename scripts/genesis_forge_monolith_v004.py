# -*- coding: utf-8 -*-
"""Project Genesis stone-only forge V004.
A single continuous natural rock forge and hollow flue, with an excavated hearth.
NO separate bellows, bucket, tools, metal exhaust hood or tiled masonry.
Experimental, independently generated from screenshot + visual concept.
Real Blender 4.5.13 LTS via GitHub Actions; never change approved assets.
"""
import bpy, os, json, random, math
from pathlib import Path
from mathutils import Vector
import numpy as np

ROOT=Path(os.environ.get("GITHUB_WORKSPACE",os.getcwd()))
OUT=ROOT/"output_forge_monolith_v004"
TEX=OUT/"textures"
TEX.mkdir(parents=True,exist_ok=True)
rng=random.Random(2826)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
ART=[]

def smooth_noise(n,grid,seed):
    r=np.random.default_rng(seed)
    coarse=r.normal(0,1,(grid+2,grid+2)).astype(np.float32)
    q=np.linspace(0,grid,n,endpoint=False,dtype=np.float32)
    a=np.floor(q).astype(np.int32); f=q-a
    f=f*f*(3-2*f)
    x0=a[:,None];x1=(a+1)[:,None]
    y0=a[None,:];y1=(a+1)[None,:]
    fx=f[:,None];fy=f[None,:]
    return (coarse[x0,y0]*(1-fx)*(1-fy)+coarse[x1,y0]*fx*(1-fy)+
            coarse[x0,y1]*(1-fx)*fy+coarse[x1,y1]*fx*fy)

def image_tex(name,arr,noncolor=False):
    h,w,_=arr.shape
    img=bpy.data.images.new(name,width=w,height=h,alpha=True)
    img.pixels.foreach_set(arr.astype(np.float32).ravel())
    img.filepath_raw=str(TEX/(name+".png"))
    img.file_format="PNG"
    if noncolor:img.colorspace_settings.name="Non-Color"
    img.save()
    return img

def pbr_rock():
    n=1536
    macro=smooth_noise(n,7,500)
    med=smooth_noise(n,33,501)
    micro=smooth_noise(n,150,502)
    shade=np.clip(1+.115*macro+.052*med+.009*micro,.78,1.22)
    # Gray weathered rock; gentle warm mineral veins, restrained saturation.
    base=np.array((.405,.391,.360),dtype=np.float32)
    albedo=np.zeros((n,n,4),dtype=np.float32)
    for k in range(3):albedo[:,:,k]=np.clip(base[k]*shade,0,1)
    albedo[:,:,3]=1
    roughness=np.clip(.81+.045*med+.018*micro,.65,.96)
    rmap=np.zeros_like(albedo)
    rmap[:,:,:3]=roughness[:,:,None]
    rmap[:,:,3]=1
    h=.55+.08*med+.006*micro
    dy,dx=np.gradient(h)
    nx=-dx*16;ny=-dy*16;nz=np.ones_like(nx)
    norm=np.sqrt(nx*nx+ny*ny+nz*nz)
    nmap=np.zeros_like(albedo)
    nmap[:,:,0]=.5+.5*nx/norm
    nmap[:,:,1]=.5+.5*ny/norm
    nmap[:,:,2]=.5+.5*nz/norm
    nmap[:,:,3]=1
    m=bpy.data.materials.new("GENESIS_PBR_geological_dark_gray_rock")
    m.use_nodes=True
    nd=m.node_tree.nodes;links=m.node_tree.links
    bs=nd.get("Principled BSDF")
    bs.inputs["Roughness"].default_value=.83
    bs.inputs["Metallic"].default_value=0.0
    def inp(label,img):
        t=nd.new("ShaderNodeTexImage");t.label=label;t.image=img
        return t
    al=inp("Rock 1536 albedo",image_tex("rock_basecolor_1536",albedo))
    ro=inp("Rock 1536 roughness",image_tex("rock_roughness_1536",rmap,True))
    no=inp("Rock 1536 tangent normal",image_tex("rock_normal_1536",nmap,True))
    links.new(al.outputs["Color"],bs.inputs["Base Color"])
    links.new(ro.outputs["Color"],bs.inputs["Roughness"])
    normal=nd.new("ShaderNodeNormalMap")
    normal.inputs["Strength"].default_value=.10
    links.new(no.outputs["Color"],normal.inputs["Color"])
    # V003 tangent-space normals produced severe black triangular facets.
    # Keep the map for later validation; geometry carries the broad relief.
    return m

rock=pbr_rock()
def plain_mat(name,color,rough=.88,emission=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*color,1)
    bs.inputs["Roughness"].default_value=rough
    if emission:
        bs.inputs["Emission Color"].default_value=(*color,1)
        bs.inputs["Emission Strength"].default_value=emission
    return m
soot=plain_mat("heat_blackened_inner_rock",(.072,.068,.062))
coal=plain_mat("charcoal_black_rough",(.035,.032,.028))
red=plain_mat("buried_dull_red_embers",(.11,.013,.004),emission=.85)
hot=plain_mat("buried_orange_embers",(.40,.043,.004),emission=1.35)
ground=plain_mat("neutral_reference_gray",(.20,.21,.22))

PARTS=[]
def part(obj):
    PARTS.append(obj);return obj
def block(loc,dim):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    ob=bpy.context.object
    ob.scale=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bevel=ob.modifiers.new("soft primitive prior to geological union","BEVEL")
    bevel.width=.16;bevel.segments=4
    bpy.context.view_layer.objects.active=ob
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return part(ob)
def ellipsoid(loc,size,seed):
    rr=random.Random(300+seed)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=loc)
    ob=bpy.context.object
    for v in ob.data.vertices:
        v.co.x*=size[0]*(1+rr.uniform(-.12,.12))
        v.co.y*=size[1]*(1+rr.uniform(-.10,.10))
        v.co.z*=size[2]*(1+rr.uniform(-.12,.12))
    return part(ob)
def arch_band():
    """One continuous load-bearing natural rock vault, not individual arch bricks."""
    verts=[];n=32
    rinner=.81;router=1.22;cz=1.02
    for y in (-.78,.46):
        for i in range(n+1):
            a=i*math.pi/n
            for rr in (rinner,router):
                verts.append((rr*math.cos(a),y,cz+rr*math.sin(a)))
    faces=[]
    stride=(n+1)*2
    for side in (0,1):
        off=side*stride
        for i in range(n):
            a=off+i*2
            faces.append((a,a+2,a+3,a+1))
    for i in range(n):
        a=i*2;b=stride+a
        faces.extend(((a,b,b+2,a+2),(a+1,a+3,b+3,b+1)))
    faces.extend(((0,1,stride+1,stride),((n*2),(stride+n*2),(stride+n*2+1),(n*2+1))))
    mesh=bpy.data.meshes.new("continuous_rock_hearth_arch")
    mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new("continuous_rock_hearth_arch",mesh)
    bpy.context.collection.objects.link(obj)
    return part(obj)
def flue_ring():
    """Tapered *hollow* natural rock flue, integral with vaulted stone cap."""
    verts=[]
    n=24
    for z,outer,inner in ((2.12,.45,.22),(2.42,.40,.20),(2.70,.36,.19)):
        for radius in (outer,inner):
            for k in range(n):
                a=2*math.pi*k/n
                irregular=1+.06*math.sin(3*a+z*4)+.025*math.cos(7*a+z*3)
                verts.append((radius*irregular*math.cos(a),
                              .23+radius*irregular*math.sin(a),z))
    faces=[]
    st=2*n
    for j in range(2):
        for side in range(2):
            base=j*st+side*n
            for i in range(n):
                a=base+i;b=base+(i+1)%n
                faces.append((a,b,b+st,a+st))
    for i in range(n):
        a=2*st+i;b=2*st+(i+1)%n
        faces.append((a,b,2*st+n+(i+1)%n,2*st+n+i))
    mesh=bpy.data.meshes.new("integrated_chimney")
    mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new("integrated_chimney",mesh)
    bpy.context.collection.objects.link(obj)
    return part(obj)

# Main stone furnace: silhouette is broadly square and heavy, with a carved frontal cavity.
block((-1.08,.04,.76),(.60,1.54,1.53))
block((1.08,.04,.76),(.60,1.54,1.53))
block((0,.16,.36),(2.45,1.56,.70))
block((0,.30,1.94),(1.97,1.16,.48))
arch_band()
# Rear and side shoulders support the hollow flue.
for i,(x,y,z,sx,sy,sz) in enumerate([
    (-1.01,.38,1.69,.40,.62,.51),(1.01,.38,1.69,.43,.62,.49),
    (-.66,.35,2.00,.48,.45,.29),(.63,.31,2.04,.50,.44,.29),
    (0,.36,2.18,.67,.54,.29),(-.88,.76,.95,.39,.39,.71),
    (.86,.75,1.03,.40,.41,.72),
]):
    ellipsoid((x,y,z),(sx,sy,sz),i)
flue_ring()
# Geological union: all stone components become ONE sculpted mesh.
bpy.ops.object.select_all(action="DESELECT")
for o in PARTS:o.select_set(True)
bpy.context.view_layer.objects.active=PARTS[0]
bpy.ops.object.join()
forge=bpy.context.object
forge.name="FORGE_SINGLE_CONTINUOUS_NATURAL_ROCK"
voxel=forge.modifiers.new("Continuous connected geology","REMESH")
voxel.mode='VOXEL';voxel.voxel_size=.043
bpy.ops.object.modifier_apply(modifier=voxel.name)
smooth=forge.modifiers.new("Subtle geological relaxation","SMOOTH")
smooth.factor=.40;smooth.iterations=2
bpy.ops.object.modifier_apply(modifier=smooth.name)
for idx,(scale,strength) in enumerate(((.64,.024),(.14,.003))):
    t=bpy.data.textures.new("rock_noise_scale_%s"%idx,type="CLOUDS")
    t.noise_scale=scale;t.noise_depth=3
    d=forge.modifiers.new("Real stone erosion %s"%idx,"DISPLACE")
    d.texture=t;d.strength=strength;d.mid_level=.50
    bpy.ops.object.modifier_apply(modifier=d.name)
tri=sum(max(0,len(p.vertices)-2) for p in forge.data.polygons)
if tri>82000:
    dec=forge.modifiers.new("WebGL budget mesh reduction","DECIMATE")
    dec.ratio=82000/tri
    bpy.ops.object.modifier_apply(modifier=dec.name)
for p in forge.data.polygons:p.use_smooth=True
forge.data.materials.append(rock)
# Real UVs for GLB PBR; these are not procedural-only viewport shaders.
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(island_margin=.006)
bpy.ops.object.mode_set(mode="OBJECT")
ART.append(forge)

def box(name,loc,dim,mat,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    obj=bpy.context.object;obj.name=name;obj.scale=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        b=obj.modifiers.new("soft corners","BEVEL");b.width=bevel;b.segments=2
    obj.data.materials.append(mat)
    ART.append(obj)
    return obj
# Recess behind the mouth and dark heat-proof floor are integral furnace details.
box("dark_recessed_hearth_back_wall",(0,.42,1.13),(1.70,.11,1.25),soot,.045)
box("stone_working_lip_integral_to_hearth",(0,-.43,.78),(1.70,1.0,.15),rock,.095)
for i in range(48):
    x=rng.uniform(-.63,.63);y=rng.uniform(-.65,.12);z=.88+rng.uniform(-.01,.07)
    r=rng.uniform(.035,.085)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(x,y,z))
    ob=bpy.context.object;ob.name="internal_charcoal_%02d"%i
    ob.scale=(r*1.2,r,r*.68)
    ob.data.materials.append(hot if i%13==0 else (red if i%7==0 else coal))
    ART.append(ob)

# Documented four-view production preview. No other loose props, bellows or chimneys.
world=bpy.data.worlds.new("Neutral photographic studio")
bpy.context.scene.world=world;world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.43,.44,.45,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.65
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.16))
floor=bpy.context.object;floor.name="studio_floor_not_in_export"
floor.scale=(9,8,.22);floor.data.materials.append(ground)
def light(name,loc,power,size):
    d=bpy.data.lights.new(name,"AREA");d.energy=power;d.size=size
    obj=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(obj)
    obj.location=loc
    obj.rotation_euler=(Vector((0,0,1.1))-obj.location).to_track_quat("-Z","Y").to_euler()
light("large front left softbox",(-3.8,-4.6,5.0),650,5)
light("front right subtle fill",(4,-4.2,4.3),390,4)
light("back edge light",(3.5,3.4,4.5),220,4)
d=bpy.data.lights.new("Live coal bounce","POINT")
d.energy=68;d.color=(1,.25,.095);d.shadow_soft_size=.45
ob=bpy.data.objects.new("Live coal bounce",d)
bpy.context.collection.objects.link(ob);ob.location=(0,-.34,1.03)
bpy.ops.object.camera_add();camera=bpy.context.object
scene=bpy.context.scene;scene.camera=camera
camera.data.type="ORTHO";camera.data.ortho_scale=4.9
scene.render.engine="CYCLES";scene.cycles.samples=36
scene.render.resolution_x=1250;scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.view_settings.view_transform="AgX"
scene.render.film_transparent=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"forge_monolith_v004.blend"))
# Portable GLB contains geometry and UV-baked PBR texture images.
bpy.ops.object.select_all(action="DESELECT")
for o in ART:o.select_set(True)
bpy.context.view_layer.objects.active=forge
bpy.ops.export_scene.gltf(filepath=str(OUT/"forge_monolith_v004.glb"),
                         export_format="GLB",use_selection=True,export_apply=True)
bpy.ops.object.select_all(action="DESELECT")
def render(name,where,target=(0,.05,1.35),scale=4.9):
    camera.location=where;camera.data.ortho_scale=scale
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat("-Z","Y").to_euler()
    scene.render.filepath=str(OUT/(name+".png"))
    bpy.ops.render.render(write_still=True)
render("three_quarter",(3.9,-6.8,3.7))
render("front",(0,-6.8,2.6))
render("rear",(-3.5,5.5,3.8))
render("detail",(2.0,-4.8,2.4),(0,-.45,1.48),3.25)
tris=sum(max(0,len(p.vertices)-2) for p in forge.data.polygons)
audit={"version":"V004","asset":"stone_forge_only","model":"one continuous natural rock outer shell",
       "bellows":False,"props":False,"brick_courses":False,"metal_flue":False,
       "forge_mesh_triangles":tris,"separate_ember_meshes":48,
       "rock_pbr_resolution":1536,"pbr_maps":["basecolor","roughness"],"normal_map":"generated but disabled after V003 tangent artifact",
       "source_reference":"wireframe screenshot, approximate proportions, NOT original mesh",
       "art_approved":False,"engine":"PlayCanvas WebGL","deadline":"2026-11-09"}
(OUT/"AUDIT.json").write_text(json.dumps(audit,indent=2))
print("GENESIS_MONOLITH_BUILD",json.dumps(audit))
