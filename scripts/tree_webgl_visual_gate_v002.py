"""Visual-gated nondestructive WebGL LOD pass for approved plaza trees.
Keep exact master GLBs unchanged. Only complete foliage cards are culled.
Screen-space transparent render comparison is a proxy, not a device-performance certificate.
"""
import sys,os,json,random,math
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
SPEC={
 'oak': ('assets/plaza_trees_v017/oak/oak_easytree_v017.glb',17017),
 'ash': ('assets/plaza_trees_v020/ash/ash_easytree_v020.glb',20020),
 'linden': ('assets/plaza_trees_v022/linden/linden_easytree_v022.glb',22022),
 'maple': ('assets/plaza_trees_v021/maple/maple_easytree_v021.glb',21021),
}
species=sys.argv[sys.argv.index('--')+1]
assert species in SPEC
src_name,seed=SPEC[species]
src=Path(src_name)
assert src.is_file(),src
out=Path('output/tree_webgl_v002')/species
out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
def reset():
 bpy.ops.object.select_all(action='SELECT')
 bpy.ops.object.delete(use_global=False)
def import_master():
 reset()
 bpy.ops.import_scene.gltf(filepath=str(src.resolve()))
 objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
 assert len(objs)>=2,('MESH_COUNT',len(objs))
 return objs
def tris(objs):
 return sum(len(p.vertices)-2 for o in objs for p in o.data.polygons)
def decimate_leaves(objs,ratio):
 affected=0
 for obj in objs:
  if 'foliage' not in obj.name.lower() and 'leaves' not in obj.name.lower():continue
  mesh=obj.data
  n=len(mesh.polygons)
  if n%2:raise RuntimeError('Leaf mesh does not have paired triangles: '+obj.name)
  rng=random.Random(seed)
  keep=set()
  for i in range(0,n,2):
   if rng.random()<ratio:keep.update((i,i+1))
  bm=bmesh.new();bm.from_mesh(mesh);bm.faces.ensure_lookup_table()
  discard=[bm.faces[i] for i in range(n) if i not in keep]
  bmesh.ops.delete(bm,geom=discard,context='FACES')
  bm.to_mesh(mesh);bm.free();mesh.update()
  affected+=n-len(keep)
 assert affected>0,('NO_LEAVES_REDUCED',ratio)
 return affected
def configure_scene(objs,focus,span):
 bpy.ops.object.select_all(action='DESELECT')
 world=bpy.data.worlds.new('WebGL compare World') if not bpy.context.scene.world else bpy.context.scene.world
 bpy.context.scene.world=world;world.use_nodes=True
 world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.72,.76,.80,1)
 world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.65
 for energy,pos in ((1900,Vector((span,-span*.7,span*1.4))),(900,Vector((-span,span,span*.9)))):
  bpy.ops.object.light_add(type='AREA',location=focus+pos)
  light=bpy.context.object;light.data.energy=energy;light.data.shape='DISK';light.data.size=span*.7
 bpy.ops.object.camera_add()
 cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=span*1.68
 scene=bpy.context.scene;scene.camera=cam
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16
 scene.cycles.use_denoising=True
 scene.render.film_transparent=True
 scene.view_settings.view_transform='Standard'
 scene.render.resolution_x=720;scene.render.resolution_y=720;scene.render.resolution_percentage=100
 scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
 return cam
def screenshot(cam,focus,span,view,name):
 direction=Vector((.65,-1,.40)) if view=='three_quarter' else Vector((0,-1,.28))
 cam.location=focus+direction.normalized()*span*2.9
 cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler()
 dst=out/(name+'_'+view+'.png')
 bpy.context.scene.render.filepath=str(dst.resolve())
 bpy.ops.render.render(write_still=True)
 im=bpy.data.images.load(str(dst.resolve()),check_existing=False)
 raw=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(raw)
 pixels=raw.reshape(im.size[1],im.size[0],4).copy()
 bpy.data.images.remove(im)
 return pixels
def diff(base,cand):
 am=base[:,:,3]>.10;bm=cand[:,:,3]>.10
 union=np.logical_or(am,bm)
 changed=np.logical_xor(am,bm)
 silhouette=(float(changed.sum())/float(max(1,union.sum())))*100
 # Mean per-channel absolute color difference of visible image content, in percent.
 # Pre-multiply by alpha to avoid transparent RGB artifacts.
 a=base[:,:,:3]*base[:,:,3:4];b=cand[:,:,:3]*cand[:,:,3:4]
 mae=float(np.abs(a-b)[union].mean())*100 if union.any() else 0.0
 return {'silhouette_change_pct':round(silhouette,4),'color_mae_pct':round(mae,4)}
master_objs=import_master()
baseline_triangles=tris(master_objs)
bounds=[o.matrix_world@Vector(c) for o in master_objs for c in o.bound_box]
minimum=Vector(tuple(min(p[i] for p in bounds) for i in range(3)))
maximum=Vector(tuple(max(p[i] for p in bounds) for i in range(3)))
focus=(minimum+maximum)/2;span=max(*(maximum-minimum),3)
cam=configure_scene(master_objs,focus,span)
base={v:screenshot(cam,focus,span,v,'master') for v in ('front','three_quarter')}
report={'species':species,'source':src_name,'baseline_triangles':baseline_triangles,'screen_comparison_px':720,'visual_change_limit_pct':1.5,'accepted':[],'rejected':[],'integration_approved':False}
candidates={'lod1':[.91,.94,.96,.98,.99],'lod2':[.82,.87,.91,.95,.975,.99]}
for name,ratios in candidates.items():
 passed=False
 for ratio in ratios:
  objs=import_master()
  removed=decimate_leaves(objs,ratio)
  newtri=tris(objs)
  cam=configure_scene(objs,focus,span)
  views={v:screenshot(cam,focus,span,v,'trial_'+name) for v in ('front','three_quarter')}
  metrics={v:diff(base[v],views[v]) for v in views}
  good=all(m['silhouette_change_pct']<=1.5 and m['color_mae_pct']<=1.5 for m in metrics.values())
  result={'lod':name,'retained_leaf_fraction':ratio,'triangles':newtri,'removed_triangles':baseline_triangles-newtri,'metrics':metrics,'passed_proxy_gate':good}
  print('LOD_CANDIDATE',json.dumps(result),flush=True)
  if good:
   # Export only selected meshes, never include studio cameras or lights.
   bpy.ops.object.select_all(action='DESELECT')
   for o in objs:o.select_set(True)
   bpy.context.view_layer.objects.active=objs[0]
   bpy.ops.export_scene.gltf(filepath=str((out/(name+'.glb')).resolve()),export_format='GLB',use_selection=True,export_lights=False,export_cameras=False)
   for v in ('front','three_quarter'):
    (out/('trial_'+name+'_'+v+'.png')).rename(out/(name+'_'+v+'.png'))
   result['bytes']=(out/(name+'.glb')).stat().st_size
   report['accepted'].append(result);passed=True;break
  report['rejected'].append(result)
 if not passed:print('WARNING no acceptable '+name+' under 1.5% render proxy; keep master',flush=True)
(out/'audit.json').write_text(json.dumps(report,indent=2))
print('LOD_FINAL',json.dumps(report),flush=True)
