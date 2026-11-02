"""Fast REAL Blender / Cycles HDRI render of actual warmed ash planks GLB.
Quality preview only, EXR remains full 32-bit float. No generated imagery.
"""
import bpy,sys,math,json,struct
from pathlib import Path
from mathutils import Vector
src=Path(sys.argv[sys.argv.index('--')+1]).resolve()
out=Path(sys.argv[sys.argv.index('--')+2]).resolve()
out.mkdir(parents=True,exist_ok=True)
assert (src/'ProjectGenesis_Tablas_Fresno_V03_Calido_HDRI.glb').exists()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(src/'ProjectGenesis_Tablas_Fresno_V03_Calido_HDRI.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert len(meshes)==1,len(meshes)
boards=meshes[0]
assert sum(len(p.vertices)-2 for p in boards.data.polygons)==10000
print('REAL_GLTF_IMPORTED_10K',len(boards.data.materials),len(boards.data.uv_layers),flush=True)
world=bpy.data.worlds.new('Actual studio HDRI PolyHaven 32-bit RGBE')
world.use_nodes=True
nodes=world.node_tree.nodes;nodes.clear()
env=nodes.new('ShaderNodeTexEnvironment')
env.image=bpy.data.images.load(str(src/'studio_small_09_2k.hdr'))
assert env.image.depth>=24
bg=nodes.new('ShaderNodeBackground')
bg.inputs['Strength'].default_value=.44
output=nodes.new('ShaderNodeOutputWorld')
world.node_tree.links.new(env.outputs['Color'],bg.inputs['Color'])
world.node_tree.links.new(bg.outputs['Background'],output.inputs['Surface'])
scene=bpy.context.scene;scene.world=world
mat=bpy.data.materials.new('Neutral matte studio floor');mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF')
bs.inputs['Base Color'].default_value=(.075,.083,.093,1)
bs.inputs['Roughness'].default_value=.92
bpy.ops.mesh.primitive_plane_add(size=200)
plane=bpy.context.object;plane.location.z=-.016;plane.data.materials.append(mat)
def softbox(pos,power,size):
    ld=bpy.data.lights.new('Area softbox','AREA');ob=bpy.data.objects.new('Area softbox',ld)
    bpy.context.collection.objects.link(ob)
    ob.location=pos;ob.rotation_euler=(Vector((0,0,.12))-ob.location).to_track_quat('-Z','Y').to_euler()
    ld.energy=power;ld.size=size
softbox((-2.5,-3,4.3),290,4.5)
softbox((3.0,0.5,3.5),125,3.8)
bpy.ops.object.camera_add()
camera=bpy.context.object
scene.camera=camera
camera.data.type='ORTHO'
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=18
scene.render.threads_mode='FIXED'
scene.render.threads=4
scene.view_layers[0].cycles.use_denoising=False
scene.render.resolution_x=960
scene.render.resolution_y=720
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-.40
scene.view_settings.gamma=1
scene.render.image_settings.file_format='OPEN_EXR'
scene.render.image_settings.color_mode='RGBA'
scene.render.image_settings.color_depth='32'
scene.render.image_settings.exr_codec='ZIP'
for name,a_deg,e_deg,ortho in (('Tablas_Fresno_V03_HDR32_3cuartos',38,26,2.06),
                               ('Tablas_Fresno_V03_HDR32_cantos',74,24,2.08)):
    az=math.radians(a_deg);e=math.radians(e_deg)
    focus=Vector((0,0,.12))
    camera.location=focus+Vector((math.sin(az)*math.cos(e)*3.8,-math.cos(az)*math.cos(e)*3.8,math.sin(e)*3.8))
    camera.rotation_euler=(focus-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=ortho
    scene.render.image_settings.file_format='OPEN_EXR'
    scene.render.image_settings.color_depth='32'
    scene.render.filepath=str(out/(name+'.exr'))
    bpy.ops.render.render(write_still=True)
    assert (out/(name+'.exr')).is_file()
    # Save display-oriented PNG from exactly the same render in Blender.
    scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGBA'
    scene.render.image_settings.color_depth='8'
    bpy.data.images['Render Result'].save_render(str(out/(name+'.png')),scene=scene)
    print('REAL_32_BIT_HDRI_DONE',name,(out/(name+'.exr')).stat().st_size,(out/(name+'.png')).stat().st_size,flush=True)
(out/'metadata.json').write_text(json.dumps({'source_model':str(src/'ProjectGenesis_Tablas_Fresno_V03_Calido_HDRI.glb'),
    'triangles':10000,'real_HDRI':'Poly Haven Studio Small 09 CC0 RGBE','samples':18,
    'master_format':'32-bit/channel OpenEXR','preview':'AgX PNG from same render'},indent=2))
