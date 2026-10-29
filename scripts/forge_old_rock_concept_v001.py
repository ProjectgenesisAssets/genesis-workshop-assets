# Project Genesis | Forge: ancient rock concept V001
# Original independent reconstruction using the approved first visual concept.
# Geometry is NOT Mike Farrant's paid/downloadable mesh and contains no Sketchfab data.
# Production: Blender 4.5.13 LTS through GitHub Actions only.
import bpy, math, random, json, os
from pathlib import Path
from mathutils import Vector, noise
import numpy as np

random.seed(840127)
OUT = Path(os.environ.get("GITHUB_WORKSPACE", os.getcwd())) / "output_forge_old_rock_v001"
TEX = OUT / "textures"
TEX.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
assets = []
maps = []

def field(n, grid, rng):
    a = rng.standard_normal((grid + 2, grid + 2)).astype(np.float32)
    k = np.linspace(0, grid, n, endpoint=False, dtype=np.float32)
    i = np.floor(k).astype(np.int32)
    f = k-i
    f = f*f*(3-2*f)
    ix = i[:,None]; iy = i[None,:]
    fx = f[:,None]; fy = f[None,:]
    return (a[ix,iy]*(1-fx)*(1-fy) +
            a[ix+1,iy]*fx*(1-fy) +
            a[ix,iy+1]*(1-fx)*fy +
            a[ix+1,iy+1]*fx*fy)

# Poly Haven "Rock Face" — real-world scanned PBR, CC0.
# https://polyhaven.com/a/rock_face
# Maps downloaded by the GitHub runner; source binaries never committed.
import urllib.request
import time
asset_id="rock_face"
maps_meta={"source":"https://polyhaven.com/a/rock_face","license":"CC0",
           "resolution":"2k","map_type":"photogrammetry_scanned"}
def fetch_scan(suffix,ext):
    name=f"{asset_id}_{suffix}_2k.{ext}"
    url=f"https://dl.polyhaven.org/file/ph-assets/Textures/{ext}/2k/{asset_id}/{name}"
    dst=TEX/name
    last_exc=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"ProjectGenesisAssetLookdev/1.0"})
            with urllib.request.urlopen(req,timeout=60) as stream:
                with dst.open("wb") as target:
                    import shutil
                    shutil.copyfileobj(stream,target)
            assert dst.stat().st_size>100000,(name,dst.stat().st_size)
            head=dst.open("rb").read(8)
            assert (head[:2]==b"\xff\xd8" if ext=="jpg" else head.startswith(b"\x89PNG")),name
            im=bpy.data.images.load(str(dst),check_existing=False)
            if suffix!="diff":im.colorspace_settings.name="Non-Color"
            im.pack();maps.append(name)
            print("PBR_SCAN_DOWNLOADED",name,dst.stat().st_size)
            return im
        except Exception as exc:
            last_exc=exc
            print("PBR_SCAN_RETRY",name,attempt,str(exc))
            time.sleep(2)
    raise RuntimeError(f"Cannot obtain validated Poly Haven CC0 map: {name}: {last_exc}")

source_diff=fetch_scan("diff","jpg")
roughimg=fetch_scan("rough","jpg")
normimg=fetch_scan("nor_gl","png")
W,H=source_diff.size
assert W>=2048 and H>=2048,(W,H)
raw=np.empty((W*H*4,),dtype=np.float32)
source_diff.pixels.foreach_get(raw)
scan=raw.reshape(H,W,4)[...,:3]
# Preserve real mineral pores/crevices; reduce warm rust hue into aged neutral stone.
luma=.24*scan[...,0]+.65*scan[...,1]+.11*scan[...,2]
muted=.62*scan+.38*luma[...,None]
stone=np.clip(muted*np.array([.86,.91,.99],dtype=np.float32),.004,1.0)
# Actual soot-stained stone retains the same scanned mineral detail.
charcoal=np.clip(stone*np.array([.19,.17,.145],dtype=np.float32)+.007,.004,1.0)
del raw,scan,muted,luma

