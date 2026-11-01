"""V018 linen: correct V017 open spring-like winding while preserving tapered tail.
This is a bounded repair of a regression, not an approval of the final 8/10 look."""
import math
_previous_cord_v017=cord
def cord(hemp):
    item=_previous_cord_v017(hemp)
    if hemp:return item
    winding=next((o for o in objects if "hand_wound_natural_linen_thread_36_turns" in o.name),None)
    if not winding:raise RuntimeError("V018: linen winding source mesh unavailable")
    turns,steps,sides=36,46,6
    if len(winding.data.vertices)!=turns*steps*sides:
        raise RuntimeError("V018: unexpected winding topology")
    for turn in range(turns):
        old_axial=.0038*math.sin(turn*1.61)+.0019*math.sin(turn*3.31)
        # Tight pitch: keep the previously successful dense yarn coverage,
        # with only a slight believable turn-to-turn variation.
        offset=.00075*math.sin(turn*1.43)+.00045*math.sin(turn*3.03)
        for j in range(steps):
            phase=2*math.pi*j/(steps-1)
            prev_tension=.0015*math.sin(phase*3.2+turn*.41)
            previous_warp=1+.018*math.sin(phase*2.2+turn*.63)
            new_warp=1+.004*math.sin(phase*2.2+turn*.63)
            for k in range(sides):
                index=(turn*steps+j)*sides+k
                v=winding.data.vertices[index]
                x,y,z=v.co
                v.co.x=x-old_axial-prev_tension+offset+.00035*math.sin(phase*1.7+turn*.11)
                v.co.y=y/previous_warp*new_warp
                v.co.z=z/previous_warp*new_warp
    winding.data.update()
    # V017 organically tapered loose end is retained unchanged.
    return item
