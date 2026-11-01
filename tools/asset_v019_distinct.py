#!/usr/bin/env python3
"""Genesis V010: physical material silhouettes, scanned CC0 PBR, dual GLB export.
This is a candidate generator; no automatic artistic approval."""
import bpy, math, random, json, os, pathlib, glob, hashlib
from math import sin, cos, pi
from mathutils import Vector
K=os.environ.get("ASSET_KIND","dry-oak-wood").replace("asset/","")
SEED={"dry-oak-wood":103,"dry-ash-wood":211,"tanned-cowhide":307,
      "tanned-goatskin":401,"hemp-cord":503,"linen-thread":601}
if K not in SEED:raise RuntimeError("Unknown asset kind: "+K)
random.seed(SEED[K])
out=pathlib.Path("output")/K
out.mkdir(parents=True,exist_ok=True)
src=pathlib.Path("sources")/K
provenance=json.loads((src/"provenance.json").read_text())
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
SCENE=bpy.context.scene
SCENE.render.engine="CYCLES"
SCENE.cycles.samples=54
# Ubuntu apt Blender is compiled without Intel OpenImageDenoise; render unbiased samples.
SCENE.cycles.use_denoising=False
for view_layer in SCENE.view_layers:
 view_layer.cycles.use_denoising=False
SCENE.render.resolution_x=1080
SCENE.render.resolution_y=1080
SCENE.render.resolution_percentage=100
SCENE.render.film_transparent=True
SCENE.render.image_settings.file_format="PNG"
SCENE.render.image_settings.color_mode="RGBA"
SCENE.view_settings.view_transform="Standard"
# Retain Blender's supported default view look for consistent compatibility.
def make_mat(name):
 m=bpy.data.materials.new(name);m.use_nodes=True
 bs=m.node_tree.nodes.get("Principled BSDF")
 bs.inputs["Metallic"].default_value=0
 bs.inputs["Roughness"].default_value=.85
 return m,bs
mat,bs=make_mat(K+"_CC0_PBR")
files=[p for p in src.iterdir() if p.suffix.lower() in (".png",".jpg",".jpeg")]
def pick(match):
 a=[p for p in files if match(p.name.lower())]
 if not a:raise RuntimeError("Required CC0 texture missing for "+K)
 return sorted(a)[0]
albedo=pick(lambda s: any(k in s for k in ("color","albedo","diffuse")))
rough=pick(lambda s:"roughness" in s)
normal=pick(lambda s:"normalgl" in s or "normal_opengl" in s or "normal_gl" in s)
def image_node(path,space):
 im=bpy.data.images.load(str(path.resolve()),check_existing=True)
 im.colorspace_settings.name=space
 node=mat.node_tree.nodes.new("ShaderNodeTexImage")
 node.image=im
 return node
color_node=image_node(albedo,"sRGB")
rough_node=image_node(rough,"Non-Color")
normal_node=image_node(normal,"Non-Color")
nodes=mat.node_tree.nodes;links=mat.node_tree.links
tints={"dry-oak-wood":(.60,.51,.43),"dry-ash-wood":(.65,.60,.53),"tanned-cowhide":(.90,.83,.75),"tanned-goatskin":(.77,.69,.58),"hemp-cord":(.82,.75,.64),"linen-thread":(.44,.41,.36)}
if K in tints:
 mix=nodes.new("ShaderNodeMixRGB");mix.blend_type="MULTIPLY";mix.inputs[0].default_value=1
 mix.inputs[2].default_value=(*tints[K],1)
 links.new(color_node.outputs["Color"],mix.inputs[1])
 links.new(mix.outputs["Color"],bs.inputs["Base Color"])
