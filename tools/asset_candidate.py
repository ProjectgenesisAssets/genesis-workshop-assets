import bpy, math, random, os, json
from mathutils import Vector
from math import sin,cos,pi
import numpy as np
K=os.environ.get("ASSET_KIND","dry-oak-wood")
OUT=os.path.abspath("output/"+K); os.makedirs(OUT,exist_ok=True)
random.seed(20261031)
bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
def material(name,base,rough=0.83):
 m=bpy.data.materials.new(name);m.diffuse_color=(*base,1);m.use_nodes=True
 bs=m.node_tree.nodes.get("Principled BSDF"); bs.inputs["Base Color"].default_value=(*base,1);bs.inputs["Roughness"].default_value=rough
 return m
def mesh(name,verts,faces,mat):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
 ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);ob.data.materials.append(mat)
 for p in me.polygons:p.use_smooth=True
 return ob
wood=K.startswith("dry-"); leather=K.startswith("tanned-"); cord=not wood and not leather
base={"dry-oak-wood":(.28,.17,.095),"dry-ash-wood":(.49,.34,.19),"tanned-cowhide":(.31,.135,.077),"tanned-goatskin":(.49,.27,.15),"hemp-cord":(.52,.40,.24),"linen-thread":(.73,.65,.47)}[K]
mat=material(K,base)
# PBR texture set: reproducible image maps, UV-compatible via generated UVs on wood/leather.
size=1024
y,x=np.mgrid[0:size,0:size].astype(np.float32);rng=np.random.default_rng(20261031)
grain=np.sin((x*0.21 + 5*np.sin(y*.012))*(1 if wood else .1))
noise=rng.normal(0,1,(size,size)).astype(np.float32)
detail=.62+.1*grain+.065*noise
if leather:detail=.77+.075*np.sin(x*.19)*np.sin(y*.21)+.05*noise
if cord:detail=.8+.10*np.cos(x*.55+y*.18)+.04*noise
detail=np.clip(detail,.22,1.2)
def tex(name,rgb):
 im=bpy.data.images.new(name,width=size,height=size,alpha=True)
 rgba=np.empty((size,size,4),dtype=np.float32)
 for c in range(3):rgba[:,:,c]=np.clip(rgb[c],0,1)
 rgba[:,:,3]=1
 im.pixels.foreach_set(rgba.ravel());im.filepath_raw=os.path.join(OUT,name+".png");im.file_format="PNG";im.save()
 return im
# Use a genuine downloaded CC0 surface scan, never silently substitute noise.
from pathlib import Path
import glob
scan_files=glob.glob(os.path.join("sources",K,"*"))
albedo=[s for s in scan_files if s.lower().endswith((".jpg",".jpeg",".png")) and any(tag in os.path.basename(s).lower() for tag in ("color","colour","albedo","diffuse"))]
if not albedo:
 raise RuntimeError("No real scanned albedo in sources/"+K+"; refusing placeholder")
color=bpy.data.images.load(os.path.abspath(albedo[0]),check_existing=True)
color.name=K+"_scanned_cc0_basecolor"

rough=tex(K+"_roughness", [np.clip(.75+.08*noise,0,1)]*3)
nodes=mat.node_tree.nodes; links=mat.node_tree.links
for label,im,space in [("Base",color,"sRGB"),("Rough",rough,"Non-Color")]:
 n=nodes.new("ShaderNodeTexImage");n.label=label;n.image=im;n.image.colorspace_settings.name=space
 links.new(n.outputs["Color"],nodes.get("Principled BSDF").inputs["Base Color" if label=="Base" else "Roughness"])
def uv_smart(ob):
 bpy.ops.object.select_all(action="DESELECT");ob.select_set(True);bpy.context.view_layer.objects.active=ob
 bpy.ops.object.mode_set(mode="EDIT");bpy.ops.mesh.select_all(action="SELECT");bpy.ops.uv.smart_project(island_margin=.025);bpy.ops.object.mode_set(mode="OBJECT")
