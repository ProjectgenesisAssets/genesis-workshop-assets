"""Build REAL Project Genesis ash wood asset candidates from sourced Meshy geometry.
Run: blender -b -t 4 --python tools/build_ash_inventory_v01.py -- INPUT_DIR OUTPUT_DIR
All operations apply to independent copies. Sources are never overwritten.
"""
import bpy, math, sys, json, zipfile, os
from pathlib import Path
from mathutils import Matrix, Vector
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

inp=Path(sys.argv[sys.argv.index("--")+1]).resolve()
out=Path(sys.argv[sys.argv.index("--")+2]).resolve()
out.mkdir(exist_ok=True,parents=True)
tex=out/"textures";tex.mkdir(exist_ok=True)
models=out/"models";models.mkdir(exist_ok=True)
renders=out/"renders";renders.mkdir(exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def archive_image(label,filename,target,side=1536):
    p=inp/(label+"_pbr_4k.zip")
    assert p.is_file(),p
    with zipfile.ZipFile(p) as z:
        src=next((x for x in z.namelist() if x.endswith(filename)),None)
        assert src,f"{filename} not found in {p}"
        from io import BytesIO
        im=Image.open(BytesIO(z.read(src))).convert("RGB")
        im.thumbnail((side,side),Image.Resampling.LANCZOS)
        if label=="weathered_tree_bark" and filename.endswith("_color.jpg"):
            im=ImageEnhance.Color(im).enhance(.70)
            im=ImageEnhance.Brightness(im).enhance(.92)
        dst=tex/target
        im.save(dst,quality=92,subsampling=0)
        return dst

grain_color=archive_image("ash_wood_grain","_color.jpg","fresno_natural_color.jpg")
grain_norm=archive_image("ash_wood_grain","_normalgl.jpg","fresno_natural_normal.jpg")
grain_rough=archive_image("ash_wood_grain","_roughness.jpg","fresno_natural_roughness.jpg")
bark_color=archive_image("weathered_tree_bark","_color.jpg","corteza_fresno_color.jpg")
bark_norm=archive_image("weathered_tree_bark","_normalgl.jpg","corteza_fresno_normal.jpg")
bark_rough=archive_image("weathered_tree_bark","_roughness.jpg","corteza_fresno_roughness.jpg")

# Wood end-grain with NON-STRAIGHT concentric growth rings, realistic pore
# variation. Physically distinct from the longitudinal ash-grain PBR map.
rng=np.random.default_rng(451)
N=1024
yy,xx=np.mgrid[0:N,0:N].astype(np.float32)
X=(xx-N/2)/(N/2);Y=(yy-N/2)/(N/2)
a=np.arctan2(Y,X)
r=np.sqrt((X+.018*np.sin(7*a))**2+(Y+.022*np.cos(5*a))**2)
# Smooth distortions make growth rings organic rather than perfect circles.
d=.013*np.sin(3.7*a+9*r)+.009*np.cos(11*a-8*r)+.01*np.sin(16*r+.4*a)
phase=(r+d)*(19.5+1.8*np.sin(a*2.2)) + .09*np.sin(34*r+4*a)
annual=np.cos(2*np.pi*phase)
thin=np.power(np.clip(annual*.5+.5,0,1),9.0)
pores=rng.random((N,N),dtype=np.float32)
pore_mask=(pores>.996).astype(np.float32)
# Smooth knots and fine radial fibers; no square concentric mask.
fibers=np.sin(a*91 + 35*r + .7*np.sin(17*r))*.035
noise=rng.normal(0,1,(N,N)).astype(np.float32)*1.4
base=np.zeros((N,N,3),dtype=np.float32)
for k,c in enumerate([204,179,143]):
    base[:,:,k]=c*(1-.16*thin) - [14,16,17][k]*thin
base+=fibers[:,:,None]*12+noise[:,:,None]
base-=pore_mask[:,:,None]*rng.uniform(9,25,(N,N,1))
Image.fromarray(np.uint8(np.clip(base,0,255)),"RGB").save(tex/"fresno_corte_anillos.png",optimize=True)
# Micro normal from annual boundaries; exported as actual PBR normal texture.
height=thin*.18 + (.5+fibers)*.05
dzdy,dzdx=np.gradient(height)
nor=np.dstack((-dzdx*6,-dzdy*6,np.ones_like(height)))
nor/=np.linalg.norm(nor,axis=2)[:,:,None]
Image.fromarray(np.uint8(np.clip((nor*.5+.5)*255,0,255)),"RGB").save(tex/"fresno_corte_normal.png",optimize=True)

def image_node(nodes,label,path,noncolor=False):
    im=bpy.data.images.load(str(path),check_existing=True)
    if noncolor:im.colorspace_settings.name="Non-Color"
    img=nodes.new("ShaderNodeTexImage")
    img.name=label
    img.label=label
    img.image=im
    img.interpolation="Linear"
    img.extension="REPEAT"
    return img

def pbr(name,color,normal=None,rough=None,r=.81):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Metallic"].default_value=0.0
    bs.inputs["Roughness"].default_value=r
    bs.inputs["Base Color"].default_value=(.79,.69,.55,1)
    n=m.node_tree.nodes;l=m.node_tree.links
    c=image_node(n,name+" · COLOR",color)
    c.location=(-700,240);l.new(c.outputs["Color"],bs.inputs["Base Color"])
    if normal is not None:
        i=image_node(n,name+" · NORMAL",normal,True)
        i.location=(-700,-80)
        nm=n.new("ShaderNodeNormalMap");nm.location=(-420,-65)
        nm.inputs["Strength"].default_value=.68
        l.new(i.outputs["Color"],nm.inputs["Color"])
        l.new(nm.outputs["Normal"],bs.inputs["Normal"])
    if rough is not None:
        i=image_node(n,name+" · ROUGHNESS",rough,True)
        i.location=(-700,-350)
        l.new(i.outputs["Color"],bs.inputs["Roughness"])
    return m
wood=pbr("Fresno · madera natural veta longitudinal PBR",grain_color,grain_norm,grain_rough,.77)
bark=pbr("Fresno · corteza gris PBR",bark_color,bark_norm,bark_rough,.89)
end=pbr("Fresno · testa anillos de crecimiento",tex/"fresno_corte_anillos.png",tex/"fresno_corte_normal.png",None,.84)

def cleanup_source(scene_name,file_path,decimate=1,target_length=1.22):
    existing=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(file_path))
    meshes=[o for o in bpy.data.objects if o not in existing and o.type=="MESH"]
    assert meshes,f"No geometry: {file_path}"
    obj=max(meshes,key=lambda o:len(o.data.polygons))
    for other in meshes:
        if other!=obj:bpy.data.objects.remove(other,do_unlink=True)
    obj.name=scene_name
    obj.parent=None
    # Bake GLTF Y-up -> Blender coordinate transform (including source scale).
    world=obj.matrix_world.copy()
    obj.data.transform(world)
    obj.matrix_world=Matrix.Identity(4)
    obj.data.update()
    # Rotate the longest axis to X. Do not distort shape by nonuniform scaling.
    v=np.asarray([v.co[:] for v in obj.data.vertices],dtype=np.float32)
    sizes=np.ptp(v,axis=0)
    major=int(np.argmax(sizes))
    if major==1:
        obj.data.transform(Matrix.Rotation(math.pi/2,4,"Z"))
    elif major==2:
        obj.data.transform(Matrix.Rotation(math.pi/2,4,"Y"))
    v=np.asarray([p.co[:] for p in obj.data.vertices],dtype=np.float32)
    s=target_length/(float(v[:,0].max()-v[:,0].min())+1e-10)
    obj.data.transform(Matrix.Scale(s,4))
    # Align bbox in space for a horizontal timber inventory presentation.
    v=np.asarray([p.co[:] for p in obj.data.vertices],dtype=np.float32)
    mn=v.min(axis=0);mx=v.max(axis=0)
    obj.data.transform(Matrix.Translation(Vector((float(-(mn[0]+mx[0])/2),float(-(mn[1]+mx[1])/2),float(-mn[2])))))
    obj.data.update()
    orig=len(obj.data.polygons)
    if decimate<1.0:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True);bpy.context.view_layer.objects.active=obj
        mod=obj.modifiers.new("Non-destructive candidate remesh","DECIMATE")
        mod.ratio=decimate
        mod.use_collapse_triangulate=True
        bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.data.materials.clear()
    obj.data.materials.append(bark if scene_name=="Tronco de fresno" else wood)
    obj.data.materials.append(end)
    obj.data.update()
    return obj,orig

