# Project Genesis - inspect a genuine CC0 photogrammetry source before charcoal sculpt.
import bpy, json, math
from pathlib import Path
from mathutils import Vector
src=Path("output_charcoal_scan_v005/wood_cc0_scan.blend").resolve()
out=Path("output_charcoal_v005_scan_reference");out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(src))
ob_mesh=[o for o in bpy.data.objects if o.type=='MESH']
audit={'source':str(src),'objects':[], 'images':[], 'license':'CC0 Poly Haven Dead Tree Trunk 02','status':'scan_reference_not_charcoal_candidate'}
for o in sorted(ob_mesh,key=lambda x:len(x.data.polygons),reverse=True):
    ext=[tuple(o.matrix_world@Vector(c)) for c in o.bound_box]
    bbox=[(min(v[i] for v in ext),max(v[i] for v in ext)) for i in range(3)]
    audit['objects'].append({'name':o.name,'polygons':len(o.data.polygons),'bbox':bbox,'materials':[m.name if m else None for m in o.data.materials]})
for im in bpy.data.images:
    audit['images'].append({'name':im.name,'file':im.filepath,'packed':bool(im.packed_file),'size':list(im.size)})
if not ob_mesh: raise RuntimeError('No scanned geometry')
chosen=sorted(ob_mesh,key=lambda x:len(x.data.polygons),reverse=True)[0]
# Isolate the largest photogrammetric object for review
for ob in list(bpy.data.objects):
    if ob!=chosen:
        bpy.data.objects.remove(ob,do_unlink=True)
# Make scan upright in review coordinate system? preserve world rotation, center geometry.
worldpts=[chosen.matrix_world@Vector(v) for v in chosen.bound_box]
mins=[min(p[i] for p in worldpts) for i in range(3)]
maxs=[max(p[i] for p in worldpts) for i in range(3)]
center=Vector([(mins[i]+maxs[i])/2 for i in range(3)])
size=max(maxs[i]-mins[i] for i in range(3))
scale=2.15/max(.001,size)
# Bake world transform to geometry, center & scale.
for v in chosen.data.vertices:
    v.co=(chosen.matrix_world@v.co-center)*scale
chosen.matrix_world.identity()
chosen.name='PG_Scanned_Tree_CC0_Reference_V005'
audit['scan_scaled_long_axis']=['X','Y','Z'][max(range(3),key=lambda i:maxs[i]-mins[i])]
audit['size_source']=[maxs[i]-mins[i] for i in range(3)]
audit['source_vertex_count']=len(chosen.data.vertices)
# Preserve all real scanned normals/texture before deciding charcoal retexturing.
world=bpy.context.scene.world or bpy.data.worlds.new('Scan world')
bpy.context.scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.27,.29,.32,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.4
def area(pos,energy,size):
    ld=bpy.data.lights.new('SoftScanQA','AREA');ld.energy=energy;ld.shape='DISK';ld.size=size
    lo=bpy.data.objects.new('SoftScanQA',ld);bpy.context.collection.objects.link(lo)
    lo.location=pos;lo.rotation_euler=(-lo.location).to_track_quat('-Z','Y').to_euler()
for pos,pow,diam in [((2,-4,4),450,4),((-3,2,3),650,3),((0,3,-2),320,4)]:area(pos,pow,diam)
camera=bpy.data.cameras.new('Camera');camera.type='ORTHO';camera.ortho_scale=3.25
cam=bpy.data.objects.new('Camera',camera);bpy.context.collection.objects.link(cam);bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32
scene.render.resolution_x=950;scene.render.resolution_y=950
scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG'
for name,pos in [('three_quarter',(3.2,-4.7,2.8)),('side',(5,-1,1.2)),('top',(1,-3,5))]:
    cam.location=pos
    cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(out/(name+'.png'))
    bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str((out/'PG_RealWoodScan_V005_Reference.blend').resolve()))
(out/'AUDIT.json').write_text(json.dumps(audit,indent=2))
print('SCAN_AUDIT',json.dumps({k:v for k,v in audit.items() if k!='images'}))