if wood:
 # Split longitudinal dry billet: tapered undulating cross section, separate end-grain rings.
 rings=32; sides=16;vs=[];fs=[]
 length=2.0 if K=="dry-oak-wood" else 1.75
 for j in range(rings):
  z=length*(j/(rings-1)-.5)
  for i in range(sides):
   a=i*2*pi/sides
   wav=.07*sin(3*a+z*2.5)+.045*sin(7*a-z*4.1)
   r=(.23 if K=="dry-oak-wood" else .19)*(1+wav+random.uniform(-.05,.05))
   # longitudinal split/fiber irregularity
   vs.append((r*cos(a),r*sin(a),z+.018*sin(a*5)))
 for j in range(rings-1):
  for i in range(sides):a=j*sides+i;b=j*sides+(i+1)%sides;fs.append((a,b,b+sides,a+sides))
 fs.extend([tuple(reversed(range(sides))),tuple((rings-1)*sides+i for i in range(sides))])
 ob=mesh("Fractured_dry_"+K,vs,fs,mat);uv_smart(ob)
elif leather:
 # Curled irregular hide, different relative thickness and grain response.
 N=32;vs=[];fs=[]
 for j in range(N):
  v=j/(N-1)
  for i in range(N):
   u=i/(N-1)
   edge=(.025*sin(19*u)+.04*sin(11*v))*((abs(u-.5)>.4) or (abs(v-.5)>.4))
   xx=(u-.5)*1.7+edge; yy=(v-.5)*1.4+edge
   zz=.11*sin(u*6+v*3)+.05*cos(v*13)+.055*(u-.5)**2
   if K=="tanned-goatskin":zz+=.085*sin(u*10+v*8)
   vs.append((xx,yy,zz))
 for j in range(N-1):
  for i in range(N-1):
   a=j*N+i;fs.append((a,a+1,a+1+N,a+N))
 ob=mesh("Tanned_hide_"+K,vs,fs,mat);uv_smart(ob)
 sol=ob.modifiers.new("Physical hide thickness","SOLIDIFY");sol.thickness=.027 if K=="tanned-cowhide" else .014
else:
 # Three helically twisted visible strands, low-cost tubular topology.
 def strand(idx):
  vs=[];fs=[];nr=140;ns=6;thick=.023 if K=="hemp-cord" else .011
  for j in range(nr):
   t=j/(nr-1);ang=idx*2*pi/3+2*pi*(11 if K=="hemp-cord" else 17)*t
   cx=.043*cos(ang);cy=.043*sin(ang);z=(t-.5)*1.6
   for i in range(ns):
    a=i*2*pi/ns
    vs.append((cx+thick*cos(a),cy+thick*sin(a),z))
  for j in range(nr-1):
   for i in range(ns):
    a=j*ns+i;b=j*ns+(i+1)%ns;fs.append((a,b,b+ns,a+ns))
  return mesh("Twisted_strand_%d"%idx,vs,fs,mat)
 for n in range(3):uv_smart(strand(n))
# Add basic scene for contact-sheet-quality evaluation render.
bpy.ops.object.camera_add(location=(2.6,-3.8,2.2));cam=bpy.context.object;direction=Vector((0,0,0))-cam.location;cam.rotation_euler=direction.to_track_quat("-Z","Y").to_euler();bpy.context.scene.camera=cam;cam.data.type="ORTHO";cam.data.ortho_scale=3.3
for loc,power,sz in [((3,-4,6),900,5),((-3,1,4),550,3)]:
 bpy.ops.object.light_add(type="AREA",location=loc);l=bpy.context.object;l.data.energy=power;l.data.shape="DISK";l.data.size=sz
scene=bpy.context.scene;scene.render.engine="CYCLES";scene.cycles.samples=24
scene.render.resolution_x=720;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.world.color=(.12,.12,.12)
for name,xyz in [("three_quarter",(2.6,-3.8,2.2)),("front",(0,-4,1)),("side",(4,0,1)),("top",(0,0,5))]:
 cam.location=xyz;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat("-Z","Y").to_euler()
 scene.render.filepath=os.path.join(OUT,name+".png");bpy.ops.render.render(write_still=True)
bpy.ops.object.select_all(action="DESELECT")
objs=[o for o in bpy.data.objects if o.type=="MESH"]
for o in objs:o.select_set(True)
bpy.context.view_layer.objects.active=objs[0]
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,K+".glb"),export_format="GLB",use_selection=True)
tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objs)
report={"asset":K,"version":"V001-prototype","triangles_mesh":tris,"objects":len(objs),"texture_px":size,"glb_bytes":os.stat(os.path.join(OUT,K+".glb")).st_size,"quality_approved":False,"note":"Procedural baseline; 4K scan-informed AAA master and independent visual validation pending."}
with open(os.path.join(OUT,"validation.json"),"w") as f:json.dump(report,f,indent=2)
print(json.dumps(report))