def classify_and_map(obj,is_log):
    mesh=obj.data
    uv=mesh.uv_layers.get("FresnoUV") or mesh.uv_layers.new(name="FresnoUV")
    coords=np.asarray([v.co[:] for v in mesh.vertices])
    mn=coords.min(axis=0);mx=coords.max(axis=0)
    length=max(mx[0]-mn[0],1e-6)
    cy=(mn[1]+mx[1])*0.5;cz=(mn[2]+mx[2])*0.5
    ry=max(mx[1]-mn[1],1e-6);rz=max(mx[2]-mn[2],1e-6)
    ends=0
    for polygon in mesh.polygons:
        n=polygon.normal;cx=polygon.center.x
        cap=(abs(n.x)>.70 and (cx<mn[0]+.09*length or cx>mx[0]-.09*length))
        polygon.material_index=1 if cap else 0
        if cap:ends+=1
        loops=list(polygon.loop_indices)
        uvals=[]
        for index in loops:
            v=mesh.vertices[mesh.loops[index].vertex_index].co
            if cap:
                u=.5+.44*(v.y-cy)/(ry*.5)
                vv=.5+.44*(v.z-cz)/(rz*.5)
            elif is_log:
                u=.5+math.atan2(v.z-cz,v.y-cy)/(2*math.pi)
                vv=(v.x-mn[0])/length*1.6
            else:
                cross=v.y if abs(n.z)>abs(n.y) else v.z
                minor=1 if abs(n.z)>abs(n.y) else 2
                u=(cross-mn[minor])/(max(mx[minor]-mn[minor],1e-6))*.9
                vv=(v.x-mn[0])/length*1.5
            uvals.append((u,vv))
        # Wrap cylindrical seam by polygon, not vertex: no long stretched
        # bark triangle across texture U=0/1.
        if is_log and not cap:
            lo=min(t[0] for t in uvals);hi=max(t[0] for t in uvals)
            if hi-lo>.5:
                uvals=[(u+1 if u<.5 else u,vv) for u,vv in uvals]
        for li,coord in zip(loops,uvals):
            uv.data[li].uv=coord
    print("UV_MAPPED",obj.name,"faces",len(mesh.polygons),"endfaces",ends,
          "bbox",mn.tolist(),mx.tolist(),flush=True)
    return {"triangles":len(mesh.polygons),"endfaces":ends,"bbox_m":[mn.tolist(),mx.tolist()]}

