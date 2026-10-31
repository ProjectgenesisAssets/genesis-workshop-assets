# Project Genesis — V008 charcoal from real CC0 photographic wood geometry/PBR.
# Source: Poly Haven Dead Tree Trunk 02 (Jenelle van Heerden / Rico Cilliers, CC0).
# Authentically scanned fibrous topology; our color treatment simulates carbonization.
# CANDIDATE ONLY. Never overwrite approved game assets.
import bpy, bmesh, json, math, hashlib, urllib.request
import numpy as np
from pathlib import Path
from mathutils import Vector

SOURCE=Path("output_charcoal_scan_v005/wood_cc0_scan.blend").resolve()
OUT=Path("output_charcoal_v008_photoscan").resolve();OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
obj=next((x for x in bpy.data.objects if x.type=='MESH' and x.name.endswith('LOD0')),None)
if obj is None: raise RuntimeError("LOD0 scan missing")

# Keep real scanned surface only. Remove alternative LODs and staging elements.
for x in list(bpy.data.objects):
    if x!=obj: bpy.data.objects.remove(x,do_unlink=True)
# Physically cut a broken 1.5-metre segment near the naturally jagged right end.
bm=bmesh.new();bm.from_mesh(obj.data)
cut=bmesh.ops.bisect_plane(bm,
    geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
    plane_co=Vector((.97,0,0)),plane_no=Vector((1,0,0)),
    clear_inner=True,clear_outer=False,dist=.0001)
bm.to_mesh(obj.data);bm.free();obj.data.update()
if len(obj.data.vertices)<1000:raise RuntimeError("Scan crop lost geometry")
# Preserve original scanned UVs; geometric surface already reflects real wood fibres.
pts=[obj.matrix_world@v.co for v in obj.data.vertices]
lo=Vector([min(p[i] for p in pts) for i in range(3)])
hi=Vector([max(p[i] for p in pts) for i in range(3)])
centre=(lo+hi)/2
scale=2.0/max((hi-lo)[i] for i in range(3))
for v in obj.data.vertices: v.co=(obj.matrix_world@v.co-centre)*scale
obj.matrix_world.identity()
obj.name="PG_Charcoal_Photoscan_Hero_V008"
# Official CC0 scan maps already downloaded by the system Python requests step.
scan_diff=str(OUT/'original_realwood_scan_color_2k.jpg')
scan_normal=str(OUT/'original_realwood_scan_normal_2k.png')
scan_rough=str(OUT/'original_realwood_scan_roughness_2k.png')
for path in [scan_diff,scan_normal,scan_rough]:
    if Path(path).stat().st_size<4096: raise RuntimeError('missing local scan map: '+path)
src_im=bpy.data.images.load(scan_diff,check_existing=False)
w,h=src_im.size
p=np.empty(w*h*4,dtype=np.float32);src_im.pixels.foreach_get(p)
v=p.reshape(h,w,4)
# Retain photographic luminosity/wood grain, but make it wood CHARCOAL.
luma=.2126*v[:,:,0]+.7152*v[:,:,1]+.0722*v[:,:,2]
grain=np.clip(.019+.078*np.power(luma,.88),.015,.085)
carbon=np.empty_like(v)
carbon[:,:,0]=grain*.92;carbon[:,:,1]=grain*.95;carbon[:,:,2]=grain*1.035
carbon[:,:,3]=1
char_im=bpy.data.images.new('CC0_scanned_wood_carbonized_basecolor_2k',w,h,alpha=True,float_buffer=False)
char_im.pixels.foreach_set(carbon.ravel())
char_im.filepath_raw=str(OUT/'PG_Charcoal_V008_CC0_ScanCarbonized_BaseColor_2k.png')
char_im.file_format='PNG';char_im.save();char_im.pack()
n_im=bpy.data.images.load(scan_normal,check_existing=False)
r_im=bpy.data.images.load(scan_rough,check_existing=False)
n_im.colorspace_settings.name='Non-Color'
r_im.colorspace_settings.name='Non-Color'
n_im.pack()
# Carbonized wood is extremely matte, but retains wood-scanned roughness variations.
rw,rh=r_im.size
rough_src=np.empty(rw*rh*4,dtype=np.float32)
r_im.pixels.foreach_get(rough_src)
rough_raw=rough_src.reshape(rh,rw,4)
rough_mean=(rough_raw[:,:,0]+rough_raw[:,:,1]+rough_raw[:,:,2])/3
rough_dst=np.zeros_like(rough_raw)
rough_val=np.clip(.87+.115*rough_mean,.85,.99)
rough_dst[:,:,:3]=rough_val[:,:,None];rough_dst[:,:,3]=1
rough_carbon=bpy.data.images.new('PG_Charcoal_Carbonized_Roughness_2K',rw,rh,alpha=True,float_buffer=False)
rough_carbon.pixels.foreach_set(rough_dst.ravel())
rough_carbon.filepath_raw=str(OUT/'PG_Charcoal_V008_Carbonized_Roughness_2K.png')
rough_carbon.file_format='PNG';rough_carbon.save()
rough_carbon.colorspace_settings.name='Non-Color';rough_carbon.pack()
r_im=rough_carbon
mat=bpy.data.materials.new('CC0_Photoscan_Carbonized_Hardwood_PBR_2k')
mat.use_nodes=True
nodes=mat.node_tree.nodes;nodes.clear()
bs=nodes.new('ShaderNodeBsdfPrincipled');bs.inputs['Metallic'].default_value=0
bs.inputs['Specular IOR Level'].default_value=.17
out=nodes.new('ShaderNodeOutputMaterial')
mat.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
def tex(name,im):
    t=nodes.new('ShaderNodeTexImage');t.name=name;t.image=im;return t
