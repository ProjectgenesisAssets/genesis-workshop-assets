# -*- coding: utf-8 -*-
"""Project Genesis / forge rock reference V001.
Independent experimental reconstruction from Gabriel's wireframe screenshot.
Official Blender 4.5.13 LTS on GitHub Actions only; not the original commercial mesh.
Never replaces forge V009/V027, approved door/anvil or the in-game assets.
"""
import bpy
import math
import os
import json
import random
from pathlib import Path
from mathutils import Vector
import numpy as np

SEED = 28102026
random.seed(SEED)
ROOT = Path(os.environ.get("GITHUB_WORKSPACE", os.getcwd()))
OUT = ROOT / "output_forge_rock_reference_v001"
TEX = OUT / "textures"
TEX.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
GEOMETRY = []
MATERIALS = {}
R = random.Random(SEED)

def material(name, rgb, rough=0.85, metallic=0.0, size=512, grain=0.055, glow=0.0):
    """Quiet, non-repeating low-frequency photographic-style first pass; GLB-ready UV albedo."""
    rng = np.random.default_rng(SEED + len(MATERIALS) * 41)
    noise = rng.standard_normal((32,32)).astype(np.float32)
    yy,xx = np.mgrid[:size,:size]
    fx = xx.astype(np.float32) / (size-1) * 30.0
    fy = yy.astype(np.float32) / (size-1) * 30.0
    ix = np.floor(fx).astype(np.int32)
    iy = np.floor(fy).astype(np.int32)
    sx = fx-ix
    sy = fy-iy
    sx = sx*sx*(3-2*sx)
    sy = sy*sy*(3-2*sy)
    smooth = (noise[iy,ix]*(1-sx)*(1-sy) +
              noise[iy,ix+1]*sx*(1-sy) +
              noise[iy+1,ix]*(1-sx)*sy +
              noise[iy+1,ix+1]*sx*sy)
    # Avoid scratchy noise; large tonal fields, detail from normal geometry.
    shade = np.clip(1.0 + grain*smooth, 0.76, 1.22)
    arr = np.zeros((size,size,4), dtype=np.float32)
    for channel in range(3):
        arr[:,:,channel] = np.clip(rgb[channel]*shade,0,1)
    arr[:,:,3] = 1
    img = bpy.data.images.new(name+"_albedo", width=size, height=size, alpha=True)
    img.pixels.foreach_set(arr.ravel())
    img.filepath_raw = str(TEX/(name+"_albedo.png"))
    img.file_format = "PNG"
    img.save()
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Roughness"].default_value = rough
    bs.inputs["Metallic"].default_value = metallic
    node = m.node_tree.nodes.new("ShaderNodeTexImage")
    node.image = img
    m.node_tree.links.new(node.outputs["Color"],bs.inputs["Base Color"])
    if glow:
        bs.inputs["Emission Color"].default_value = (*rgb,1)
        bs.inputs["Emission Strength"].default_value = glow
    MATERIALS[name] = m
    return m

stone = [
    material("rock_gray_cold",(0.285,0.275,0.255),grain=0.042),
    material("rock_gray_neutral",(0.345,0.327,0.300),grain=0.047),
    material("rock_ash_brown",(0.310,0.285,0.258),grain=0.049),
]
soot = material("rock_heat_soot",(0.115,0.105,0.093),grain=0.032)
fireclay = material("inner_fireclay_dark",(0.165,0.118,0.089),grain=0.034)
wood = material("weathered_oak",(0.31,0.175,0.091),rough=.77,grain=0.09)
leather = material("old_oiled_leather",(0.205,0.095,0.055),rough=.68,grain=0.07)
iron = material("worn_iron",(0.115,0.112,0.110),rough=.57,metallic=.76,grain=.04)
sack = material("coal_sack_burlap",(0.33,0.244,0.15),rough=.92,grain=.06)
coal = material("charcoal_black",(0.065,0.059,0.053),rough=.93,grain=.045)
ember = material("ember_heat",(0.90,0.105,0.014),rough=.83,grain=.03,glow=5.8)
embersoft = material("ember_darkred",(0.31,0.026,0.008),rough=.9,grain=.02,glow=2.4)

def register(obj, name, mat):
    obj.name = name
    obj.data.materials.append(mat)
    GEOMETRY.append(obj)
    return obj