def export_glb(obj,path):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.gltf(filepath=str(path),export_format="GLB",
        use_selection=True,export_texcoords=True,export_normals=True,export_materials="EXPORT",
        export_apply=False)
    print("EXPORT",path,str(path.stat().st_size),flush=True)

log,log_tris=cleanup_source("Tronco de fresno",inp/"ash_log_single.glb",.55,1.06)
boards,board_tris=cleanup_source("Tablas de fresno",inp/"ash_planks_stack.glb",1,1.38)
log_info=classify_and_map(log,True)
board_info=classify_and_map(boards,False)
export_glb(log,models/"ProjectGenesis_Tronco_Fresno_V01.glb")
export_glb(boards,models/"ProjectGenesis_Tablas_Fresno_V01.glb")

# Neutral studio with physical contact shadows; NOT a 2D concept image.
studio=bpy.data.worlds.new("Soft neutral studio")
bpy.context.scene.world=studio
studio.use_nodes=True
studio.node_tree.nodes["Background"].inputs["Color"].default_value=(.32,.36,.40,1)
studio.node_tree.nodes["Background"].inputs["Strength"].default_value=.8
floor_mat=bpy.data.materials.new("Matte studio stone")
floor_mat.diffuse_color=(.14,.16,.18,1)
floor_mat.use_nodes=True
fbs=floor_mat.node_tree.nodes.get("Principled BSDF")
fbs.inputs["Base Color"].default_value=(.18,.205,.23,1)
fbs.inputs["Roughness"].default_value=.94
bpy.ops.mesh.primitive_plane_add(size=200)
floor=bpy.context.object
floor.name="Studio floor - not part of GLB"
floor.data.materials.append(floor_mat)
floor.location.z=-.013
for name,pos,energy,size in [
    ("Large softbox",(-2.5,-3,6),750,4.2),
    ("Fill", (3,-2,3),480,4),
    ("Rim", (1.5,3,5),900,3)]:
    light=bpy.data.lights.new(name,"AREA")
    ob=bpy.data.objects.new(name,light)
    bpy.context.collection.objects.link(ob)
    ob.location=pos
    ob.rotation_euler=(Vector((0,0,.15))-ob.location).to_track_quat("-Z","Y").to_euler()
    light.energy=energy;light.shape="DISK";light.size=size