mat.node_tree.links.new(tex('Carbonized scanned albedo',char_im).outputs['Color'],bs.inputs['Base Color'])
norm=nodes.new('ShaderNodeNormalMap');norm.inputs['Strength'].default_value=.98
mat.node_tree.links.new(tex('Real scan normals',n_im).outputs['Color'],norm.inputs['Color'])
mat.node_tree.links.new(norm.outputs['Normal'],bs.inputs['Normal'])
mat.node_tree.links.new(tex('Real scan roughness',r_im).outputs['Color'],bs.inputs['Roughness'])
obj.data.materials.clear();obj.data.materials.append(mat)
for poly in obj.data.polygons: poly.material_index=0
# Stage is light-only with alpha; no artificial red emissive and no stone shader.
world=bpy.context.scene.world or bpy.data.worlds.new('Black carbon render world')
bpy.context.scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.25,.26,.28,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.21
def area(name,pos,power,size):
    ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.shape='DISK';ld.size=size
    o=bpy.data.objects.new(name,ld);bpy.context.collection.objects.link(o)
    o.location=pos;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
area('Key', (2,-3,3.5),275,3.4)
area('Rake', (-2,2.5,3),390,2.5)
area('Fill',(-3,-2,-1),105,4)
data_cam=bpy.data.cameras.new('QA camera');data_cam.type='ORTHO'
cam=bpy.data.objects.new('QA camera',data_cam)
bpy.context.collection.objects.link(cam);bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=48
scene.render.resolution_x=1080;scene.render.resolution_y=1080
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.view_settings if False else None
scene.view_settings.exposure=-.28
for name,pos,scale in [
 ('three_quarter',(3.0,-3.9,2.4),2.9),
 ('side',(1,-5,1),2.8),
 ('broken_end',(5,-.6,.8),2.58),
 ('upper',(1.8,-2.4,4.0),2.85),
 ('macro_wood_fibre',(3.6,-3,1.8),1.45)
]:
    cam.location=pos;cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
    data_cam.ortho_scale=scale
    scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'PG_Charcoal_V008_Photoscan_Master.blend'))
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
bpy.context.view_layer.objects.active=obj
bpy.ops.export_scene.gltf(filepath=str(OUT/'PG_Charcoal_V008_Photoscan_Master.glb'),export_format='GLB',use_selection=True)
audit={'version':'V008','status':'PHOTO_SCAN_CARBON_V008_CANDIDATE_NOT_APPROVED',
       'license':'CC0 Poly Haven dead_tree_trunk_02 source + Project Genesis carbonization edit',
       'triangles':len(obj.data.polygons),
       'material':'CC0 scanned fibrous geometry, deeply charred albedo, 2k scan normals, physically modified charcoal roughness/low specular',
       'maps':{'color':char_im.filepath_raw,'original_normal':scan_normal,'original_roughness':scan_rough},
       'mesh_vertices':len(obj.data.vertices),'textures':list(src_im.size),
       'glb_size_bytes':(OUT/'PG_Charcoal_V008_Photoscan_Master.glb').stat().st_size,
       'provenance':'https://polyhaven.com/a/dead_tree_trunk_02',
       'needs_manual_art_approval':True}
(OUT/'AUDIT.json').write_text(json.dumps(audit,indent=2))
print('SCAN_CARBONIZED_V008',json.dumps(audit))