def cube(name, center, dims, mat, bevel=0.0, jitter=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center)
    ob = bpy.context.object
    ob.scale = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if jitter:
        rr = random.Random(SEED+sum((i+1)*ord(c) for i,c in enumerate(name)))
        for v in ob.data.vertices:
            v.co.x += rr.uniform(-jitter,jitter)
            v.co.y += rr.uniform(-jitter,jitter)
            v.co.z += rr.uniform(-jitter,jitter)
    if bevel:
        mod = ob.modifiers.new("Large worn stone corners","BEVEL")
        mod.width = bevel
        mod.segments = 3
        ob.modifiers.new("Weighted face normals","WEIGHTED_NORMAL")
    return register(ob,name,mat)

def rod(name,a,b,radius,mat,verts=12):
    a,b = Vector(a),Vector(b)
    delta=b-a
    mid=(a+b)*.5
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius,
        depth=delta.length, location=mid)
    ob=bpy.context.object
    ob.rotation_euler=delta.to_track_quat('Z','Y').to_euler()
    return register(ob,name,mat)

def rough_stone(name,position,dims,mat=None,seed=0):
    """Large weather-rounded rock mass; vertices rather than diffuse-noise do the work."""
    rr=random.Random(SEED+seed)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=position)
    ob=bpy.context.object
    for v in ob.data.vertices:
        x,y,z=v.co
        variation=1+rr.uniform(-.067,.067)
        v.co=(x*dims[0]*variation, y*dims[1]*variation,z*dims[2]*variation)
    for p in ob.data.polygons: p.use_smooth=True
    return register(ob,name,mat or rr.choice(stone))

def wedge_arch(name,a0,a1,rin,rout,y0,y1,cz,mat):
    """A true keystone ring section, with a deep masonry smoke arch."""
    vertices=[]
    for y in (y0,y1):
        for theta,r in ((a0,rin),(a1,rin),(a1,rout),(a0,rout)):
            vertices.append((math.cos(theta)*r,y,cz+math.sin(theta)*r))
    faces=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),
           (2,6,7,3),(3,7,4,0)]
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    ob=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(ob)
    bevel=ob.modifiers.new("Hand softened arch corners","BEVEL")
    bevel.width=.038
    bevel.segments=3
    ob.modifiers.new("Weighted arch normals","WEIGHTED_NORMAL")
    return register(ob,name,mat)

def cylinder(name,loc,radius,depth,mat,vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc)
    return register(bpy.context.object,name,mat)

# Stone forge dimensions: broad firebox, tall arched opening, 2.25 m overall height.
# The reference photo is NOT a captured 3D mesh; preserve its functional silhouette.
cube("grounded dark firebox interior",(0,.24,1.145),(1.89,.65,1.14),soot,.075)
cube("interior sloping firebed",(0,-.34,.79),(1.85,1.15,.22),fireclay,.065)
cube("furnace continuous heatproof plinth",(0,0,.35),(2.53,1.60,.54),stone[1],.19,.038)
# Broad irregular masses, not repetitively stacked rectangular brick courses.
for i,(x,z,dx,dz) in enumerate([
    (-1.11,.45,.37,.44),(-.77,.27,.51,.37),(-.24,.35,.61,.39),
    (.40,.32,.60,.41),(1.00,.38,.42,.49),(-1.15,1.04,.35,.55),
    (1.15,1.04,.36,.55),(-1.18,1.47,.33,.40),(1.19,1.47,.33,.40)]):
    rough_stone("front integral rock %02d"%i,(x,-.81,z),(dx,.24,dz),
                stone[i%3],i+40)
for side in (-1,1):
    for i,(y,z) in enumerate([(-.49,.42),(.19,.42),(.66,.48),
                               (-.48,1.05),(.18,1.17),(.67,1.19),
                               (-.33,1.72),(.38,1.72)]):
        rough_stone("load wall %s-%02d"%(side,i),(side*1.13,y,z),
                    (.37,.39,.38),soot if i==6 else stone[(i+1)%3],i+200*(side+2))
# Lower face of arch at z 1.02; upper part reaches 2.04.
cz=1.04
segments=10
for i in range(segments):
    t0=math.pi*i/segments
    t1=math.pi*(i+1)/segments
    wedge_arch("large firebox keystone %02d"%i,t0,t1,.82,1.13,
               -.92,-.49,cz,soot if 2<i<8 else stone[i%3])
for i,(x,y,z,dx,dy,dz) in enumerate([
    (-.91,.14,1.86,.36,.46,.28),(-.44,.18,2.06,.39,.44,.26),
    (.09,.19,2.15,.39,.44,.29),(.55,.19,2.06,.40,.44,.30),
    (.96,.12,1.85,.35,.45,.30)]):
    rough_stone("upper furnace integrated shoulder %02d"%i,(x,y,z),
                (dx,dy,dz),soot if i==2 else stone[i%3],450+i)