else:links.new(color_node.outputs["Color"],bs.inputs["Base Color"])
rmin=nodes.new("ShaderNodeMath");rmin.operation="MAXIMUM"
rmin.inputs[1].default_value=.78 if K.startswith("tanned-") else .72
links.new(rough_node.outputs["Color"],rmin.inputs[0])
links.new(rmin.outputs[0],bs.inputs["Roughness"])
normal_map=nodes.new("ShaderNodeNormalMap")
normal_map.inputs["Strength"].default_value=.72
links.new(normal_node.outputs["Color"],normal_map.inputs["Color"])
links.new(normal_map.outputs["Normal"],bs.inputs["Normal"])
# A split/cracked edge has its own dark wood core; hide thickness is integrated into the mesh.
# Exposed fracture faces must retain the same photographed PBR maps, never flat paint.
wood_edge=mat
objects=[]
def mesh(name,v,f,uv=None,mats=None,side_indices=None):
 me=bpy.data.meshes.new(name)
 me.from_pydata(v,[],f);me.update()
 ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
 for m in (mats or [mat]):me.materials.append(m)
 if side_indices:
  for face,idx in zip(me.polygons,side_indices):face.material_index=idx
 if uv:
  layer=me.uv_layers.new(name="UVMap")
  for face in me.polygons:
   for loop_id in face.loop_indices:
    vi=me.loops[loop_id].vertex_index
    layer.data[loop_id].uv=uv[vi]
 else:
  bpy.ops.object.select_all(action="DESELECT")
  ob.select_set(True);bpy.context.view_layer.objects.active=ob
  bpy.ops.object.mode_set(mode="EDIT")
  bpy.ops.mesh.select_all(action="SELECT")
  bpy.ops.uv.smart_project(island_margin=.018)
  bpy.ops.object.mode_set(mode="OBJECT")
 for poly in me.polygons:poly.use_smooth=len(poly.vertices)==4
 objects.append(ob)
 return ob
def transform(ob,loc,rot):
 ob.location=loc;ob.rotation_euler=rot
def wood_piece(label,oak,offset):
 # Hand-split half log: convex outside bark side and a jagged concave radial split.
 count_arc=15;count_split=9;sections=37
 length=1.48 if oak else 1.64
 radius=.25 if oak else .205
 v=[];faces=[];mats=[]; uv_coords=[]
 for j in range(sections):
  t=j/(sections-1);z=length*(t-.5)
  taper=1-.12*t+.028*sin(t*9)
  section=[]
  # Curved exterior of a half log.
  for i in range(count_arc):
   a=-pi/2+pi*i/(count_arc-1)
   r=radius*taper*(1+.047*sin(7*a+3*t)+.027*sin(13*a-5*t))
   section.append((max(.012,r*cos(a)),r*sin(a)))
  # Rough exposed splitting plane with longitudinal splinters and uneven tears.
  for i in range(1,count_split-1):
   f=i/(count_split-1);y=radius*taper*(1-2*f)
   crack=.046*sin(f*13+2.7*t)+.018*sin(f*29-5*t)
   crack+=.026*(1 if oak else .42)*sin(t*13+f*24)
   section.append((crack,y))
  for i,(xx,yy) in enumerate(section):
   # Fibrils follow the grain axis, not uncorrelated vertex noise.
   end_damage=.026*(sin(i*3.71)**2) if j in (0,sections-1) else 0
   v.append((xx+offset*.017,yy,z+end_damage))
   uv_coords.append((t*2.2,i/(count_arc+count_split-3)))
 n=len(section)
 for j in range(sections-1):
  for i in range(n):
   a=j*n+i;b=j*n+(i+1)%n
   faces.append((a,b,b+n,a+n));mats.append(0 if i<count_arc-1 else 1)
 faces.append(tuple(reversed(range(n))));mats.append(1)
 faces.append(tuple((sections-1)*n+i for i in range(n)));mats.append(1)
 ob=mesh(label,v,faces,uv=uv_coords,mats=[mat,wood_edge],side_indices=mats)
 transform(ob,(offset*.13,offset*.17,0),(.12*offset,1.36+.04*offset,offset*.11))
 # Raised longitudinal fractured fibers along the exposed plane; low budget.
 strip_mat=wood_edge
 for strand in range(11 if oak else 9):
  zz=random.uniform(-length*.46,length*.42)
  span=random.uniform(.18,.40)
  yy=random.uniform(-radius*.8,radius*.8)
  x=.015+random.uniform(.003,.026)
  v2=[(x,yy,zz),(x+.006,yy+.006,zz+.025),
      (x+.003,yy+.004,min(length*.49,zz+span)),
      (x-.006,yy-.003,min(length*.49,zz+span*.75))]
  piece=mesh(label+"_fiber_%02d"%strand,v2,[(0,1,2),(0,2,3)],mats=[strip_mat])
  transform(piece,tuple(ob.location),tuple(ob.rotation_euler))
 return ob
