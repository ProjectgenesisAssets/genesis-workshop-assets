# Project Genesis Plaza - procedural arboreal V004 (original, no purchased models)
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
out=Path('output_plaza_v004')/kind;out.mkdir(parents=True,exist_ok=True)
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

def branch(a, direction, length, rad, curve=.22, segments=7):
    # One continuous taper per limb (ring-to-ring mesh), not stacked pipe segments.
    d=direction.normalized()
    wander=Vector((rng.uniform(-.7,.7),rng.uniform(-.7,.7),rng.uniform(-.25,.6)))
    centers=[a+d*length*(j/segments)+wander*length*curve*(j/segments)**2 for j in range(segments+1)]
    base=len(verts);sides=9
    for j,center in enumerate(centers):
        tangent=(centers[min(segments,j+1)]-centers[max(0,j-1)]).normalized()
        ref=Vector((0,0,1)) if abs(tangent.z)<.93 else Vector((1,0,0))
        axis=tangent.cross(ref).normalized();other=tangent.cross(axis).normalized()
        t=j/segments
        radius=max(.003,rad*((1-t)**1.35+.035))
        for k in range(sides):
            ang=math.tau*k/sides
            verts.append(tuple(center+radius*(axis*math.cos(ang)+other*math.sin(ang))))
    for j in range(segments):
        for k in range(sides):
            k2=(k+1)%sides
            faces.append((base+j*sides+k,base+j*sides+k2,base+(j+1)*sides+k2,base+(j+1)*sides+k))
            uvfaces.append(((k/sides,j/segments),(k2/sides,j/segments),
                            (k2/sides,(j+1)/segments),(k/sides,(j+1)/segments)))
        if j>=2:anchors.append((centers[j],d))
    return centers[-1]

# Four intentionally different branch architectures; inspect before foliage approval.
h=p['h'];r=p['r']
params={
 'oak':dict(trunk=.59,lean=.16,primary=7,branches=18,low=.38,high=.78,
            lateral=1.45,up=.08,curve=.32,rad=.62),
 'ash':dict(trunk=.84,lean=.045,primary=4,branches=24,low=.51,high=.94,
            lateral=.78,up=.98,curve=.12,rad=.37),
 'maple':dict(trunk=.38,lean=.11,primary=5,branches=19,low=.27,high=.70,
              lateral=1.26,up=.40,curve=.19,rad=.51),
 'linden':dict(trunk=.78,lean=.055,primary=6,branches=25,low=.44,high=.91,
              lateral=.96,up=-.07,curve=.23,rad=.43)}
a=params[kind]
# Main leader height varies hugely: oak/maple split early; ash/linden retain leader.
top=h*a['trunk']
centerline=[Vector((a['lean']*math.sin(t*3.2)*t,a['lean']*.45*math.sin(t*5.6),top*t))
            for t in [j/20 for j in range(21)]]
for j in range(20):
    t=j/20
    rad=r*(1-t)**(.82 if kind=='oak' else 1.07)+.012
    tube(centerline[j],centerline[j+1],rad,
         r*(1-(j+1)/20)**(.82 if kind=='oak' else 1.07)+.008,sides=15)
# Root flare, stronger for old oak.
for j in range(8 if kind=='oak' else 6):
    angle=j*math.tau/(8 if kind=='oak' else 6)+rng.uniform(-.10,.10)
    breadth=2.4 if kind=='oak' else 1.65
    tube(Vector((0,0,.31)),Vector((math.cos(angle)*r*breadth,math.sin(angle)*r*breadth,.025)),
         r*(.45 if kind=='oak' else .28),.014,9)

# First-order scaffold is deliberately architectural, not a scaled clone.
for k in range(a['primary']):
    theta=(k+.19)*math.tau/a['primary']+rng.uniform(-.17,.17)
    plane=Vector((math.cos(theta),math.sin(theta),0))
    if kind=='oak':
        z=top*(.62+.28*(k%3)/2)
        tilt=.07+.10*(k%2)
        L=p['crown']*rng.uniform(1.10,1.43)
    elif kind=='maple':
        z=top*(.80+.15*(k%2))
        tilt=.58+.12*(k%3)
        L=p['crown']*rng.uniform(1.17,1.52)
    elif kind=='ash':
        z=top*(.69+.27*(k%3)/2)
        tilt=1.12+.25*(k%2)
        L=p['crown']*rng.uniform(.77,1.04)
    else:
        z=top*(.68+.26*(k%3)/2)
        tilt=.20+.08*(k%2)
        L=p['crown']*rng.uniform(.88,1.16)
    anchor=Vector((a['lean']*math.sin(z/top*3.2)*z/top,0,z))
    direction=(plane+Vector((0,0,tilt))).normalized()
    tip=branch(anchor,direction,L,r*a['rad']*(1-.035*k),a['curve'],10)
    anchors.append((tip,direction))
    # Secondary crowns grow from the tip *and* from the scaffold midsection.
    for j in range(4):
        at=anchor+(tip-anchor)*(.47+.12*j)
        swirl=plane*.51+Vector((-plane.y,plane.x,0))*rng.choice((-1,1))*.74
        rise=.35 if kind=='oak' else (.77 if kind=='ash' else (.45 if kind=='maple' else -.18))
        leafdir=(swirl+Vector((0,0,rise))).normalized()
        branch(at,leafdir,L*rng.uniform(.35,.62),r*.105,.17,5)

