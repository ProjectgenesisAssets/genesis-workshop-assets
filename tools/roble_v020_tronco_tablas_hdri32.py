#!/usr/bin/env python3
"""Project Genesis | Roble V020 review: retain V019 split oak log, repair end grain
and derive boards from its existing PBR material. A candidate, NOT approved.
Requires V019 original artifact and genuine Poly Haven HDRI. Blender 4.5.13 LTS.
"""
import bpy, math, json, random, hashlib, struct
from pathlib import Path
from mathutils import Vector
import numpy as np

BASE=Path("input").resolve()
OUT=Path("output/oak_v020").resolve()
REND=OUT/"renders"
MOD=OUT/"models"
for p in (OUT,REND,MOD):p.mkdir(parents=True,exist_ok=True)
SRC=BASE/"dry-oak-wood.glb"
HDR=BASE/"studio_small_09_2k.hdr"
assert SRC.is_file() and HDR.is_file(), "Existing V019 GLB and genuine Radiance HDRI required"
src_hash=hashlib.sha256(SRC.read_bytes()).hexdigest()
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(SRC))
imported=[o for o in bpy.data.objects if o not in before and o.type=="MESH"]
assert len(imported)==1,("Expected one existing V019 oak mesh",len(imported))
oak=imported[0];oak.name="ROBLE_V020_original_V019_geometry"
oak_data_start=len(oak.data.vertices)
old_material_names=[m.name for m in oak.data.materials]
print("OAK_SOURCE",src_hash,"MATERIALS",old_material_names,
      "VERTS",oak_data_start,"FACES",len(oak.data.polygons),flush=True)
assert len(oak.data.materials)>=3,old_material_names

# Reuse existing actual CC0 photographic bark and longitudinal-grain PBR.
end_idx=next((i for i,m in enumerate(oak.data.materials)
              if m and ("endgrain" in m.name.lower() or "cut_endgrain" in m.name.lower())),None)
assert end_idx is not None,("No source endgrain material found",old_material_names)
bark_idx=next((i for i,m in enumerate(oak.data.materials)
               if m and "bark" in m.name.lower()),None)
side_idx=next((i for i,m in enumerate(oak.data.materials)
               if i!=end_idx and i!=bark_idx),None)
assert side_idx is not None
side_mat=oak.data.materials[side_idx]
print("MATERIAL_INDICES",json.dumps({"side":side_idx,"bark":bark_idx,"end":end_idx}),flush=True)

# Make natural ring-porous oak crosscut with imperfect growth rings, medullary rays,
# fine pores and subtle cross-grain cracks. Endgrain is procedural baked albedo
# (explicitly NOT an additional photographic scan or a texture-color trick).
N=1536
yy,xx=np.mgrid[0:N,0:N].astype(np.float32)
u=(xx+.5)/N-.52;v=(yy+.5)/N-.51
rad=np.sqrt((u*.92)**2+(v*1.03)**2)+1e-5
angle=np.arctan2(v,u)
bend=.006*np.sin(7*angle+19*rad)+.004*np.sin(13*angle-9*rad)+.0025*np.sin(21*angle+14*rad)
r=rad+bend
# Natural irregular growth rings. Avoid squared/end-on parallel zebra stripes.
phase=2*np.pi*(29.5*r+0.12*np.sin(11*r))
wide=np.exp(-((np.cos(phase)-.90)/.21)**2)
fine=np.cos(phase*2.0+.23*np.sin(angle*4))
rays=np.maximum(0,np.cos(47*angle+.8*np.sin(9*r)))**14
pore=np.maximum(0,np.sin(xx*.42+yy*.08)*np.sin(yy*.37-xx*.15))**6
rng=np.random.default_rng(20261104)
fleck=rng.normal(0,.012,(N,N)).astype(np.float32)
# Brown oak heartwood, restrained contrast; unpainted real PBR side material untouched.
detail=(-.145*wide+.014*fine+.041*rays+.014*pore+fleck
        +.025*np.sin(3*angle+14*r))