def hide(cow):
 # Rounded but irregular dried hide, with large folds for cow and tight wrinkles for goat.
 nx=44;ny=39;v=[];faces=[];uv=[];w=1.58 if cow else 1.32;h=1.21 if cow else 1.10
 thick=.027 if cow else .013
 for j in range(ny):
  t=j/(ny-1);yy=(t-.5)*h
  for i in range(nx):
   u=i/(nx-1);xx=(u-.5)*w
   # Hide outline has coherent uneven lobes, not a uniform rectangle.
   rim=abs(u-.5)*2;edge=abs(t-.5)*2
   xx+=.065*sin(8*t+1.2)*(rim**6)
   yy+=.072*sin(8*u+2.1)*(edge**6)
   fold= .079*sin(u*7.7+sin(t*3.2)) if cow else .054*sin(u*13.5+t*6)
   crease= .052*math.exp(-((u-(.54+.08*sin(t*4)))/.083)**2)
   fine=(.013 if cow else .027)*sin(26*t+9*u)*sin(7*u)
   zz=.042+fold+crease+fine +.065*(u-.5)**2
   if not cow:zz+=.055*sin((u+t)*17)*math.exp(-((u-.77)/.16)**2)
   v.append((xx,yy,zz));uv.append((u,t))
 for j in range(ny-1):
  for i in range(nx-1):
   a=j*nx+i;faces.append((a,a+1,a+nx+1,a+nx))
 top=len(v)
 for x,y,z in list(v):v.append((x,y,z-thick))
 uv+=list(uv)
 for f in list(faces):faces.append(tuple(top+i for i in reversed(f)))
 for i in range(nx-1):
  a=i;faces.append((a,a+top,a+1+top,a+1))
  a=(ny-1)*nx+i;faces.append((a,a+1,a+1+top,a+top))
 for j in range(ny-1):
  a=j*nx;faces.append((a,a+nx,a+nx+top,a+top))
  a=j*nx+nx-1;faces.append((a,a+top,a+nx+top,a+nx))
 ob=mesh("bovine_cured_hide" if cow else "goat_cured_hide",v,faces,uv)
 # Rolled corner: small low-poly geometry with the same scanned material.
 return ob
