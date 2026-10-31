# Project Genesis — Assemble charcoal firewood pile V009 from approved V008 scan.
# A candidate demo only; the original V008 model, texture and approved UI stay intact.
from pathlib import Path
import io, json, numpy as np, trimesh
from PIL import Image
from trimesh.visual.material import PBRMaterial
from trimesh.transformations import rotation_matrix

OUT=Path('output_charcoal_pile_v009');OUT.mkdir(exist_ok=True)
IN=Path('output_charcoal_v008_photoscan/PG_Charcoal_V008_Photoscan_Master.glb')
source=trimesh.load(IN,file_type='glb',force='scene')
mesh=next(iter(source.geometry.values()))
m=mesh.visual.material
webmesh=mesh.copy()
# Remap bitmap encoding only. The mesh/UVs and all original PBR details stay at 2K.
webmat=PBRMaterial(name='PG_Charcoal_V008_PBR_2K_shared_WEB')
for k in ('baseColorTexture','normalTexture','metallicRoughnessTexture'):
    image=getattr(m,k).convert('RGB')
    b=io.BytesIO()
    image.save(b,'JPEG',quality=96,subsampling=0,optimize=True)
    setattr(webmat,k,Image.open(io.BytesIO(b.getvalue())))
webmat.metallicFactor=0.0
webmat.roughnessFactor=1.0
webmat.doubleSided=True
webmesh.visual=trimesh.visual.TextureVisuals(uv=mesh.visual.uv.copy(),material=webmat)
specs=[
 {'name':'01_carbon_base','az':4.,'pitch':-22.,'roll':20.,'scale':.85,'radius':.27,'h':.53},
 {'name':'02_carbon_cross','az':94.,'pitch':-28.,'roll':-52.,'scale':.77,'radius':.31,'h':.54},
 {'name':'03_carbon_diagonal','az':193.,'pitch':-23.,'roll':96.,'scale':.72,'radius':.27,'h':.51},
 {'name':'04_carbon_support','az':278.,'pitch':-29.,'roll':171.,'scale':.79,'radius':.26,'h':.53},
]
def assemble(geo,path):
    scene=trimesh.Scene()
    name='Carbon_V008_Shared_Real_Scan_Geometry'
    scene.add_geometry(geo,geom_name=name,node_name='master_source_hidden')
    scene.graph.update(frame_to='master_source_hidden',frame_from=scene.graph.base_frame,
        matrix=np.diag([.00001,.00001,.00001,1]))
    for spec in specs:
        a=np.radians(spec['az'])
        M=rotation_matrix(a,[0,1,0]) @ rotation_matrix(np.radians(spec['pitch']),[0,0,1]) @ rotation_matrix(np.radians(spec['roll']),[1,0,0])
        M[:3,:3]*=spec['scale']
        M[:3,3]=[spec['radius']*np.cos(a),spec['h'],-spec['radius']*np.sin(a)]
        scene.graph.update(frame_to=spec['name'],frame_from=scene.graph.base_frame,
            matrix=M,geometry=name)
    path.write_bytes(scene.export(file_type='glb'))
    reloaded=trimesh.load(path,file_type='glb',force='scene')
    assert len(reloaded.geometry)==1
    assert len(reloaded.graph.nodes_geometry)==5
    return path.stat().st_size

hq=assemble(mesh,OUT/'PG_Charcoal_Pile_V009_HQ.glb')
web=assemble(webmesh,OUT/'PG_Charcoal_Pile_V009_WEB.glb')
audit={'asset':'PG_Charcoal_Pile_V009','source':'PG_Charcoal_Photoscan_Hero_V008',
'status':'candidate_not_approved',
'geometry':'four oriented instances of one original V008 real-scan wood geometry',
'original_source_intact':True,'model_nodes':4,'unique_meshes':1,
'triangles_per_mesh':len(mesh.faces),'rendered_triangles':4*len(mesh.faces),
'hq_bytes':hq,'web_bytes':web,'maps':'2K PBR reused; web JPEG Q96 non-subsampled',
'hover':'yaw -45 to 45; easing to 0 on pointer exit','pieces':specs}
(OUT/'AUDIT.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False))
print('V009_SUCCEEDED',json.dumps({k:v for k,v in audit.items() if k!='pieces'}))