# Chimney: a hollow-looking broad rough stone crown, absolutely no metal exhaust hood.
for j in range(2):
    z=2.31+j*.27
    for i in range(7):
        theta=2*math.pi*i/7 + j*.16
        x=.31*math.cos(theta); y=.28+.29*math.sin(theta)
        rough_stone("smoke stack rock %02d %02d"%(j,i),(x,y,z),
                  (.18,.17,.18),soot if i in (0,1,2,5) else stone[(i+j)%3],650+j*20+i)
cylinder("hollow flue dark recess",(.0,.28,2.55),.19,.035,soot,20)

# At least a few real ember fissures and many subdued black coals.
for i in range(42):
    x=R.uniform(-.74,.74); y=R.uniform(-.73,.14)
    z=.92+R.uniform(-.035,.07)
    s=R.uniform(.055,.13)
    rough_stone("hearth charcoal %02d"%i,(x,y,z),(s,s*.8,s*.7),
                ember if i%7==0 else (embersoft if i%9==0 else coal),950+i)
for i in range(7):
    x=-.56+i*.18
    rough_stone("embers seen between coals %02d"%i,(x,-.49,.885),
                (.07,.05,.025),ember,1080+i)

# Mechanically coherent long wooden wedge bellows; independent reusable sub-assembly.
# Pointed air nozzle faces firebox on left; full hide expands to right.
def bellows_profile(x):
    u=max(0,min(1,(x-1.24)/2.42))
    width=.105+.62*u**.78
    floor=.71
    top=1.02+.56*u
    return width,floor,top
def plank(name,which,mat):
    verts=[]
    for x in (1.22,3.67):
        w,lo,hi=bellows_profile(x)
        z=hi if which=="top" else lo
        verts.extend([(x,-w,z),(x,w,z)])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],[(0,1,3,2)]);mesh.update()
    ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
    solid=ob.modifiers.new("Real wood panel thickness","SOLIDIFY")
    solid.thickness=.065
    bevel=ob.modifiers.new("Hand planed board corners","BEVEL")
    bevel.width=.022;bevel.segments=2
    return register(ob,name,mat)
plank("bellows upper wooden leaf","top",wood)
plank("bellows lower wooden leaf","bottom",wood)
for side in (-1,1):
    verts=[]; faces=[]
    NX,NZ=28,10
    for i in range(NX+1):
        x=1.25+2.38*i/NX
        w,lo,hi=bellows_profile(x)
        for j in range(NZ+1):
            t=j/NZ
            # Radial leather pleats converge naturally toward pointed nozzle.
            amplitude=.055*(.14+.86*(i/NX)**.68)
            fan=math.sin(math.pi*6.4*t+(.4*i/NX))
            yy=side*w*(1+amplitude*fan)
            zz=lo+(hi-lo)*t
            verts.append((x,yy,zz))
    for i in range(NX):
        for j in range(NZ):
            a=i*(NZ+1)+j
            faces.append((a,a+NZ+1,a+NZ+2,a+1))
    mesh=bpy.data.meshes.new("bellows leather folds")
    mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new("bellows tailored radial leather %s"%side,mesh)
    bpy.context.collection.objects.link(ob)
    thick=ob.modifiers.new("Hide thickness","SOLIDIFY")
    thick.thickness=.009
    for p in mesh.polygons:p.use_smooth=True
    register(ob,ob.name,leather)
# Bellows bracing, nozzle, hinge, rear staff and handle.
rod("bellows wrought iron nozzle",(1.08,0,1.0),(1.33,0,1.01),.048,iron)
for x in (1.34,3.30):
    rod("bellows structural left staff %.2f"%x,(x,-.66,.54),(x,-.66,1.90),.058,wood)
    rod("bellows structural right staff %.2f"%x,(x,.66,.54),(x,.66,1.90),.058,wood)
rod("bellows horizontal lower beam",(1.29,-.68,.65),(3.87,-.68,.65),.060,wood)
rod("bellows long wooden hand lever",(.91,-.01,2.10),(4.85,-.01,2.10),.045,wood)
rod("bellows pivot crossbar",(3.25,-.68,2.08),(3.25,.68,2.08),.064,wood)
rod("bellows rear pull cord",(4.65,-.02,2.10),(3.83,-.04,.88),.014,sack)

# Supporting props from original screenshot, kept visually secondary.
def barrel(name,x,y,z,height,radius):
    cylinder(name+" oak body",(x,y,z+height/2),radius,height,wood,16)
    for h in (z+.11,z+height-.10):
        cylinder(name+" wrought band %.2f"%h,(x,y,h),radius*1.03,.035,iron,16)
