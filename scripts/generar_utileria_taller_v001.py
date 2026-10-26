# -*- coding: utf-8 -*-
"""Initial PlayCanvas blacksmith workshop props; each asset is separately exported."""
import bpy, sys, math, json, os
from pathlib import Path
from mathutils import Vector
valid={"mesa","estanteria","soporte_herramientas","carbonera"}
argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
assert len(argv)==1 and argv[0] in valid, argv
kind=argv[0]
root=Path(os.environ.get("GITHUB_WORKSPACE",os.getcwd()))
out=root/("output_taller_"+kind+"_v001");out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
def material(name,color,metal=0,rough=.8):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 bs=m.node_tree.nodes.get("Principled BSDF")
 bs.inputs["Base Color"].default_value=(*color,1)
 bs.inputs["Metallic"].default_value=metal;bs.inputs["Roughness"].default_value=rough
 return m
wood=[material("Roble_seco",(.245,.132,.066)),material("Roble_oscuro",(.17,.086,.041)),material("Tablon_gastado",(.28,.16,.084))]
iron=material("Hierro_forjado",(.08,.085,.084),.8,.58)
coal=material("Carbon_mate",(.025,.023,.019),0,.93)
def block(n,xyz,dims,mat,bevel=.012):
 bpy.ops.mesh.primitive_cube_add(size=1,location=xyz);o=bpy.context.object;o.name=n;o.dimensions=dims
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 if bevel:
  b=o.modifiers.new("Redondeo","BEVEL");b.width=bevel;b.segments=2
  o.modifiers.new("Normales","WEIGHTED_NORMAL")
 return o
def cylinder(n,xyz,radius,depth,mat,verts=12):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=radius,depth=depth,location=xyz)
 o=bpy.context.object;o.name=n;o.data.materials.append(mat);return o
if kind=="mesa":
 # Solid timber blacksmith's workbench, iron corner braces, scarred planks
 for j in range(4):block("Encimera_tablon_%d"%j,(0,-.32+j*.21,.92),(1.72,.203,.11),wood[j%3],.012)
 for x in (-.70,.70):
  for y in (-.27,.28):
   block("Pata_%.2f_%.2f"%(x,y),(x,y,.46),(.145,.145,.92),wood[1],.013)
 for z in (.20,.69):
  block("Travesano_%d"%int(z*100),(0,0,z),(1.45,.10,.09),wood[1])
 for x in (-.77,.77):block("Cantonera_%d"%int(x*100),(x,-.015,.94),(.043,.82,.024),iron,.005)
elif kind=="estanteria":
 for x in (-.73,.73):
  for y in (-.26,.26):block("Montante_%.2f_%.2f"%(x,y),(x,y,1.04),(.11,.11,2.08),wood[1])
 for level,z in enumerate((.25,.80,1.36,1.94)):
  for j in range(3):block("Tabla_%d_%d"%(level,j),(0,-.22+j*.22,z),(1.68,.21,.062),wood[(level+j)%3])
 for z in (.22,1.86):block("Refuerzo_posterior_%d"%int(z*100),(0,.31,z),(1.55,.047,.065),iron,.008)
elif kind=="soporte_herramientas":
 block("Tablero_mural",(0,.025,1.0),(1.55,.095,1.48),wood[0])
 for i in range(8):
  x=-.67+i*.19
  block("Liston_vertical_%d"%i,(x,-.043,1),(.03,.027,1.39),wood[1],.003)
 for row,z in enumerate((.52,1.03,1.52)):
  block("Riel_hierro_%d"%row,(0,-.079,z),(1.42,.032,.043),iron,.005)
  for j in range(4):
   x=-.56+j*.36
   cylinder("Gancho_%d_%d"%(row,j),(x,-.125,z),.014,.09,iron,10)
elif kind=="carbonera":
 # Four-sided wooden storage box with dark visible charcoal pieces.
 block("Fondo",(0,0,.10),(1.0,.72,.10),wood[1])
 for x in (-.48,.48):block("Costado_x%d"%int(x*100),(x,0,.37),(.07,.72,.52),wood[0])
 for y in (-.33,.33):block("Costado_y%d"%int(y*100),(0,y,.37),(.96,.065,.52),wood[2])
 for z in (.17,.54):
  for y in (-.345,.345):block("Zuncho_%d_%d"%(int(z*100),int(y*100)),(0,y,z),(.98,.017,.028),iron,.004)
 for i in range(28):
  x=((i*17)%23)/23*.78-.39;y=((i*11)%19)/19*.48-.24;z=.57+(i%5)*.02
  block("Carbon_%02d"%i,(x,y,z),(.085+(i%3)*.014,.055,.045),coal,.009)
bpy.context.view_layer.update()
meshes=[o for o in bpy.data.objects if o.type=="MESH"]
tris=sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons)
assert tris < 6000,tris
name="Taller_"+kind.capitalize()+"_V001"
bpy.ops.wm.save_as_mainfile(filepath=str(out/(name+".blend")))
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
bpy.ops.export_scene.gltf(filepath=str(out/(name+".glb")),export_format="GLB",use_selection=True,export_apply=False)
(out/(name+"_AUDIT.json")).write_text(json.dumps({"asset":name,"status":"VISUAL_CANDIDATE_NOT_APPROVED","triangles":tris,"meshes":len(meshes),"target":"PlayCanvas/WebGL"},indent=2))
# Separate cameras/lights from asset export.
sc=bpy.context.scene;sc.render.engine="CYCLES";sc.cycles.device="CPU";sc.cycles.samples=12;sc.view_layers[0].cycles.use_denoising=False;sc.render.image_settings.file_format="PNG"
sc.render.resolution_x=900;sc.render.resolution_y=900;sc.render.resolution_percentage=100
world=bpy.data.worlds.new("Estudio");sc.world=world;world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.5
ld=bpy.data.lights.new("Luz","AREA");lo=bpy.data.objects.new("Luz",ld);bpy.context.collection.objects.link(lo);lo.location=(2,-3,4);ld.energy=600;ld.size=4
def point(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()
point(lo,(0,0,1))
camd=bpy.data.cameras.new("Camara");cam=bpy.data.objects.new("Camara",camd);bpy.context.collection.objects.link(cam);sc.camera=cam
camd.type="ORTHO";camd.ortho_scale=3.3
for angle,pos in (("Frontal",(0,-4.8,2)),("TresCuartos",(3.4,-4.4,2.7)),("Lateral",(4.8,0,2.1))):
 cam.location=pos;point(cam,(0,0,.95))
 sc.render.filepath=str(out/(name+"_"+angle+".png"))
 bpy.ops.render.render(write_still=True)
print("ASSET_SUCCESS",name,tris,flush=True)