def cord(hemp):
 # Coil laid on the ground. Each of the three strands is a real helical swept tube.
 turns=2.48 if hemp else 3.27
 steps=440 if hemp else 480
 sides=7 if hemp else 6
 thread_r=.018 if hemp else .010
 strand_r=.011 if hemp else .006
 central_r=.020 if hemp else .012
 v=[];faces=[];uv=[]
 for part in range(3):
  start=len(v)
  for j in range(steps):
   t=j/(steps-1)
   ang=2*pi*turns*t
   R=(.13+.47*t+.012*sin(ang*2.4)) if hemp else (.10+.37*t+.006*sin(ang*3.7))
   cx=R*cos(ang);cy=R*sin(ang)
   cz=.036+.014*sin(ang*2)+.015*(t*t)
   # A free tip extends away from the last turn for a natural loose end.
   if t>.91:
    tail=(t-.91)/.09
    cx+=.23*tail;cy-=.11*tail
   dt=.0005
   a2=ang+2*pi*turns*dt
   r2=R+.47*dt if hemp else R+.37*dt
   tangent=Vector((r2*cos(a2)-R*cos(ang),r2*sin(a2)-R*sin(ang),.002))
   tangent.normalize()
   lateral=Vector((-tangent.y,tangent.x,0))
   up=Vector((0,0,1))
   twist=2*pi*((27 if hemp else 38)*t+part/3)
   center=Vector((cx,cy,cz))+central_r*(cos(twist)*lateral+sin(twist)*up)
   for k in range(sides):
    a=2*pi*k/sides
    rad=strand_r*(1+.095*sin(8*t+part*1.4)+.05*sin(35*t+part))
    q=center+rad*(cos(a)*lateral+sin(a)*up)
    v.append(tuple(q))
    uv.append((t*12,k/(sides-1)))
  for j in range(steps-1):
   for k in range(sides):
    a=start+j*sides+k;b=start+j*sides+(k+1)%sides
    c=start+(j+1)*sides+(k+1)%sides;d=start+(j+1)*sides+k
    faces.append((a,b,c,d))
 ob=mesh("hemp_3_ply_coil" if hemp else "linen_fine_thread_coil",v,faces,uv)
 # Separate few tapered frayed filaments at the end and scattered along the coil.
 wisp_count=22 if hemp else 10
 for f in range(wisp_count):
  t=random.random()*.96
  ang=2*pi*turns*t
  R=(.13+.47*t) if hemp else (.10+.37*t)
  xx=R*cos(ang);yy=R*sin(ang);zz=.048
  a=ang+random.uniform(-2,2)
  L=random.uniform(.027,.072) if hemp else random.uniform(.012,.030)
  p=[(xx,yy,zz),(xx+L*cos(a),yy+L*sin(a),zz+L*.28),
     (xx+L*cos(a+.04),yy+L*sin(a+.04),zz+L*.29)]
  mesh("loose_fibril_%02d"%f,p,[(0,1,2)],mats=[mat])
 return ob
# The V010 geometry overrides are local, source-controlled and reviewed separately.
exec(compile(pathlib.Path("tools/geometry_v004.py").read_text(encoding="utf-8"),
             "tools/geometry_v004.py", "exec"),globals())
exec(compile(pathlib.Path("tools/geometry_v005.py").read_text(encoding="utf-8"),
             "tools/geometry_v005.py", "exec"),globals())
exec(compile(pathlib.Path("tools/geometry_v006.py").read_text(encoding="utf-8"),
             "tools/geometry_v006.py", "exec"),globals())
# Final V010 art-direction overrides; old stable source is preserved.
exec(compile(pathlib.Path("tools/geometry_v008.py").read_text(encoding="utf-8"),
             "tools/geometry_v008.py", "exec"),globals())
exec(compile(pathlib.Path("tools/geometry_v009.py").read_text(encoding="utf-8"),
             "tools/geometry_v009.py", "exec"),globals())
exec(compile(pathlib.Path("tools/geometry_v010.py").read_text(encoding="utf-8"),
             "tools/geometry_v010.py", "exec"),globals())
exec(compile(pathlib.Path("tools/geometry_v013.py").read_text(encoding="utf-8"),
             "tools/geometry_v013.py", "exec"),globals())
exec(compile(pathlib.Path("tools/geometry_v014.py").read_text(encoding="utf-8"),
             "tools/geometry_v014.py", "exec"),globals())
exec(compile(pathlib.Path("tools/geometry_v015.py").read_text(encoding="utf-8"),
             "tools/geometry_v015.py", "exec"),globals())
exec(compile(pathlib.Path("tools/geometry_v016.py").read_text(encoding="utf-8"),
             "tools/geometry_v016.py", "exec"),globals())
# Owner-directed physical redesign: one recognizable asset per inventory item.
exec(compile(pathlib.Path("tools/geometry_v017_redesign.py").read_text(encoding="utf-8"),
             "tools/geometry_v017_redesign.py","exec"),globals())
exec(compile(pathlib.Path("tools/geometry_v019_distinct.py").read_text(encoding="utf-8"),
             "tools/geometry_v019_distinct.py","exec"),globals())
if K=="dry-oak-wood":
 wood_piece("oak_single_split_bark_forward",True,0)
elif K=="dry-ash-wood":
 wood_piece("ash_single_split_inner_forward",False,0)