def save_toned_scan(name,rgb):
    im=bpy.data.images.new(name,width=W,height=H,alpha=True)
    rgba=np.concatenate((rgb.astype(np.float32),np.ones((H,W,1),dtype=np.float32)),axis=2)
    im.pixels.foreach_set(rgba.ravel())
    path=TEX/(name+".png")
    im.filepath_raw=str(path)
    im.file_format="PNG"
    im.save()
    im.pack()
    maps.append(path.name)
    return im
rockimg=save_toned_scan("PolyHaven_RockFace_CC0_WeatheredNeutralRock",stone)
sootimg=save_toned_scan("PolyHaven_RockFace_CC0_FurnaceSoot",charcoal)
del stone,charcoal
def pbr(name, image, rough=.86, normal_strength=.42):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    nd=m.node_tree.nodes
    lk=m.node_tree.links
    bs=nd.get("Principled BSDF")
    bs.inputs["Metallic"].default_value=0
    bs.inputs["Roughness"].default_value=rough
    tex=nd.new("ShaderNodeTexImage");tex.image=image
    rr=nd.new("ShaderNodeTexImage");rr.image=roughimg
    nt=nd.new("ShaderNodeTexImage");nt.image=normimg
    nm=nd.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value=normal_strength
    lk.new(tex.outputs["Color"],bs.inputs["Base Color"])
    lk.new(rr.outputs["Color"],bs.inputs["Roughness"])
    lk.new(nt.outputs["Color"],nm.inputs["Color"])
    lk.new(nm.outputs["Normal"],bs.inputs["Normal"])
    return m
rock=pbr("Scanned_OldRock_PolyHaven_2K_CC0",rockimg,.84,.84)
soot=pbr("Scanned_Rock_SootInterior_PolyHaven_2K_CC0",sootimg,.92,.65)
coal=bpy.data.materials.new("Coal_Matte_Natural")
coal.diffuse_color=(.029,.028,.025,1)
coal.use_nodes=True
coal.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.025,.023,.021,1)
coal.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=.93

def active(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active=o

def apply_transform(o):
    active(o)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return o

# V004: weathered quarry-rock foundation, never a clay brick slab.
# A continuous structural core is physically sculpted before integrating
# asymmetrical natural stone outcrops. Every outcrop is merged into the forge.
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,.37))
body=bpy.context.object
body.name="GENESIS_Forge_Rock_Foundation"
body.dimensions=(2.24,1.12,.74)
apply_transform(body)
active(body)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.subdivide(number_cuts=12)
bpy.ops.object.mode_set(mode="OBJECT")
for v in body.data.vertices:
    p=v.co.copy()
    large=noise.noise(p*3.1+Vector((2.31,6.47,1.73)))
    medium=noise.noise(p*8.6+Vector((7.13,1.9,5.81)))
    little=noise.noise(p*18.2+Vector((4.3,9.21,2.18)))
    fracture_field=abs(noise.noise(p*5.1+Vector((5.47,3.11,8.14))))
    split=-.030*max(0.0,1.0-fracture_field/.14)**2
    d=.073*large+.029*medium+.008*little+split
    v.co += v.normal*d
