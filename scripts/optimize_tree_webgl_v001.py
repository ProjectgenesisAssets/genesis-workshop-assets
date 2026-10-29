"""Non-destructive WebGL LOD test: decimate only leaf cards from existing GLB."""
import bpy,json,sys
from pathlib import Path
src=Path(sys.argv[sys.argv.index('--')+1]);out=Path(sys.argv[sys.argv.index('--')+2])
out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(src.resolve()))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert meshes,'No meshes in GLB'
baseline=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes)
results=[]
for label,ratio in [('lod1',0.58),('lod2',0.22)]:
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(src.resolve()))
    for obj in [o for o in bpy.context.scene.objects if o.type=='MESH']:
        if 'foliage' not in obj.name.lower() and 'leaves' not in obj.name.lower():continue
        # Remove complete leaf cards by selecting face pairs, preserving UV/alpha and avoiding broken leaf triangles.
        mesh=obj.data
        polys=list(mesh.polygons)
        assert len(polys)%2==0,'Expected paired leaf triangles'
        keep=set()
        import random
        rng=random.Random(17017)
        for i in range(0,len(polys),2):
            if rng.random()<ratio:keep.update((i,i+1))
        import bmesh
        bm=bmesh.new();bm.from_mesh(mesh);bm.faces.ensure_lookup_table()
        drop=[bm.faces[i] for i in range(len(polys)) if i not in keep]
        bmesh.ops.delete(bm,geom=drop,context='FACES')
        bm.to_mesh(mesh);bm.free();mesh.update()
    bpy.ops.export_scene.gltf(filepath=str((out/(label+'.glb')).resolve()),export_format='GLB')
    tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in bpy.context.scene.objects if o.type=='MESH')
    results.append({'lod':label,'triangles':tris,'bytes':(out/(label+'.glb')).stat().st_size})
(out/'audit.json').write_text(json.dumps({'baseline_triangles':baseline,'lods':results},indent=2))
print('WEBGL_LOD_AUDIT',json.dumps(results))
