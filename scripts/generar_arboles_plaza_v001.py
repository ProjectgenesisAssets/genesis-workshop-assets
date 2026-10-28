# Project Genesis - four original procedural plaza trees for PlayCanvas.
# Blender 4.5.13 LTS; no external models, textures or paid services.
import bpy, math, random, json, sys
from mathutils import Vector
from pathlib import Path

SPECIES = {
 'oak': dict(seed=101, name='Roble', height=7.0, trunk=.38, spread=1.45, leaf=4800, color=(.26,.38,.105), bend=.60),
 'ash': dict(seed=202, name='Fresno', height=8.2, trunk=.26, spread=1.06, leaf=3700, color=(.28,.43,.14), bend=.45),
 'maple': dict(seed=303, name='Arce', height=6.8, trunk=.32, spread=1.33, leaf=4400, color=(.55,.195,.064), bend=.52),
 'linden': dict(seed=404, name='Tilo', height=7.5, trunk=.34, spread=1.28, leaf=4900, color=(.25,.40,.115), bend=.52),
}
kind = sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'oak'
assert kind in SPECIES, kind
sp=SPECIES[kind]
rng=random.Random(sp['seed'])
out=Path('output_plaza_trees')/kind
out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def mat(name, color, rough=1):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=rough
    return m

bark=mat(kind+'_aged_bark',(.19,.135,.087),.95)
foliage=[]
for j,f in enumerate((.82,1.,1.14)):
    c=sp['color']
    foliage.append(mat(kind+'_leafshade_'+str(j),tuple(min(1,x*f) for x in c),.86))
barkverts=[];barkfaces=[];endpoints=[]

def tube(a,b,r0,r1,name='branch', sides=9):
    if (b-a).length < .005: return
    vec=(b-a).normalized()
    ref=Vector((0,0,1)) if abs(vec.z)<.9 else Vector((1,0,0))
    side=vec.cross(ref).normalized();side2=vec.cross(side).normalized()
    base=len(barkverts)
    for p,r in ((a,r0),(b,r1)):
        for i in range(sides):
            t=2*math.pi*i/sides
            barkverts.append(tuple(p + r*(math.cos(t)*side+math.sin(t)*side2)))
    for i in range(sides):
        ni=(i+1)%sides
        barkfaces.append((base+i,base+ni,base+sides+ni,base+sides+i))

# Structural twigs, organically asymmetric and reproducible.
def branch(a, direction, length, radius, depth):
    d=direction.normalized()
    midpoint=a+d*length*.52 + Vector((rng.uniform(-.09,.09),rng.uniform(-.09,.09),0))
    b=a+d*length + Vector((rng.uniform(-.12,.12),rng.uniform(-.12,.12),0))
    tube(a,midpoint,radius,radius*.78)
    tube(midpoint,b,radius*.78,radius*.58)
    if depth==0:
        endpoints.append((b,d))
        return
    forks=3 if depth>=2 else 2
    spin=rng.random()*2*math.pi
    for i in range(forks):
        angle=spin+(2*math.pi*i/forks)+rng.uniform(-.30,.30)
        horizontal=Vector((math.cos(angle), math.sin(angle),0))
        lean=.75 if depth>=3 else 1.15
        nd=(d*.72+horizontal*lean+Vector((0,0,.32))).normalized()
        if kind=='ash': nd.z=max(.33,nd.z);nd.normalize()
        branch(b,nd,length*rng.uniform(.57,.73),radius*.59,depth-1)

h=sp['height']
tube(Vector((0,0,0)),Vector((0,0,h*.25)),sp['trunk']*1.25,sp['trunk'],sides=13)
branch(Vector((0,0,h*.25)),Vector((.04,-.02,1)),h*.19,sp['trunk'],4)
# Low bark-root flares, sculpted as tapering offshoots rather than cylinder-only.
for i in range(7):
    t=2*math.pi*i/7+rng.random()*.25
    start=Vector((0,0,.36))
    end=Vector((math.cos(t)*sp['trunk']*1.65,math.sin(t)*sp['trunk']*1.65,.025))
    tube(start,end,sp['trunk']*.35,.015,sides=7)

bm=bpy.data.meshes.new(kind+'_bark_mesh')
bm.from_pydata(barkverts,[],barkfaces);bm.update()
bo=bpy.data.objects.new(kind+'_trunk_and_branches',bm)
bpy.context.collection.objects.link(bo);bm.materials.append(bark)
for p in bm.polygons: p.use_smooth=True

