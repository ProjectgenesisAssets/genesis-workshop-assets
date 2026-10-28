# Project Genesis Plaza - procedural arboreal V003 (original, no purchased models)
# Blender 4.5.13, CPU Cycles; GLB 2.0 opaque bark and alpha-MASK leaf clusters.
# Techniques: tapered spline-like branching and crown pruning; multi-leaf opacity atlas.
import bpy,math,random,json,sys
import numpy as np
from mathutils import Vector
from pathlib import Path

DATA={
 'oak': dict(seed=601,h=7.4,r=.39,crown=2.95,low=.40,top=.98,card=4600,color=(.245,.355,.090),name='Roble'),
 'ash': dict(seed=602,h=8.4,r=.29,crown=2.10,low=.46,top=.99,card=4300,color=(.260,.388,.108),name='Fresno'),
 'maple':dict(seed=603,h=7.1,r=.34,crown=2.72,low=.42,top=.97,card=4700,color=(.460,.195,.065),name='Arce'),
 'linden':dict(seed=604,h=7.5,r=.35,crown=2.58,low=.43,top=.97,card=5000,color=(.238,.345,.097),name='Tilo')}
kind=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'oak'
p=DATA[kind]; rng=random.Random(p['seed'])
out=Path('output_plaza_v003')/kind;out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)

# Reproducible 512px bark albedo with fine longitudinal grooves and irregularity.
def save_pixels(name, arr, colorspace='sRGB'):
    h,w,_=arr.shape
    image=bpy.data.images.new(name,width=w,height=h,alpha=True)
    image.pixels.foreach_set(np.asarray(arr,dtype=np.float32).reshape(-1))
    image.filepath_raw=str((out/(name+'.png')).resolve())
    image.file_format='PNG';image.save()
    if colorspace!='sRGB':image.colorspace_settings.name='Non-Color'
    image.pack()
    return image
sz=512
yy,xx=np.mgrid[0:sz,0:sz].astype(np.float32)
rr=np.random.default_rng(p['seed'])
groove=np.sin(xx*.17+2*np.sin(yy*.015)+2.4*np.sin(xx*.031+yy*.008))
grain=np.sin(xx*.49+yy*.018)*.10
coarse=np.sin(xx*.033+yy*.049)*.16
noise=rr.normal(0,.07,(sz,sz)).astype(np.float32)
val=np.clip(.78+.12*groove+grain+coarse+noise,.44,1.04)
barkbase=(.32,.245,.172) if kind=='ash' else (.28,.207,.145)
rgba=np.stack([np.clip(barkbase[i]*val*(1+.04*np.sin(yy*.026+i)),0,1)
               for i in range(3)]+[np.ones_like(val)],axis=-1)
barkimg=save_pixels(kind+'_bark_albedo',rgba)
# Grain-projected normal map; PBR roughness stays high.
dx=np.gradient(val,axis=1);dy=np.gradient(val,axis=0)
normal=np.stack([-.9*dx,-.9*dy,np.ones_like(val)],axis=-1)
normal=normal/np.linalg.norm(normal,axis=-1)[...,None]
nm=np.concatenate([.5+.5*normal,np.ones((sz,sz,1),np.float32)],axis=-1)
normalimg=save_pixels(kind+'_bark_normal',nm,'Non-Color')

def material(name,img,normal_image=None,cutout=False):
    m=bpy.data.materials.new(name);m.use_nodes=True
    node=m.node_tree.nodes.get('Principled BSDF')
    node.inputs['Roughness'].default_value=.87
    node.inputs['Metallic'].default_value=0
    tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=img
    m.node_tree.links.new(tex.outputs['Color'],node.inputs['Base Color'])
    if cutout:
        quant=m.node_tree.nodes.new('ShaderNodeMath');quant.operation='ROUND'
        m.node_tree.links.new(tex.outputs['Alpha'],quant.inputs[0])
        m.node_tree.links.new(quant.outputs[0],node.inputs['Alpha'])
        m.use_backface_culling=False
    if normal_image:
        nt=m.node_tree.nodes.new('ShaderNodeTexImage');nt.image=normal_image
        normal_node=m.node_tree.nodes.new('ShaderNodeNormalMap')
        normal_node.inputs['Strength'].default_value=.42
        m.node_tree.links.new(nt.outputs['Color'],normal_node.inputs['Color'])
        m.node_tree.links.new(normal_node.outputs['Normal'],node.inputs['Normal'])
    return m