bpy.ops.object.camera_add()
camera=bpy.context.object
bpy.context.scene.camera=camera
camera.data.type="ORTHO"
scene=bpy.context.scene
scene.render.engine="CYCLES"
scene.cycles.samples=36
scene.cycles.device="CPU"
scene.render.threads_mode="FIXED";scene.render.threads=4
scene.view_layers[0].cycles.use_denoising=False
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
scene.view_settings.view_transform="AgX"
scene.render.resolution_percentage=100
scene.render.resolution_x=1080;scene.render.resolution_y=820

def render(o,name,azimuth,elevation,scale):
    for obj in (log,boards):obj.hide_render=obj!=o
    a=math.radians(azimuth);e=math.radians(elevation)
    center=Vector((0,0,.16))
    camera.location=center+Vector((math.sin(a)*math.cos(e)*3.4,-math.cos(a)*math.cos(e)*3.4,math.sin(e)*3.4))
    camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler()
    camera.data.ortho_scale=scale
    scene.render.filepath=str(renders/name)
    bpy.ops.render.render(write_still=True)
    print("RENDER",name,flush=True)

render(log,"Tronco_Fresno_V01_tres_cuartos.png",37,23,1.85)
render(log,"Tronco_Fresno_V01_extremo_y_corteza.png",70,22,1.80)
render(boards,"Tablas_Fresno_V01_tres_cuartos.png",36,23,2.15)
render(boards,"Tablas_Fresno_V01_cantos.png",75,25,2.18)

report={"source_geometry":{"log_source_triangles":log_tris,"boards_source_triangles":board_tris},
    "produced":{"log":log_info,"boards":board_info},
    "source_files":["ash_log_single.glb","ash_planks_stack.glb"],
    "materials":["fresno_natural PBR", "corteza envejecida PBR","endgrain procedural ring color and normal"],
    "caveat":"First visual candidates. Inspect ring geometry, bark scale and plank UV in real rendered images; no game integration."}
(out/"asset_report.json").write_text(json.dumps(report,indent=2))
print("COMPLETE",json.dumps(report),flush=True)