# Opaque leaf-shaped polygons: no alpha overdraw, no texture downloads.
# Each leaf is a slightly folded pentagon (4 triangles), lit on both sides.
lv=[];lf=[];li=[]
count=sp['leaf']
for i in range(count):
    anchor,twigd=endpoints[i%len(endpoints)]
    # Distribute over overlapping organic ellipsoids, not uniform spheres.
    az=rng.random()*2*math.pi
    u=rng.uniform(-1,1)
    rad=math.sqrt(max(0,1-u*u))*rng.random()**.43
    spread=sp['spread']*(.69 if kind=='ash' else 1)
    pos=anchor+Vector((math.cos(az)*rad*spread,math.sin(az)*rad*spread,u*spread*.72))
    # Ensure no foliage intersects ground, naturally raised crown.
    if pos.z<h*.41: pos.z=h*.41+rng.random()*.17
    length=rng.uniform(.085,.16) * (1.15 if kind=='oak' else 1)
    width=length*rng.uniform(.36,.54)
    normal=Vector((rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-.1,1))).normalized()
    a=normal.cross(Vector((0,0,1)))
    if a.length<.1: a=Vector((1,0,0))
    a.normalize()
    b=normal.cross(a).normalized()
    angle=rng.random()*2*math.pi
    a2=a*math.cos(angle)+b*math.sin(angle)
    b2=-a*math.sin(angle)+b*math.cos(angle)
    base=len(lv)
    # Petiole, shoulders, tip, far shoulder, middle vein ridge.
    for point in (pos-a2*length*.48,
                  pos-a2*length*.12+b2*width*.60,
                  pos+a2*length*.55,
                  pos-a2*length*.12-b2*width*.60,
                  pos+normal*length*.065):
        lv.append(tuple(point))
    shade=rng.randrange(3)
    for face in ((0,1,4),(1,2,4),(2,3,4),(3,0,4)):
        lf.append(tuple(base+k for k in face));li.append(shade)
lm=bpy.data.meshes.new(kind+'_leaf_geometry')
lm.from_pydata(lv,[],lf);lm.update()
for m in foliage: lm.materials.append(m)
for p,idx in zip(lm.polygons,li):p.material_index=idx;p.use_smooth=True
lo=bpy.data.objects.new(kind+'_individual_leaf_canopy',lm)
bpy.context.collection.objects.link(lo)

triangles=sum(len(p.vertices)-2 for mesh in (bm,lm) for p in mesh.polygons)
assert triangles<=60000,(kind,triangles)
audit={'species':kind,'tree_name':sp['name'],'triangles':triangles,'limit':60000,
       'bark_triangles':sum(len(p.vertices)-2 for p in bm.polygons),
       'leaf_triangles':len(lf),'individual_leaves':count,
       'materials':4,'source':'Original Blender procedural geometry (no third-party assets)',
       'engine':'PlayCanvas WebGL / glTF 2.0','status':'visual candidate; NOT art-approved'}
(out/'AUDIT.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False))
bpy.ops.wm.save_as_mainfile(filepath=str((out/(kind+'_plaza_v001.blend')).resolve()))
# Export meshes ONLY, not review studio lights or cameras.
bpy.ops.object.select_all(action='DESELECT')
bo.select_set(True);lo.select_set(True)
bpy.context.view_layer.objects.active=bo
bpy.ops.export_scene.gltf(filepath=str((out/(kind+'_plaza_v001.glb')).resolve()),
    export_format='GLB',use_selection=True,export_apply=True)

# Studio review: separate floor/lighting does not enter exported GLB.
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.mesh.primitive_plane_add(size=200)
ground=bpy.context.object;ground.name='REVIEW_ONLY_ground';ground.data.materials.append(mat('review_grass',(.20,.24,.14)))
def point_camera(target,position):
    bpy.ops.object.camera_add(location=position)
    cam=bpy.context.object;direction=Vector(target)-cam.location
    cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
    bpy.context.scene.camera=cam
    return cam
for loc,power,size in [((5,-5,11),1700,6),((-5,3,8),1100,7)]:
    bpy.ops.object.light_add(type='AREA',location=loc)
    light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.world.color=(.24,.26,.30)
cam=point_camera((0,0,h*.52),(h*1.05,-h*1.16,h*.72))
for name,xyz in [('front',(h*.02,-h*1.32,h*.62)),
                 ('three_quarter',(h*.95,-h*1.05,h*.75)),
                 ('side',(h*1.34,0,h*.67)),
                 ('rear',(0,h*1.30,h*.62))]:
    cam.location=xyz
    cam.rotation_euler=(Vector((0,0,h*.53))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str((out/(name+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
print('GENESIS_TREE_AUDIT',json.dumps(audit))