base=np.stack((.55+detail*.88,.375+detail*.74,.220+detail*.54),axis=-1)
# Fine radial checking fissures, sparse and stopped before pith.
cracks=np.zeros((N,N),dtype=np.float32)
for a0 in (.17,1.37,2.72,4.24,5.62):
    dist=np.abs(np.sin(angle-a0-.025*np.sin(9*r)))
    span=(r>.16)&(r<.435)
    cracks=np.maximum(cracks,(dist<(.005+.001*np.sin(r*32)))*span)
base*=1-.33*cracks[...,None]
base=np.clip(base,0,1)
pixels=np.uint8(np.rint(base*255))
from PIL import Image
end_path=OUT/"oak_v020_true_radial_endgrain.png"
Image.fromarray(pixels,"RGB").save(end_path,compress_level=5)
assert end_path.stat().st_size>100000

# Keep original PBR node links on both long-grain and bark materials.
endmat=bpy.data.materials.new("ROBLE_V020_endgrain_radial_PBR")
endmat.use_nodes=True
bs=endmat.node_tree.nodes.get("Principled BSDF")
bs.inputs["Metallic"].default_value=0.0
bs.inputs["Roughness"].default_value=.88
tex=endmat.node_tree.nodes.new("ShaderNodeTexImage")
tex.image=bpy.data.images.load(str(end_path))
endmat.node_tree.links.new(tex.outputs["Color"],bs.inputs["Base Color"])
oak.data.materials[end_idx]=endmat

# Preserve V019 log vertices/faces. Repair ONLY the end-face UVs, projected
# in their actual transverse plane. The original side UVs remain unchanged.
mesh=oak.data
uv=mesh.uv_layers.active or mesh.uv_layers.new(name="UVMap")
coords=np.array([tuple(v.co) for v in mesh.vertices],dtype=np.float64)
ranges=np.ptp(coords,axis=0)
mainaxis=int(np.argmax(ranges))
minor=[i for i in range(3) if i!=mainaxis]
center=coords.mean(axis=0)
extent=max(np.ptp(coords[:,minor[0]]),np.ptp(coords[:,minor[1]]))
end_faces=[p for p in mesh.polygons if p.material_index==end_idx]
assert end_faces,("End material has no polygons",old_material_names)
# Endgrain bitmap represents the tree radius. Make UV mapping truly radial.
for face in end_faces:
    for lid in face.loop_indices:
        p=mesh.vertices[mesh.loops[lid].vertex_index].co
        uv.data[lid].uv=(.52+(p[minor[0]]-center[minor[0]])/(extent*1.10),
                         .51+(p[minor[1]]-center[minor[1]])/(extent*1.10))
assert len(oak.data.vertices)==oak_data_start
print("OAK_ENDGRAIN_FIXED",len(end_faces),"faces", "major axis",mainaxis,flush=True)

