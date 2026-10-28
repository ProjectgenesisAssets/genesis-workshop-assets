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

N=1536
rng=np.random.default_rng(7712)
broad=field(N,9,rng)
mid=field(N,36,rng)
fine=field(N,137,rng)
grain=rng.normal(0,1,(N,N)).astype(np.float32)
tint=field(N,7,rng)
h=.50 + .055*broad + .028*mid + .012*fine + .005*grain
gy,gx=np.gradient(h)
nx=-gx*2.8
ny=-gy*2.8
nz=np.ones_like(nx)
norm=np.sqrt(nx*nx+ny*ny+nz*nz)
normal=np.stack([.5+.5*nx/norm,.5+.5*ny/norm,.5+.5*nz/norm],axis=2)
roughmap=np.clip(.86+.028*broad+.012*mid+.007*grain,.69,.98)

def save_map(name,rgb,is_data=False):
    im=bpy.data.images.new(name,width=N,height=N,alpha=True)
    alpha=np.ones((N,N,1),dtype=np.float32)
    rgba=np.concatenate([np.clip(rgb,0,1),alpha],axis=2)
    im.pixels.foreach_set(rgba.ravel())
    path=TEX/(name+".png")
    im.filepath_raw=str(path)
    im.file_format="PNG"
    im.save()
    if is_data: im.colorspace_settings.name="Non-Color"
    im.pack()
    maps.append(path.name)
    return im

stone_variation=.94+.075*broad+.04*mid+.012*fine+.006*grain
sand=np.clip(.5+.22*tint,0,1)
rockrgb=np.stack([
    (.345+.030*sand)*stone_variation,
    (.327+.010*sand)*stone_variation,
    (.295-.007*sand)*stone_variation
],axis=2)
soot_variation=np.clip(.92+.055*broad+.035*mid+.020*grain,.5,1.1)
sootrgb=np.stack([
    (.074+.008*sand)*soot_variation,
    (.069+.006*sand)*soot_variation,
    (.061+.004*sand)*soot_variation
],axis=2)
roughimg=save_map("rock_roughness",np.repeat(roughmap[...,None],3,axis=2),True)
normimg=save_map("rock_normal",normal.astype(np.float32),True)
rockimg=save_map("natural_aged_rock_albedo",rockrgb)
sootimg=save_map("coal_soot_rock_albedo",sootrgb)

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
rock=pbr("NaturalRock_Worn_CoarsePBR_1536",rockimg,.84,.38)
soot=pbr("Firebox_Soot_Stone_PBR_1536",sootimg,.91,.24)
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

# Large unified stone mass: rectangular, softened base and arched bulging hood.
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,.37))
body=bpy.context.object
body.name="GENESIS_Forge_Rock_Mass"
body.dimensions=(2.24,1.12,.74)
apply_transform(body)

bpy.ops.mesh.primitive_uv_sphere_add(segments=100,ring_count=50,location=(0,.015,1.03))
hood=bpy.context.object
hood.name="Organic_Sculpt_Arch_Dome"
hood.scale=(1.08,.55,.81)
apply_transform(hood)

bpy.ops.mesh.primitive_cone_add(vertices=80,radius1=.325,radius2=.205,depth=.65,location=(0,.16,1.87))
chimney=bpy.context.object
chimney.name="Organic_Rock_Chimney"
apply_transform(chimney)

bpy.ops.object.select_all(action="DESELECT")
for o in (body,hood,chimney): o.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.object.join()
body.name="GENESIS_Forge_MonolithicRock"
active(body)
body.data.remesh_voxel_size=.026
bpy.ops.object.voxel_remesh()

# Multi-scale natural erosion. This is actual mesh relief, not painted bricks.
for v in body.data.vertices:
    p=v.co.copy()
    macro=noise.noise(p*2.35+Vector((6.1,8.7,2.4)))
    meso=noise.noise(p*7.5+Vector((1.9,4.6,5.1)))
    micro=noise.noise(p*23+Vector((9.2,1.1,3.7)))
    d=.023*macro+.009*meso+.0025*micro
    v.co += v.normal*d
body.data.update()
body.data.materials.append(rock)
body.data.materials.append(soot)

# Firebox arch: true hollow, arched and deep; never a solid decorative black patch.
radius=.745
cross=[(-radius,.735),(radius,.735)]
cross.extend((radius*(1-2*j/48),.952+.552*math.sqrt(max(0,1-(1-2*j/48)**2))) for j in range(49))
num=len(cross)
verts=[(x,y,z) for y in (-.79,.29) for (x,z) in cross]
faces=[]
faces.append(tuple(reversed(tuple(range(num)))))
faces.append(tuple(range(num,2*num)))
for j in range(num):
    k=(j+1)%num
    faces.append((j,k,num+k,num+j))
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

# Softened edge geometry without cartoon-like chiselled stone block outlines.
active(body)
sm=body.modifiers.new("Eroded_Stone_Smooth","SMOOTH")
sm.factor=.85;sm.iterations=2
bpy.ops.object.modifier_apply(modifier=sm.name)
for poly in body.data.polygons: poly.use_smooth=True
active(body)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(island_margin=.005)
bpy.ops.object.mode_set(mode="OBJECT")
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
  "asset":"Forge_Ancient_Rock", "version":"concept_reconstruction_v001",
  "basis":"User-approved first 2D visual concept: geometry recreated independently",
  "copyright":"Original procedural Blender geometry and noise-derived PBR maps",
  "blender":bpy.app.version_string,
  "mesh_objects":len([o for o in assets if o.type=="MESH"]),
  "total_mesh_faces":mesh_faces,
  "texture_files":maps,
  "render_views":list(shots),
  "notes":"Only forge, no bellows, tool rack, barrels, or other workshop props. NOT yet artistically approved."
}
(OUT/"AUDIT.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")
print("GENESIS_FORGE_CONCEPT_3D_DONE",json.dumps(audit))