body.data.update()
# Embedded geological growths: unequal and staggered, not stacked stone blocks.
outcrops=[
  (-.99,-.48,.21,.32,.24,.27),(-.72,-.57,.42,.30,.19,.25),
  (-.37,-.60,.17,.36,.23,.21),(.07,-.59,.36,.33,.20,.28),
  (.47,-.58,.14,.30,.24,.24),(.80,-.53,.43,.35,.22,.27),
  (1.05,-.29,.16,.22,.32,.27),(-1.07,.24,.40,.23,.31,.31),
  (1.09,.27,.48,.24,.29,.23),(-.86,.57,.18,.34,.24,.20),
  (-.28,.58,.45,.26,.19,.26),(.47,.56,.23,.36,.23,.23),
  (.91,.48,.16,.30,.23,.23),(-.98,-.43,.85,.28,.22,.28),
  (1.01,-.39,1.04,.26,.23,.31),(-.73,-.40,1.37,.27,.20,.20),
  (.76,-.38,1.30,.29,.21,.24)
]
rock_growths=[]
for i,(x,y,z,sx,sy,sz) in enumerate(outcrops):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(x,y,z))
    rg=bpy.context.object
    rg.name="Integrated_Weathered_Stone_%02d"%i
    rg.scale=(sx,sy,sz)
    rg.rotation_euler=(.17*i,.29*i,.41*i)
    apply_transform(rg)
    for v in rg.data.vertices:
        p=v.co
        fine=noise.noise(p*7.1+Vector((i*2.31,i*.91,4.16)))
        crag=noise.noise(p*3.0+Vector((i*.11,1.3,2.1)))
        v.co+=v.normal*(.024*fine+.042*crag)
    rg.data.update()
    rock_growths.append(rg)

# V003: proven watertight arch mass, roughened after voxel merge.
bpy.ops.mesh.primitive_uv_sphere_add(segments=100,ring_count=50,location=(0,.015,1.03))
hood=bpy.context.object
hood.name="Rock_Hood_Proven_Topology"
hood.scale=(1.08,.55,.81)
apply_transform(hood)

bpy.ops.mesh.primitive_cone_add(vertices=80,radius1=.325,radius2=.205,depth=.65,location=(0,.16,1.87))
chimney=bpy.context.object
chimney.name="Organic_Rock_Chimney"
apply_transform(chimney)

bpy.ops.object.select_all(action="DESELECT")
for o in [body,hood,chimney]+rock_growths: o.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.object.join()
body.name="GENESIS_Forge_MonolithicRock"
active(body)
body.data.remesh_voxel_size=.026
bpy.ops.object.voxel_remesh()

# V003 sculpt: actual decimetric rock relief, fractures and weathering.
# Large irregular forms carry the silhouette; scanned PBR handles pore detail.
for v in body.data.vertices:
    p=v.co.copy()
    macro=noise.noise(p*2.12+Vector((6.1,8.7,2.4)))
    meso=noise.noise(p*6.4+Vector((1.9,4.6,5.1)))
    micro=noise.noise(p*16.0+Vector((9.2,1.1,3.7)))
    fracture_field=abs(noise.noise(p*5.25+Vector((4.17,9.4,2.8))))
    fracture=-.024*max(0.0,1.0-fracture_field/.12)**2
    d=.053*macro+.022*meso+.004*micro+fracture
    v.co += v.normal*d
body.data.update()
print("FORGE_DEBUG_AFTER_VOXEL",len(body.data.vertices),len(body.data.polygons))
body.data.materials.append(rock)
body.data.materials.append(soot)

# Firebox arch: true hollow, arched and deep; never a solid decorative black patch.
radius=.745
cross=[(-radius,.735),(radius,.735)]
# Hand-hewn stone arch; preserve clearance and depth, avoid mathematically perfect curve.
cross.extend((radius*(1-2*j/48),.952+.552*math.sqrt(max(0,1-(1-2*j/48)**2))) for j in range(49))
num=len(cross)
verts=[(x,y,z) for y in (-.79,.29) for (x,z) in cross]
faces=[]
faces.append(tuple(range(num)))
faces.append(tuple(reversed(tuple(range(num,2*num)))))
for j in range(num):
    k=(j+1)%num
    faces.append((num+j,num+k,k,j))