# Reuse original side-grain shader for three physically distinct sawed oak boards.
# Their dimensions and stagger are based on the same real wood stock,
# rather than re-coloring the already approved ash boards.
rand=random.Random(1723)
board_specs=[
    (1.66,.392,.103,-.075,-.13,.080,-.014),
    (1.51,.360,.103,.060,.072,.183,.026),
    (1.60,.356,.099,-.045,.235,.286,-.035)
]
boards=[]
for idx,(L,W,T,cx,cy,cz,yaw) in enumerate(board_specs):
    stations=19
    verts=[];faces=[];materials=[]
    # Four corners per cross-section. Subtle saw irregularities in silhouette.
    for j in range(stations):
        t=j/(stations-1)
        x=L*(t-.5)
        for signy,signz in ((-1,-1),(1,-1),(1,1),(-1,1)):
            taper=1+.006*math.sin(4.0*t+idx)+.003*math.sin(13*t+idx)
            yy=signy*W*.5*taper+.0012*math.sin(7*t+idx)
            zz=signz*T*.5+.0017*math.sin(11*t+idx*2.1)
            if j in (0,stations-1):x+=(rand.random()-.5)*.0025
            verts.append((x,yy,zz))
    for j in range(stations-1):
        for k in range(4):
            a=j*4+k;b=j*4+(k+1)%4
            faces.append((a,b,b+4,a+4));materials.append(0)
    faces += [tuple(reversed(range(4))),tuple((stations-1)*4+k for k in range(4))]
    materials += [1,1]
    m=bpy.data.meshes.new("Oak board cross-section V020")
    m.from_pydata(verts,[],faces);m.update()
    ob=bpy.data.objects.new("ROBLE_V020_TABLA_%02d"%(idx+1),m)
    bpy.context.collection.objects.link(ob)
    m.materials.append(side_mat)
    m.materials.append(endmat)
    for pol,idxmat in zip(m.polygons,materials):
        pol.material_index=idxmat
    uvs=m.uv_layers.new(name="UVMap")
    for pol in m.polygons:
        for lid in pol.loop_indices:
            q=m.vertices[m.loops[lid].vertex_index].co
            if pol.material_index==1:
                # Center of growth rings is outside each milled board, yielding
                # anatomical nested ARCS rather than full circular "coins".
                uvs.data[lid].uv=(.52+(q.y+W*.7)/(.88),.51+(q.z+T*.20)/(.85))
            else:
                # Wood grain always runs longitudinally along X.
                span=q.y/W if abs(pol.normal.z)>.65 else q.z/T
                uvs.data[lid].uv=(.03+(q.x/L+.5)*2.15,.15+.72*(span+.5))
    ob.location=(cx,cy,cz)
    ob.rotation_euler.z=yaw
    for pol in m.polygons:pol.use_smooth=False
    boards.append(ob)

# Make sure boards are not completely flat, single-sided planes.
assert sum(len(o.data.polygons) for o in boards)>160
assert len(boards)==3