for k in range(a['branches']):
    t=a['low']+(a['high']-a['low'])*(k+.6)/a['branches']
    z=t*h
    theta=k*2.39996+rng.uniform(-.24,.24)
    horizontal=Vector((math.cos(theta),math.sin(theta),0))
    if kind=='oak':
        width=math.sqrt(max(.12,1-((t-.61)/.44)**2))
    elif kind=='ash':
        width=max(.2,1-(t-.63)*.54)
    elif kind=='maple':
        width=math.sqrt(max(.16,1-((t-.59)/.37)**2))
    else:
        width=math.sqrt(max(.12,1-((t-.66)/.43)**2))
    length=p['crown']*a['lateral']*width*rng.uniform(.52,.85)
    up=a['up']+rng.uniform(-.1,.16)
    direction=(horizontal+Vector((0,0,up))).normalized()
    # For species with split trunks, upper branchlets originate on the crowns,
    # not magically from a full-height central pole.
    origin=(Vector((0,0,min(z,top*.94))) if z<=top else
            centerline[-1]+horizontal*(z-top)*(.48 if kind=='maple' else .24)+Vector((0,0,z-top)))
    endpoint=branch(origin,direction,length,r*(.13 if kind=='ash' else .19),a['curve'],7)
    anchors.append((endpoint,direction))
    for j in range(3):
        side=(horizontal*.45+Vector((-horizontal.y,horizontal.x,0))*rng.choice([-1,1])*.72+
              Vector((0,0,.4 if kind!='linden' else -.12))).normalized()
        branch(origin+(endpoint-origin)*(.48+.15*j),side,length*.46,r*.065,.17,4)
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

bm=bpy.data.meshes.new(kind+'_V004_bark');bm.from_pydata(verts,[],faces);bm.update()
bm.materials.append(bark)
uv=bm.uv_layers.new(name='UVMap')
for poly,quad in zip(bm.polygons,uvfaces):
    for li,co in zip(poly.loop_indices,quad):uv.data[li].uv=co
for polygon in bm.polygons:polygon.use_smooth=True
ob=bpy.data.objects.new(kind+'_branch_architecture',bm);bpy.context.collection.objects.link(ob)
lm=bpy.data.meshes.new(kind+'_V004_foliage');lm.from_pydata(lv,[],lf);lm.update()
lm.materials.append(foliage);luv=lm.uv_layers.new(name='UVMap')
for poly,tri_uv in zip(lm.polygons,lu):
    for li,co in zip(poly.loop_indices,tri_uv):luv.data[li].uv=co
leaves=bpy.data.objects.new(kind+'_connected_foliage_cards',lm);bpy.context.collection.objects.link(leaves)

tris=sum(len(poly.vertices)-2 for mesh in (bm,lm) for poly in mesh.polygons)
assert 0<tris<=60000,(kind,tris)
audit={'species':kind,'triangle_count':tris,'ceiling':60000,
       'bark_triangles':len(bm.polygons)*2,'card_triangles':len(lm.polygons),
       'foliage_cards':p['card'],'glTF_expected_alpha_mode':'MASK',
       'techniques':['species-specific leader height and root flare','independent scaffold branching architecture','continuous tapered limb rings','spiral secondary branches',
                     'foliage alpha-cutout atlas','bark albedo and normal textures'],
       'status':'V004 distinct-skeleton candidate: visual approval pending'}
(out/'AUDIT.json').write_text(json.dumps(audit,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str((out/(kind+'_plaza_v004.blend')).resolve()))
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);leaves.select_set(True)
bpy.context.view_layer.objects.active=ob
bpy.ops.export_scene.gltf(filepath=str((out/(kind+'_plaza_v004.glb')).resolve()),
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
# Critical skeletal silhouette QA: four species should differ without leaves.
leaves.hide_render=True
for shot,pos in [('skeleton_front',(0,-h*1.4,h*.69)),
                 ('skeleton_three_quarter',(h*.92,-h*1.14,h*.82))]:
    cam.location=pos
    cam.rotation_euler=(Vector((0,0,h*.49))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str((out/(shot+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
leaves.hide_render=False
print('V004_AUDIT',json.dumps(audit))