me=bpy.data.meshes.new("Real_Arch_Cavity_Cutter")
me.from_pydata(verts,[],faces)
me.update()
cut=bpy.data.objects.new("ARCH_CUTTER_TEMP",me)
bpy.context.collection.objects.link(cut)
cut.data.materials.append(soot)
bpy.ops.object.select_all(action="DESELECT")
active(body)
bo=body.modifiers.new("Carved open fire chamber","BOOLEAN")
bo.operation="DIFFERENCE"
bo.solver="EXACT"
bo.object=cut
bpy.ops.object.modifier_apply(modifier=bo.name)
bpy.data.objects.remove(cut,do_unlink=True)
print("FORGE_DEBUG_AFTER_ARCH_BOOLEAN",len(body.data.vertices),len(body.data.polygons))

# Open air flue descends into the combustion chamber, visible from above.
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.121,depth=1.15,location=(0,.16,1.84))
flue=bpy.context.object
flue.name="FLUE_CUTTER_TEMP"
flue.data.materials.append(soot)
active(body)
bo=body.modifiers.new("True smoke exhaust through rock","BOOLEAN")
bo.operation="DIFFERENCE"; bo.solver="EXACT";bo.object=flue
bpy.ops.object.modifier_apply(modifier=bo.name)
bpy.data.objects.remove(flue,do_unlink=True)
print("FORGE_DEBUG_AFTER_FLUE_BOOLEAN",len(body.data.vertices),len(body.data.polygons))

# Softened edge geometry without cartoon-like chiselled stone block outlines.
active(body)
sm=body.modifiers.new("Eroded_Stone_Smooth","SMOOTH")
sm.factor=.42;sm.iterations=1
bpy.ops.object.modifier_apply(modifier=sm.name)
for poly in body.data.polygons: poly.use_smooth=True
# Stable world-scale planar UV projection directly on mesh loops.
# Avoids fragmented automatic island pack, remains valid in background Blender.
# Per-side projection at ~75 cm per scanned texture tile.
uv_layer=body.data.uv_layers.get("Rock_Projected_UV") or body.data.uv_layers.new(name="Rock_Projected_UV")
for poly in body.data.polygons:
    n=poly.normal
    axis=max(range(3),key=lambda k:abs(n[k]))
    for li in poly.loop_indices:
        p=body.data.vertices[body.data.loops[li].vertex_index].co
        if axis==0:
            uv=(p.y*1.19,p.z*1.19)
        elif axis==1:
            uv=(p.x*1.19,p.z*1.19)
        else:
            uv=(p.x*1.19,p.y*1.19)
        uv_layer.data[li].uv=uv
# Verify front opening with actual BVH mesh ray casts: no cosmetically painted fake arch.
inv=body.matrix_world.inverted()
def first_surface_y(x,z):
    origin=inv @ Vector((x,-3,z))
    direction=inv.to_3x3() @ Vector((0,1,0))
    ok,where,nrm,face=body.ray_cast(origin,direction, distance=6.0)
    assert ok,("Forge surface absent",x,z)
    return float((body.matrix_world @ where).y)
cavity_back_y=first_surface_y(0,1.14)
shoulder_front_y=first_surface_y(.82,1.14)
assert cavity_back_y > .12, ("ARCH HOLLOW FAILED - back wall is not visible",cavity_back_y)
assert shoulder_front_y < -.20, ("ARCH OUTER WALL FAILED",shoulder_front_y)
assert cavity_back_y-shoulder_front_y > .42, ("ARCH OPENING TOO SHALLOW",cavity_back_y,shoulder_front_y)
QA_ARCH_OPEN={"center_back_y":round(cavity_back_y,4),
              "outer_shoulder_front_y":round(shoulder_front_y,4),
              "confirmed_depth_m":round(cavity_back_y-shoulder_front_y,4)}
print("GENESIS_TRUE_ARCH_OPENING_CONFIRMED",QA_ARCH_OPEN)
assets.append(body)

# Independent coal/ash microforms reside INSIDE the chamber, never equipment props.
for i in range(23):
    x=random.uniform(-.55,.55)
    y=random.uniform(-.36,.14)
    z=.755+random.uniform(.015,.085)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x,y,z))
    o=bpy.context.object
    o.name="Integrated_Charcoal_%02d"%i
    o.scale=(random.uniform(.055,.13),random.uniform(.06,.12),random.uniform(.037,.08))
    o.rotation_euler=(random.random(),random.random(),random.random())
    o.data.materials.append(coal)
    assets.append(o)

