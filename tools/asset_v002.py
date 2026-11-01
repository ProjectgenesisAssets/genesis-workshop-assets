#!/usr/bin/env python3
"""Genesis V002: distinct sculptural material geometry, scanned CC0 PBR, dual GLB export.
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
SCENE.cycles.samples=28
SCENE.render.resolution_x=900
SCENE.render.resolution_y=900
SCENE.render.resolution_percentage=100
SCENE.render.film_transparent=True
SCENE.render.image_settings.file_format="PNG"
SCENE.render.image_settings.color_mode="RGBA"
SCENE.view_settings.view_transform="Standard"
SCENE.view_settings.look="Medium High Contrast"
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
links.new(color_node.outputs["Color"],bs.inputs["Base Color"])
links.new(rough_node.outputs["Color"],bs.inputs["Roughness"])
normal_map=nodes.new("ShaderNodeNormalMap")
normal_map.inputs["Strength"].default_value=.72
links.new(normal_node.outputs["Color"],normal_map.inputs["Color"])
links.new(normal_map.outputs["Normal"],bs.inputs["Normal"])
# A split/cracked edge has its own dark wood core; hide thickness is integrated into the mesh.
wood_edge=bpy.data.materials.new("dry_wood_exposed_inner")
wood_edge.diffuse_color=(.24,.15,.08,1) if K=="dry-oak-wood" else (.48,.37,.24,1)
wood_edge.use_nodes=True
wood_edge.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=.94
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
 v=[];faces=[];mats=[]
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
   crack=.025*sin(f*13+2.7*t)+.012*sin(f*29-5*t)
   crack+=.026*(1 if oak else .42)*sin(t*13+f*24)
   section.append((crack,y))
  for i,(xx,yy) in enumerate(section):
   # Fibrils follow the grain axis, not uncorrelated vertex noise.
   end_damage=.026*(sin(i*3.71)**2) if j in (0,sections-1) else 0
   v.append((xx+offset*.017,yy,z+end_damage))
 n=len(section)
 for j in range(sections-1):
  for i in range(n):
   a=j*n+i;b=j*n+(i+1)%n
   faces.append((a,b,b+n,a+n));mats.append(0 if i<count_arc-1 else 1)
 faces.append(tuple(reversed(range(n))));mats.append(1)
 faces.append(tuple((sections-1)*n+i for i in range(n)));mats.append(1)
 ob=mesh(label,v,faces,mats=[mat,wood_edge],side_indices=mats)
 transform(ob,(offset*.27,offset*.07,0),(.05*offset,.08*offset,offset*.09))
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
   fold= .13*sin(u*7.7+sin(t*3.2)) if cow else .074*sin(u*13.5+t*6)
   crease= .07*math.exp(-((u-(.54+.08*sin(t*4)))/.083)**2)
   fine=(.013 if cow else .027)*sin(26*t+9*u)*sin(7*u)
   zz=.08+fold+crease+fine +.12*(u-.5)**2
   if not cow:zz+=.055*sin((u+t)*17)*math.exp(-((u-.77)/.16)**2)
   v.append((xx,yy,zz));uv.append((u,t))
 for j in range(ny-1):
  for i in range(nx-1):
   a=j*nx+i;faces.append((a,a+1,a+nx+1,a+nx))
 top=len(v)
 for x,y,z in v:v.append((x,y,z-thick))
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
   R=.13+.47*t if hemp else .10+.37*t
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
if K=="dry-oak-wood":
 wood_piece("oak_split_primary",True,-.7)
 wood_piece("oak_split_secondary",True,.7)
elif K=="dry-ash-wood":
 wood_piece("ash_split_primary",False,-.8)
 wood_piece("ash_split_secondary",False,.75)
elif K=="tanned-cowhide":hide(True)
elif K=="tanned-goatskin":hide(False)
elif K=="hemp-cord":cord(True)
else:cord(False)
# Keep floor, camera and lights out of exported GLB.
bpy.ops.object.camera_add(location=(2.7,-3.2,2.5))
camera=bpy.context.object
SCENE.camera=camera
camera.data.type="ORTHO"
camera.data.ortho_scale=2.35 if K.startswith("dry-") else (2.20 if K.startswith("tanned-") else 1.8)
for loc,power,size in [((3,-4,5),850,4.5),((-3,1,3.5),650,3.8),((.5,3,5),470,3)]:
 bpy.ops.object.light_add(type="AREA",location=loc)
 light=bpy.context.object;light.data.energy=power;light.data.shape="DISK";light.data.size=size
def render(view,point,scale=None):
 camera.location=point
 camera.rotation_euler=(Vector((0,0,0))-camera.location).to_track_quat("-Z","Y").to_euler()
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
for node,im in zip((color_node,rough_node,normal_node),original):
 small=im.copy()
 small.scale(1536,1536)
 small.filepath_raw=str((out/(im.name+"_1536.png")).resolve())
 small.file_format="PNG"
 small.save()
 node.image=small
export(out/(K+".glb"))
tris=sum(max(0,len(f.vertices)-2) for o in objects for f in o.data.polygons)
report={
 "asset":K,"version":"V002_candidate","objects":len(objects),
 "triangles_mesh":tris,"triangles_goal_under":30000,
 "master_bytes":(out/(K+"_master.glb")).stat().st_size,
 "glb_bytes":(out/(K+".glb")).stat().st_size,
 "master_texture_px":list(original[0].size),
 "web_texture_px":1536,
 "pbr_maps":["Color","Roughness","NormalGL"],
 "source_id":provenance["id"],
 "source_url":provenance["source_url"],
 "license":"CC0-1.0",
 "species_or_fiber_verified":provenance.get("species_or_fiber_verified",False),
 "quality_approved":False,
 "visual_score":None,
 "notes":"Experimental sculpted/procedural geometry with reference CC0 surface PBR. Species/provenance and artistic review pending."
}
(out/"validation.json").write_text(json.dumps(report,indent=2))
print("GENESIS_V002_REPORT "+json.dumps(report))