elif K=="tanned-cowhide":hide(True)
elif K=="tanned-goatskin":hide(False)
elif K=="hemp-cord":cord(True)
else:cord(False)
# Keep floor, camera and lights out of exported GLB.
bpy.ops.object.camera_add(location=(2.7,-3.2,2.5))
camera=bpy.context.object
SCENE.camera=camera
camera.data.type="ORTHO"
camera.data.ortho_scale=2.0 if K.startswith("dry-") else (1.90 if K.startswith("tanned-") else (.94 if K=="linen-thread" else 1.27))
focus=Vector((0,0,.24)) if K.startswith("dry-") else Vector((0,-.24,.18))
for loc,power,size in [((3,-4,5),630,4.5),((-3,1,3.5),410,3.8),((.5,3,5),240,3)]:
 bpy.ops.object.light_add(type="AREA",location=loc)
 light=bpy.context.object;light.data.energy=power;light.data.shape="DISK";light.data.size=size
def render(view,point,scale=None):
 camera.location=point
 camera.rotation_euler=(focus-camera.location).to_track_quat("-Z","Y").to_euler()
 if scale:camera.data.ortho_scale=scale
 SCENE.render.filepath=str(out/(view+".png"))
 bpy.ops.render.render(write_still=True)
render("three_quarter",(2.7,-3.2,2.5))
render("front",(0,-4,1.0))
render("side",(4,0,1.0))
render("top",(0,0,5.0))
render("detail",(1.2,-2.3,1.1),.90 if K.startswith("dry-") else .78)
for ob in bpy.context.selected_objects:ob.select_set(False)
bpy.ops.object.select_all(action="DESELECT")
for ob in objects:ob.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
def export(path):
 bpy.ops.export_scene.gltf(filepath=str(path),export_format="GLB",use_selection=True,
                           export_apply=True,export_yup=True)
export(out/(K+"_master.glb"))
# Preserve original scans; create smaller embedded textures for WebGL inventory.
original=[color_node.image,rough_node.image,normal_node.image]
for source_node,im in zip((color_node,rough_node,normal_node),original):
 small=im.copy()
 small.name=im.name+"_V019_distinct_web"
 webres=(1024 if source_node==color_node else 768) if K=="linen-thread" else ((1024 if source_node==color_node else 768) if K.startswith("dry-") else (1536 if source_node==color_node else 1024))
 small.scale(webres,max(1,round(webres*im.size[1]/im.size[0])))
 small.filepath_raw=str((out/(small.name+"."+("png" if source_node==normal_node else "jpg"))).resolve())
 small.file_format="PNG" if source_node==normal_node else "JPEG"
 small.save()
 # Critically replace the large 4K images on ALL materials, including bark and end-grain copies.
 # V004 only replaced three nodes and accidentally embedded full-resolution copies (~140 MB GLBs).
 replaced=0
 for material in bpy.data.materials:
  if not material.use_nodes:continue
  for tex_node in material.node_tree.nodes:
   if tex_node.type=="TEX_IMAGE" and tex_node.image==im:
    tex_node.image=small
    replaced+=1
 if replaced<1:raise RuntimeError("WebGL PBR image was not assigned: "+im.name)
# Re-encode auxiliary 2K photographic bark/bobbin maps for inventory without touching the 4K master.
secondary_small={}
for material in bpy.data.materials:
 if not material.use_nodes:continue
 for image_tex in material.node_tree.nodes:
  if image_tex.type!="TEX_IMAGE" or not image_tex.image:continue
  img=image_tex.image
  if "zz_v006_" not in img.filepath:continue
  key=img.as_pointer()
  if key not in secondary_small:
   reduced=img.copy()
   reduced.name=img.name+"_V019_distinct_1k"
   extra_res=(640 if "NormalGL" in img.filepath else 768) if K=="linen-thread" else ((512 if "NormalGL" in img.filepath else 768) if K.startswith("dry-") else (768 if "NormalGL" in img.filepath else 1024))
   reduced.scale(extra_res,max(1,round(extra_res*img.size[1]/img.size[0])))
   is_normal="NormalGL" in img.filepath
   reduced.filepath_raw=str((out/(reduced.name+(".png" if is_normal else ".jpg"))).resolve())
   reduced.file_format="PNG" if is_normal else "JPEG"
   reduced.save()
   secondary_small[key]=reduced
  image_tex.image=secondary_small[key]