# Ember glow is a very restrained light, not a pile of bright glowing spheres.
bpy.ops.object.light_add(type="POINT",location=(0,-.12,.94))
fire_light=bpy.context.object
fire_light.name="RENDER_ONLY_low_ember_bounce"
fire_light.data.energy=25
fire_light.data.color=(1,.18,.036)
fire_light.data.shadow_soft_size=.35

# Pack only actual 3D asset geometry and PBR maps.
bpy.ops.object.select_all(action="DESELECT")
for o in assets:o.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(OUT/"forge_old_rock_v001.glb"),export_format="GLB",
                          use_selection=True,export_materials="EXPORT",export_image_format="AUTO",
                          export_yup=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"forge_old_rock_v001.blend"))

# Studio turntable stills on neutral floor, no props.
ground=bpy.data.materials.new("Studio_Floor_RENDER_ONLY")
ground.diffuse_color=(.11,.106,.106,1)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.005))
plane=bpy.context.object
plane.name="RENDER_ONLY_Studio_Plane"
plane.data.materials.append(ground)
def area(name,pos,power,size,color):
    bpy.ops.object.light_add(type="AREA",location=pos)
    o=bpy.context.object;o.name=name
    o.data.energy=power
    o.data.shape="DISK"
    o.data.size=size
    o.data.color=color
    direction=Vector((0,0,1)) - o.location
    o.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
area("Key_Light",(-3.1,-4.5,5.7),720,5.5,(1,.93,.85))
area("Fill_Light",(3.5,-2.6,3.4),350,5,(.77,.85,1))
area("Rim_Light",(0,3.7,4.6),810,4.3,(1,.89,.72))
scene.world.color=(.12,.12,.12)
scene.render.engine="CYCLES"
scene.cycles.samples=54
scene.cycles.use_denoising=True
scene.render.resolution_x=1080
scene.render.resolution_y=1080
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.view_settings.view_transform="AgX"
scene.render.film_transparent=False
bpy.ops.object.camera_add()
camera=bpy.context.object
camera.name="RENDER_ONLY_Lookdev_Camera"
scene.camera=camera
camera.data.type="ORTHO"
camera.data.ortho_scale=3.25
shots={
"front": (0,-4.7,2.00),
"three_quarter": (3.45,-5.0,2.65),
"rear": (3.3,4.4,2.35),
"detail": (1.6,-3.35,1.70)
}
for name,pos in shots.items():
    camera.location=pos
    direction=Vector((0,0,1.10))-camera.location
    camera.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
    camera.data.ortho_scale=2.75 if name=="detail" else 3.3
    scene.render.filepath=str(OUT/(name+".png"))
    bpy.ops.render.render(write_still=True)

mesh_faces=sum(len(o.data.polygons) for o in assets if o.type=="MESH")
audit={
  "asset":"Forge_Ancient_Rock", "version":"asymmetric_weathered_stone_v004",
  "basis":"User-approved first 2D visual concept: geometry recreated independently",
  "copyright":"Original independent 3D geometry; Poly Haven Rock Face scanned material CC0",
  "blender":bpy.app.version_string,
  "mesh_objects":len([o for o in assets if o.type=="MESH"]),
  "total_mesh_faces":mesh_faces,
  "texture_files":maps,
  "material_provenance": maps_meta,
  "render_views":list(shots),
  "actual_arch_opening_ray_test": QA_ARCH_OPEN,
  "notes":"Only forge, no bellows or props. V004 asymmetric embedded rock outcrops, sculpted and fissured foundation, 2K scanned CC0 rock. Still under artistic review. NOT yet artistically approved."
}
(OUT/"AUDIT.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")
print("GENESIS_FORGE_CONCEPT_3D_DONE",json.dumps(audit))