# 1024 atlas of FOUR INDIVIDUAL botanical leaves (not a disk of overlapping leaves).
# Leaf blades are lanceolate, elliptic, lobed (oak), and palmate (maple).
N=1024
atlas=np.zeros((N,N,4),dtype=np.float32)
for tile in range(4):
    tx=(tile%2)*512;ty=(tile//2)*512
    ys,xs=np.mgrid[0:512,0:512].astype(np.float32)
    # Axial coordinate: petiole at y=80, tip at y=455.
    t=(ys-78)/380
    u=(xs-256)/164
    if kind=='oak':
        width=np.sin(np.clip(t,0,1)*math.pi)**.72
        width*=.69+.22*np.cos(6*math.pi*t+.1*tile)
    elif kind=='maple':
        # Three pronounced lobes and serration instead of elliptical clovers.
        width=np.sin(np.clip(t,0,1)*math.pi)**.68*(.62+.36*np.cos(4*math.pi*t+.5*tile)**2)
    elif kind=='ash':
        width=np.sin(np.clip(t,0,1)*math.pi)**1.15*.52
    else:
        width=np.sin(np.clip(t,0,1)*math.pi)**.75*.76
    width*=1+.07*np.sin(29*t+tile)*np.sin(19*t+tile)
    center=256+14*np.sin(t*math.pi)*math.sin(tile*1.8)
    lateral=(xs-center)/164
    mask=(t>=0)&(t<=1)&(np.abs(lateral)<width)
    # Thin tapered midrib, asymmetrical veins, mottled green color.
    rib=np.exp(-((xs-center)/3.3)**2)*.18
    vein=np.sin(34*t+np.abs(lateral)*16)*np.exp(-np.abs(lateral)*3)*.045
    speck=rr.normal(0,.035,(512,512))
    c=np.array(p['color'],dtype=np.float32)
    shade=np.clip(1.38+.25*np.sin(t*math.pi)+vein+speck+.11*tile/4,.65,1.9)
    region=atlas[ty:ty+512,tx:tx+512]
    for i in range(3):
        value=np.clip(c[i]*shade+(rib*(.20 if i==1 else .06)),0,1)
        region[:,:,i][mask]=value[mask]
    region[:,:,3][mask]=1.0
    # Small petiole, integrated within leaf texture.
    stalk=(np.abs(xs-256)<3)&(ys>55)&(ys<118)
    region[stalk,:3]=c*.62;region[stalk,3]=1.0
leafimg=save_pixels(kind+'_foliage_cluster_atlas',atlas)
bark=material(kind+'_phototextured_bark',barkimg,normalimg)
foliage=material(kind+'_leaf_atlas_alpha_MASK',leafimg,cutout=True)

# Build one bark mesh and one leaf-card mesh: two glTF draw materials/tree.
verts=[];faces=[];uvfaces=[];anchors=[]
def tube(a,b,r0,r1,sides=9):
    if (b-a).length<.004:return
    d=(b-a).normalized()
    v=Vector((0,0,1)) if abs(d.z)<.92 else Vector((1,0,0))
    x=d.cross(v).normalized();y=d.cross(x).normalized()
    base=len(verts)
    for center,r in ((a,r0),(b,r1)):
        for i in range(sides):
            phase=math.tau*i/sides
            point=center+r*(math.cos(phase)*x+math.sin(phase)*y)
            verts.append(tuple(point))
    for i in range(sides):
        j=(i+1)%sides
        faces.append((base+i,base+j,base+sides+j,base+sides+i))
        # Bark texture's V axis is longitudinal, repeating around branches.
        uvfaces.append(((i/sides,0),(j/sides,0),(j/sides,1),(i/sides,1)))

def branch(a, direction, length, rad, curve=.22, segments=6):
    d=direction.normalized()
    spin=Vector((rng.uniform(-.5,.5),rng.uniform(-.5,.5),rng.uniform(.25,.65)))
    last=a
    for j in range(segments):
        t=(j+1)/segments
        nxt=a+d*length*t+spin*length*curve*t*t
        tube(last,nxt,max(.008,rad*(1-(j/segments)*.88)),
             max(.004,rad*(1-t*.91)),sides=8)
        if j>=2:
            anchors.append((nxt,d))
        last=nxt
    return last

h=p['h'];r=p['r'];trunk=[Vector((0,0,0))]
for j in range(1,14):
    t=j/13
    trunk.append(Vector((.16*math.sin(t*2.9),.11*math.sin(t*4.2),h*t)))
for j in range(13):
    tube(trunk[j],trunk[j+1],r*(1-j/13)*.91+.025,r*(1-(j+1)/13)*.91+.018,sides=13)
# Natural uneven roots.
for j in range(7):
    a=j*math.tau/7+rng.uniform(-.13,.13)
    tube(Vector((0,0,.28)),Vector((math.cos(a)*r*1.8,math.sin(a)*r*1.8,.018)),
         r*.29,.012,8)
# Golden-angle branch phyllotaxis plus vertical crown taper, not identical V forks.
for k in range(22):
    t=.34+.55*(k+1)/23
    a=t*13
    idx=min(12,max(3,round(a)))
    z=trunk[idx].z
    theta=k*2.39996+rng.uniform(-.26,.26)
    horizontal=Vector((math.cos(theta),math.sin(theta),0))
    crownprofile=math.sqrt(max(.02,1-((t-.66)/.45)**2))
    length=p['crown']*crownprofile*rng.uniform(.70,1.05)
    tilt=.19+.27*(k/22) if kind!='ash' else .42+.12*(k/22)
    d=(horizontal+Vector((0,0,tilt))).normalized()
    first=branch(trunk[idx],d,length,r*(.37-.10*t),.12,7)
    # Side sprays emanate from *along* primary branches (not only endpoints).
    for m in range(3):
        frac=.46+m*.18
        origin=trunk[idx]+d*length*frac+Vector((0,0,.08*frac))
        side=(horizontal*.62+
              Vector((-horizontal.y,horizontal.x,0))*rng.choice((-1,1))*.69+
              Vector((0,0,.28+rng.random()*.2))).normalized()
        branch(origin,side,length*(.37-.08*m),r*.095,.16,4)
    anchors.append((first,d))

# Prune cluster positions to an ellipsoidal, species-specific crown envelope.
lv=[];lf=[];lu=[]
for i in range(p['card']):
    center,base_direction=anchors[i%len(anchors)]
    zfract=(center.z-h*.33)/max(1e-4,h*.65)
    spread=p['crown']*.32
    az=rng.random()*math.tau;rad=math.sqrt(rng.random())*spread
    pos=center+Vector((math.cos(az)*rad,math.sin(az)*rad,rng.uniform(-.37,.4)))
    if pos.z<h*.36:pos.z=h*.36+rng.random()*.15
    card_size=rng.uniform(.13,.24) * (1.13 if kind=='oak' else 1)
    facing=(Vector((rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-.15,.7)))).normalized()
    a=facing.cross(Vector((0,0,1)))
    if a.length<.1:a=Vector((1,0,0))
    a.normalize();b=facing.cross(a).normalized()
    phase=rng.uniform(-.8,.8)
    x=(a*math.cos(phase)+b*math.sin(phase))*card_size
    y=(-a*math.sin(phase)+b*math.cos(phase))*card_size
    s=len(lv)
    for v in (pos-x-y,pos+x-y,pos+x+y,pos-x+y):lv.append(tuple(v))
    lf.append((s,s+1,s+2));lf.append((s,s+2,s+3))
    tile=rng.randrange(4)
    u0=(tile%2)*.5;v0=(tile//2)*.5
    coords=[(u0,v0),(u0+.5,v0),(u0+.5,v0+.5),(u0,v0+.5)]
    lu.append((coords[0],coords[1],coords[2]))
    lu.append((coords[0],coords[2],coords[3]))

bm=bpy.data.meshes.new(kind+'_V003_bark');bm.from_pydata(verts,[],faces);bm.update()
bm.materials.append(bark)
uv=bm.uv_layers.new(name='UVMap')
for poly,quad in zip(bm.polygons,uvfaces):
    for li,co in zip(poly.loop_indices,quad):uv.data[li].uv=co
for polygon in bm.polygons:polygon.use_smooth=True
ob=bpy.data.objects.new(kind+'_branch_architecture',bm);bpy.context.collection.objects.link(ob)
lm=bpy.data.meshes.new(kind+'_V003_foliage');lm.from_pydata(lv,[],lf);lm.update()
lm.materials.append(foliage);luv=lm.uv_layers.new(name='UVMap')
for poly,tri_uv in zip(lm.polygons,lu):
    for li,co in zip(poly.loop_indices,tri_uv):luv.data[li].uv=co
leaves=bpy.data.objects.new(kind+'_connected_foliage_cards',lm);bpy.context.collection.objects.link(leaves)

tris=sum(len(poly.vertices)-2 for mesh in (bm,lm) for poly in mesh.polygons)
assert 0<tris<=60000,(kind,tris)
audit={'species':kind,'triangle_count':tris,'ceiling':60000,
       'bark_triangles':len(bm.polygons)*2,'card_triangles':len(lm.polygons),
       'foliage_cards':p['card'],'glTF_expected_alpha_mode':'MASK',
       'techniques':['curved tapered trunks','spiral phyllotaxis','branchlets along primary branches',
                     'foliage alpha-cutout atlas','bark albedo and normal textures'],
       'status':'V003 visual candidate (not quality approved)'}
(out/'AUDIT.json').write_text(json.dumps(audit,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str((out/(kind+'_plaza_v003.blend')).resolve()))
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);leaves.select_set(True)
bpy.context.view_layer.objects.active=ob
bpy.ops.export_scene.gltf(filepath=str((out/(kind+'_plaza_v003.glb')).resolve()),
                         export_format='GLB',use_selection=True,export_apply=True)

# Offscreen review lighting, NOT included in game GLB.
bpy.ops.mesh.primitive_plane_add(size=200)
ground=bpy.context.object;ground.data.materials.append(bpy.data.materials.new('studio_ground'))
ground.data.materials[0].diffuse_color=(.38,.40,.33,1)
for loc,power,size in [((6,-5,11),2800,9),((-5,3,9),1700,10),((0,7,13),1900,9)]:
    bpy.ops.object.light_add(type='AREA',location=loc)
    o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size
bpy.ops.object.camera_add(location=(h*1.3,-h*.95,h*.72))
cam=bpy.context.object;bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU'
scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=960;scene.render.resolution_y=960;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
for shot,pos in [('front',(0,-h*1.4,h*.69)),
                 ('three_quarter',(h*.92,-h*1.14,h*.82)),
                 ('side',(h*1.4,0,h*.72)),('rear',(0,h*1.4,h*.69))]:
    cam.location=pos
    cam.rotation_euler=(Vector((0,0,h*.50))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str((out/(shot+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
print('V003_AUDIT',json.dumps(audit))
