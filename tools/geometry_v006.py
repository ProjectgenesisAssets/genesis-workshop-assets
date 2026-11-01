# V006 authored from explicit photographic CC0 bark / spool wood, with source manifests.
# V004 wood shapes and V005 linen thread coiling remain unchanged.
from pathlib import Path
def _secondary_image(role,label):
    paths=sorted((Path("sources")/K).glob("zz_v006_"+role+"_"+label+".*"))
    if not paths:return None
    im=bpy.data.images.load(str(paths[0].resolve()),check_existing=True)
    im.colorspace_settings.name="sRGB" if label=="Color" else "Non-Color"
    return im
def _install_photographic_wood_pbr(target,role, tint):
    mats=target.node_tree
    nodes=mats.nodes;links=mats.links
    bs=nodes.get("Principled BSDF")
    scans={k:_secondary_image(role,k) for k in ("Color","Roughness","NormalGL")}
    if not all(scans.values()):return False
    albedo=nodes.new("ShaderNodeTexImage");albedo.image=scans["Color"]
    rough=nodes.new("ShaderNodeTexImage");rough.image=scans["Roughness"]
    norm=nodes.new("ShaderNodeTexImage");norm.image=scans["NormalGL"]
    normalmap=nodes.new("ShaderNodeNormalMap");normalmap.inputs["Strength"].default_value=.8
    links.new(norm.outputs["Color"],normalmap.inputs["Color"])
    links.new(normalmap.outputs["Normal"],bs.inputs["Normal"])
    links.new(rough.outputs["Color"],bs.inputs["Roughness"])
    mul=nodes.new("ShaderNodeMixRGB");mul.blend_type="MULTIPLY"
    mul.inputs[0].default_value=1
    mul.inputs[2].default_value=(*tint,1)
    links.new(albedo.outputs["Color"],mul.inputs[1])
    links.new(mul.outputs["Color"],bs.inputs["Base Color"])
    return True
_v004_bark=v4_bark_material
def v4_bark_material():
    if not _secondary_image("bark","Color"):return _v004_bark()
    m=mat.copy();m.name="V006_PolyHaven_CC0_photographed_bark"
    _install_photographic_wood_pbr(m,"bark",(.91,.88,.78) if K=="dry-oak-wood" else (.95,.91,.82))
    return m
_v005_bobbin=linen_bobbin
def linen_bobbin():
    result=_v005_bobbin()
    m=bpy.data.materials.get("turned_hardwood_bobbin")
    if m and _secondary_image("bobbin","Color"):
        _install_photographic_wood_pbr(m,"bobbin",(.56,.43,.31))
    return result