barrel("left blacksmith tool bucket",-1.70,-1.10,0,.68,.27)
barrel("small bellows tub",1.66,-1.14,0,.34,.21)
for i in range(3):
    a=(-1.7+R.uniform(-.15,.15),-1.11+R.uniform(-.13,.13),.42)
    b=(a[0]+R.uniform(-.25,.20),a[1],1.40+R.uniform(-.1,.2))
    rod("loose iron tool %d"%i,a,b,.019,iron,8)
# Coal sack is a loose rounded burlap volume.
rough_stone("rough cloth coal sack",(-1.03,-1.19,.26),(.41,.33,.31),sack,1800)
for i in range(14):
    rough_stone("black coal sack filling %02d"%i,
          (-1.03+R.uniform(-.25,.25),-1.22+R.uniform(-.20,.20),.50+R.uniform(-.02,.08)),
          (.065,.06,.05),coal,1850+i)
rod("tongs first shank",(.83,-.98,.13),(.73,-.98,1.09),.018,iron)
rod("tongs second shank",(.90,-.98,.13),(.82,-.98,1.08),.018,iron)

# World, lights and four documentary views.
world=bpy.context.scene.world
if not world: world=bpy.data.worlds.new("studio neutral")
bpy.context.scene.world=world
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.36,.37,.40,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.70
floor=material("neutral_studio_floor",(.34,.35,.365),rough=.97,grain=.005,size=128)
cube("presentation floor",(1.15,0,-.11),(10,8,.18),floor,0)
# Exclude floor from GLB export.
GEOMETRY.pop()
def point(name,loc,energy,color,radius):
    data=bpy.data.lights.new(name,"POINT");data.energy=energy;data.color=color
    data.shadow_soft_size=radius
    ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob)
point("real ember bounce",(0,-.51,1.04),180,(1,.23,.045),.45)
def area(name,loc,power,size):
    data=bpy.data.lights.new(name,"AREA");data.energy=power;data.shape="DISK";data.size=size
    ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob)
    direction=Vector((.5,0,1.1))-ob.location
    ob.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
area("large softbox",(-4,-5,6),850,5)
area("rim right",(5,3,5),600,4)
bpy.ops.object.camera_add()
camera=bpy.context.object;bpy.context.scene.camera=camera
camera.data.type='ORTHO';camera.data.ortho_scale=7.1
def take_shot(name,loc,target,ortho=None):
    camera.location=loc
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=ortho or 7.1
    bpy.context.scene.render.filepath=str(OUT/(name+".png"))
    bpy.ops.render.render(write_still=True)
scene=bpy.context.scene
scene.render.engine="CYCLES"
scene.cycles.samples=28
scene.render.resolution_x=1280
scene.render.resolution_y=850
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
scene.view_settings.view_transform="AgX"
scene.render.filepath=str(OUT/"three_quarter.png")
# Save editable Blender master (includes presentation setup).
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"forge_rock_reference_v001.blend"))
# Export scene geometry only (no studio floor, cameras or lights).
bpy.ops.object.select_all(action="DESELECT")
for obj in GEOMETRY: obj.select_set(True)
bpy.context.view_layer.objects.active=GEOMETRY[0]
bpy.ops.export_scene.gltf(filepath=str(OUT/"forge_rock_reference_v001.glb"),
    export_format='GLB',use_selection=True,export_apply=True)
bpy.ops.object.select_all(action="DESELECT")
take_shot("three_quarter",(5.4,-8.3,4.5),(.88,0,1.15))
take_shot("front",(.7,-9.0,3.0),(.7,0,1.12))
take_shot("rear",(5.2,7.8,4.0),(1.1,0,1.2))
take_shot("detail",(1.85,-5.2,3.15),(.22,-.28,1.25),4.0)
tris=sum(len(p.vertices)-2 for o in GEOMETRY if o.type=="MESH" for p in o.data.polygons)
audit={
  "asset":"forge_rock_reference","version":"V001","status":"candidate_not_artist_approved",
  "reference":"Gabriel 2026-10-27 wireframe screenshot; manually reconstructed, not exact topology",
  "masonry":"oversize worn natural rocks, integrated soot-black stone flue, no metal hood",
  "bellows":"separate hand-operated wood/leather geometry; static, animation pending",
  "meshes":len(GEOMETRY),"source_mesh_triangles_before_modifiers":tris,
  "pbr_texture_albedos":[m.name for m in MATERIALS.values()],
  "build":"Blender 4.5.13 on GitHub Actions",
  "target":"PlayCanvas WebGL vertical slice / 9 November 2026",
  "human_art_approval":False}
(OUT/"AUDIT.json").write_text(json.dumps(audit,indent=2,ensure_ascii=False))
print("GENESIS_ROCK_REFERENCE_BUILD",json.dumps(audit))