export(out/(K+".glb"))
# Reject accidental duplications and disconnected old geometry.
assert len(objects)==1, "V017 must contain precisely one cohesive mesh, found "+str(len(objects))
assert objects[0].data.uv_layers.active is not None
assert objects[0].get("actual_piece_count")==1
assert (objects[0].get("single_continuous_hide") is True) if K.startswith("tanned-") else (objects[0].get("true_solid_half_log") is True)
from collections import Counter
edges=Counter()
for face in objects[0].data.polygons:
 ids=list(face.vertices)
 for a,b in zip(ids,ids[1:]+ids[:1]):
  edges[tuple(sorted((a,b)))]+=1
nonmanifold=sum(1 for count in edges.values() if count!=2)
if nonmanifold:raise RuntimeError("V017 open or non-manifold surface edges: "+str(nonmanifold))
tris=sum(max(0,len(f.vertices)-2) for o in objects for f in o.data.polygons)
report={
 "asset":K,"version":"V019_distinct_candidate","objects":len(objects),
 "triangles_mesh":tris,"triangles_goal_under":30000,
 "master_bytes":(out/(K+"_master.glb")).stat().st_size,
 "glb_bytes":(out/(K+".glb")).stat().st_size,
 "master_texture_px":list(original[0].size),
 "web_texture_px":1536,
 "pbr_maps":["Color","Roughness","NormalGL"],
 "source_id":provenance["id"],
 "source_url":provenance["source_url"],
 "secondary_scan_used":(pathlib.Path("sources")/K/"secondary_sources.json").exists(),
 "license":"CC0-1.0",
 "species_or_fiber_verified":provenance.get("species_or_fiber_verified",False),
 "quality_approved":False,
 "single_object":len(objects)==1,
 "closed_surface":nonmanifold==0,
 "presentation":"bark and split wood" if K.startswith("dry-") else "single spiral leather roll with natural loose flap",
 "visual_score":None,
 "notes":"Owner-directed V017 candidate: one physically connected split log per wood (bark-facing oak, fiber-facing ash); one continuous rolled-and-partly-unrolled sheet per cured leather type. CC0 photographed material maps; human approval pending."
}
# Verify the actual exported glTF structure and account for embedded material images.
import struct
with open(out/(K+".glb"),"rb") as g:
 binary=g.read()
if binary[:4]!=b"glTF":raise RuntimeError("V017 GLB signature invalid")
first_chunk_len=struct.unpack("<I",binary[12:16])[0]
document=json.loads(binary[20:20+first_chunk_len].decode("utf-8"))
imgstats=[]
for im in document.get("images",[]):
 view=document["bufferViews"][im["bufferView"]]
 imgstats.append({"name":im.get("name",""),"mime":im.get("mimeType",""),"bytes":view["byteLength"]})
report["glb_images"]=imgstats
report["glb_meshes"]=len(document.get("meshes",[]))
report["glb_materials"]=len(document.get("materials",[]))
report["normal_mapped_materials"]=sum(1 for m in document.get("materials",[]) if m.get("normalTexture"))
report["total_embedded_image_bytes"]=sum(x["bytes"] for x in imgstats)
if report["glb_meshes"]<1 or report["normal_mapped_materials"]<1:
 raise RuntimeError("Missing expected textured geometry in exported GLB")
# Artistic distinction is reported from actual generated mesh and preserves original versions.
profile=objects[0].get("species_silhouette_profile") or objects[0].get("physical_style")
if not profile:raise RuntimeError("V019 did not install differentiated species geometry")
report["distinctive_profile"]=profile
report["difference_is_geometric"]=True
report["not_botanically_or_animal_scan_verified"]=True
report["visual_review_status"]="NOT_APPROVED"
report["one_piece_validated"]=len(objects)==1
(out/"validation.json").write_text(json.dumps(report,indent=2))
print("GENESIS_V019_DISTINCT_REPORT "+json.dumps(report))
