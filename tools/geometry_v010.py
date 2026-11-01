"""V010 visual correction after six actual V009 renders: preserve natural horizontal
firewood reading and remove detached hemp hairs. Keep all previous versions in Git."""
_v009_cord=cord
_v009_bark=v4_bark_material
def v4_bark_material():
    result=_v009_bark()
    if K.startswith("dry-"):
        # Physically matte bark, toned down so it does not overpower exposed wood fibers.
        for node in result.node_tree.nodes:
            if node.type=="MIX_RGB" and node.blend_type=="MULTIPLY":
                color=node.inputs[2].default_value
                if K=="dry-oak-wood" and .84<=color[0]<=.99:
                    node.inputs[2].default_value=(.93,.72,.60,1)
                elif K=="dry-ash-wood" and .90<=color[0]<=1.01:
                    node.inputs[2].default_value=(.79,.73,.63,1)
    return result
def wood_piece(label,oak,offset):
    # V009 tilted the billets end-on; the renders proved it worse.
    # Revert to correct horizontal storage composition and expose a small torn edge.
    ob=_v008_wood_piece(label,oak,offset)
    ob.rotation_euler.x=.17+.04*offset
    for child in objects:
        if child.name.startswith(label+"_split_sliver"):
            child.rotation_euler=tuple(ob.rotation_euler)
    return ob
def cord(hemp):
    if hemp:
        # V009 fibrils were disconnected in render; use attached V008 strands instead.
        return _v008_cord(True)
    return _v009_cord(False)