def export(objs,path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    bpy.ops.export_scene.gltf(filepath=str(path),export_format="GLB",use_selection=True,
                              export_texcoords=True,export_normals=True,export_materials="EXPORT")
    assert path.stat().st_size>200000
export([oak],MOD/"ProjectGenesis_Roble_Tronco_V020.glb")
export(boards,MOD/"ProjectGenesis_Roble_Tablas_V020.glb")

# Genuine HDRI environment - no JPG/PNG substitutions.
scene=bpy.context.scene
scene.render.engine="CYCLES";scene.cycles.samples=64
scene.render.threads_mode="FIXED";scene.render.threads=4
scene.view_layers[0].cycles.use_denoising=False
scene.render.resolution_x=1100;scene.render.resolution_y=850
scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.render.image_settings.color_mode="RGBA"
scene.view_settings.view_transform="AgX"
scene.view_settings.look="AgX - Medium High Contrast"
scene.view_settings.exposure=-.38
scene.world=bpy.data.worlds.new("Studio Small 09 real 32bit HDRI")
scene.world.use_nodes=True
wn=scene.world.node_tree.nodes;wl=scene.world.node_tree.links
wn.clear()
env=wn.new("ShaderNodeTexEnvironment")
env.image=bpy.data.images.load(str(HDR))
assert env.image.file_format=="HDR" and env.image.depth>=24
bg=wn.new("ShaderNodeBackground");bg.inputs["Strength"].default_value=.55
outnode=wn.new("ShaderNodeOutputWorld")
wl.new(env.outputs["Color"],bg.inputs["Color"])
wl.new(bg.outputs["Background"],outnode.inputs["Surface"])
def area(name,loc,power,size):
    light=bpy.data.lights.new(name,"AREA")
    obj=bpy.data.objects.new(name,light)
    bpy.context.collection.objects.link(obj)
    obj.location=loc
    obj.rotation_euler=(Vector((0,0,.14))-obj.location).to_track_quat("-Z","Y").to_euler()
    light.energy=power;light.size=size
area("Oak neutral softbox key",(-2.5,-3.0,4.8),240,4.6)
area("Oak edge soft fill",(2.5,1.0,3.6),85,3.2)
camd=bpy.data.cameras.new("Project Genesis oak review")
cam=bpy.data.objects.new("Project Genesis oak review",camd)
bpy.context.collection.objects.link(cam)
scene.camera=cam;camd.type="ORTHO"
def render(name,targets,azimuth,elev,scale,focus=None):
    for o in [oak]+boards:o.hide_render=o not in targets
    focus=Vector(focus or (0,0,.16))
    az=math.radians(azimuth);el=math.radians(elev)
    cam.location=focus+Vector((math.sin(az)*math.cos(el)*3.6,-math.cos(az)*math.cos(el)*3.6,math.sin(el)*3.6))
    cam.rotation_euler=(focus-cam.location).to_track_quat("-Z","Y").to_euler()
    camd.ortho_scale=scale
    scene.render.image_settings.file_format="OPEN_EXR"
    scene.render.image_settings.color_depth="32"
    scene.render.filepath=str(REND/(name+".exr"))
    bpy.ops.render.render(write_still=True)
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_depth="8"
    bpy.data.images["Render Result"].save_render(str(REND/(name+".png")),scene=scene)
    assert (REND/(name+".exr")).stat().st_size>100000
    assert (REND/(name+".png")).stat().st_size>40000
    print("GENESIS_OAK_RENDER",name,flush=True)

render("roble_tronco_3cuartos",[oak],56,25,2.12)
render("roble_tronco_corte",[oak],76,21,1.62)
render("roble_tronco_dorso",[oak],-48,26,2.14)
render("roble_tablas_3cuartos",boards,43,25,2.23,(0,.05,.16))
render("roble_tablas_cantos",boards,76,24,1.82,(.26,.08,.20))
render("roble_tablas_superior",boards,25,63,2.17,(0,.05,.16))

# Read the real binary GLB JSON to check material images and triangle budget.
def validate_glb(p):
    data=p.read_bytes()
    assert data[:4]==b"glTF"
    assert struct.unpack_from("<I",data,4)[0]==2
    assert struct.unpack_from("<I",data,8)[0]==len(data)
    jlen,jtype=struct.unpack_from("<I4s",data,12)
    assert jtype==b"JSON"
    gltf=json.loads(data[20:20+jlen])
    tris=sum(gltf["accessors"][pr["indices"]]["count"]//3
             for m in gltf["meshes"] for pr in m["primitives"])
    assert tris<30000,(p.name,tris)
    assert gltf.get("images"),"Missing embedded PBR images"
    assert any("radial" in im.get("name","").lower() or "endgrain" in im.get("name","").lower()
               for im in gltf["images"]), "Missing corrected endgrain"
    return {"file":p.name,"sha256":hashlib.sha256(data).hexdigest(),
            "bytes":len(data),"triangles":tris,"material_count":len(gltf["materials"]),
            "images":len(gltf["images"]),"meshes":len(gltf["meshes"])}

report={
 "asset":"dry-oak-wood","candidate":"V020_review_not_approved",
 "source":"V019_distinct_candidate","source_glb_sha256":src_hash,
 "source_geometry_vertex_count":oak_data_start,
 "new_oak_log_geometry_vertex_count":len(oak.data.vertices),
 "geometry_original_unchanged":oak_data_start==len(oak.data.vertices),
 "endgrain":"baked realistic radial rings, rays and checks; corrected transverse UV",
 "side_and_bark_PBR":"from same original V019 oak, unchanged",
 "board_geometry":"three timber boards with tiny saw irregularities and distinct thickness",
 "renderer":"Blender "+bpy.app.version_string+" Cycles 64 samples",
 "lighting":{"hdr":"studio_small_09_2k.hdr","format":"Radiance HDRI RGBE 32-bit environment",
             "samples":64,"hdr_strength":.55,"output":"32-bit float EXR and PNG"},
 "approved":False,"integrated":False,
 "outputs":[validate_glb(p) for p in [MOD/"ProjectGenesis_Roble_Tronco_V020.glb",MOD/"ProjectGenesis_Roble_Tablas_V020.glb"]]
}
(OUT/"validation.json").write_text(json.dumps(report,indent=2,ensure_ascii=False))
print("GENESIS_OAK_V020_COMPLETE",json.dumps(report,ensure_ascii=False),flush=True)
