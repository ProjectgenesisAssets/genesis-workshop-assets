"""Genesis Shield V017: conservative hand-forged dent review from untouched V015."""
from pathlib import Path
src=Path(__file__).with_name("render_escudo_hierro_meshy_v015.py").read_text(encoding="utf-8")
assert 'def strong_edge_deformation(x,z,rad):' in src
assert 'def plateidx(j,i):return 1+(j-1)*SEG+(i%SEG)' in src
assert 'RINGS=48  # actual surface vertices' in src
src=src.replace("V015","V017").replace("v015","v017")
start=src.index("def strong_edge_deformation(x,z,rad):")
end=src.index("\nplate_verts.append((c.x,ymn-.062*R+",start)
replacement='''def strong_edge_deformation(x,z,rad):
    # V017: V015 iron plate topology remains 48x120, no extra segments.
    # Only soften and asymmetrize THREE existing physical edge hammer marks.
    depression=0.0
    for idx,hit in enumerate(edge_hits):
        dx=x-hit["x"];dz=z-hit["z"]
        a=math.radians(hit["rotation_deg"]);cs=math.cos(a);sn=math.sin(a)
        u=(cs*dx+sn*dz)/(R*hit["major_R"])
        v=(-sn*dx+cs*dz)/(R*hit["minor_R"])
        r=math.hypot(u,v)
        if r>3.0:continue
        ang=math.atan2(v,u)
        # Low-amplitude irregular outline, not a grid of folded polygon strips.
        edge=1.0+.085*math.sin(3*ang+idx*1.12+.27)+.035*math.sin(6*ang-idx*.83)
        q=r/edge
        core=math.exp(-1.83*q*q)*(1.0+.065*math.tanh(u))
        # Raised lip is discontinuous, very shallow relative to main dent.
        lip=(.112+.018*math.sin(4*ang+idx*.45))*math.exp(-((q-1.14)/.24)**2)
        # A short tool-slide trace within the dent, barely visible at distance.
        shear=.075*math.exp(-((v+.24*u+.19)/.19)**2)*math.exp(-((u-.20)/.65)**2)
        shoulder=.045*math.exp(-((v-.32*u-.14)/.16)**2)*math.exp(-((u+.25)/.58)**2)
        depression+=R*hit["depth_R"]*(core+shear-lip-shoulder)
    # Preserve the caprine / iron joint: deformation disappears before rim.
    t=max(0.0,min(1.0,(1.0-rad/PLATE_R)/.13))
    edge_protection=t*t*(3.0-2.0*t)
    return max(-.006*R,min(.042*R,depression))*edge_protection
'''
src=src[:start]+replacement+src[end:]
# The original plate ring index is unchanged, with matching SEG on every loop.
assert 'def plateidx(j,i):return 1+(j-1)*SEG+(i%SEG)' in src
assert 'SEG=120' in src and 'RINGS=48' in src
src=src.replace('"V017_3_edge_hits_added":True','"V015_3_edge_hits_preserved":True,"V017_edge_hits_slightly_irregular":True')
src=src.replace('{"reference":"V013B","iron_only_softbox_watts":260','{"reference":"V015","iron_only_softbox_watts":260')
src=src.replace('"macro_geometry_untouched_at_edge":True,','"macro_geometry_untouched_at_edge":True,\n    "impact_profile":"slightly asymmetric shallow lips, restrained short hammer drag; original plate topology",')
src=src.replace('render("V017_01_frente_golpes_fuertes",-1)','render("V017_01_frente_golpes_moderados",-1)')
src=src.replace('render("V017_03_detalle_golpes_borde",-1,detail=True)','render("V017_03_detalle_hierro",-1,detail=True)')
src=src.replace('REPORT["status"]="rendered_pending_human_review"',
                'REPORT["status"]="rendered_pending_human_review"\nREPORT["conservative_v017"]={"base":"V015 exact approved source references","topology":"unmodified 48 rings x 120 segments","change":"only 3 impact shapes: mild asymmetry, broken shallow lip, limited drag","iron_material":"V175 unchanged","leather":"V020 unchanged","hdr_lighting":"unchanged","human_approval":False}')
out=Path("output_escudo_meshy_v017")
out.mkdir(exist_ok=True)
dst=out/"generated_render_escudo_v017.py"
assert src.count('render("V017_0')==3
compile(src,str(dst),"exec")
dst.write_text(src,encoding="utf-8")
print("GENESIS_V017_PATCH_CREATED",dst,len(src))
