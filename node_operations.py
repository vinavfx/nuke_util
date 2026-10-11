# -----------------------------------------------------------
# AUTHOR --------> Francisco Contreras
# OFFICE --------> Senior VFX Compositor, Software Developer
# WEBSITE -------> https://vinavfx.com
# -----------------------------------------------------------
import nuke  # type: ignore
import nukescripts  # type: ignore

from .graph import get_input_connections, get_output_connections


def replace_node_with_clone(src, dst, keep_pos=True):
    clone = nuke.clone(src, inpanel=False)
    clone.setSelected(False)
    for index, input_node in get_input_connections(dst):
        clone.setInput(index, input_node)
    for index, output_node in get_output_connections(dst):
        output_node.setInput(index, clone)
    if keep_pos:
        clone.setXYpos(dst.xpos(), dst.ypos())
    nuke.delete(dst)
    return clone


def unclone_node(clone):
    if not clone.clones():
        return

    xpos, ypos = clone.xpos(), clone.ypos()
    nukescripts.declone(clone)
    node = nuke.selectedNode()
    node.setSelected(False)
    node.hideControlPanel()
    node.setXYpos(xpos, ypos)
    return node


def transfer_knobs(
    source_node,
    dest_node,
    link=False,
    transfer_all=False,
    ignore_hidden=True,
    disable_knob_changed=True,
):
    if not source_node or not dest_node:
        nuke.message("Source or destination node not found.")
        return

    excluded = set()
    if not transfer_all:
        group = nuke.createNode("Group", inpanel=False)
        try:
            excluded = set(group.knobs())
        finally:
            nuke.delete(group)

    source_knobs = {knob.name() for knob in source_node.allKnobs()}
    dest_knobs = {knob.name() for knob in dest_node.allKnobs()}
    common_knobs = source_knobs.intersection(dest_knobs)
    source_name = source_node.fullName()
    linked_names = []

    callback_backup = dest_node["knobChanged"].value()
    if disable_knob_changed:
        dest_node["knobChanged"].setValue("")

    try:
        for knob_name in common_knobs:
            if knob_name in excluded:
                continue

            source_knob = source_node.knob(knob_name)
            dest_knob = dest_node.knob(knob_name)
            if not (source_knob and dest_knob):
                continue
            if not dest_knob.visible() and ignore_hidden:
                continue
            if not nuke.toNode(source_name):
                continue

            visible = source_knob.visible()
            if link:
                dest_knob.setExpression("root.{}.{}".format(source_name, knob_name))
            else:
                if isinstance(dest_knob, nuke.Enumeration_Knob):
                    dest_knob.setValues(source_knob.values())
                dest_knob.fromScript(source_knob.toScript())

            dest_knob.setVisible(visible)
            linked_names.append(knob_name)
    finally:
        if disable_knob_changed:
            dest_node["knobChanged"].setValue(callback_backup)

    return linked_names


def clear_selection():
    for node in nuke.selectedNodes():
        node.setSelected(False)


def copy_node_to_clipboard(node, group=None):
    if group:
        group.begin()
    try:
        clear_selection()
        node.setSelected(True)
        nuke.nodeCopy("%clipboard%")
        node.setSelected(False)
    finally:
        if group:
            group.end()


def paste_node_from_clipboard():
    clear_selection()
    nuke.nodePaste("%clipboard%")
    node = nuke.selectedNode()
    node.setSelected(False)
    return node


def duplicate_nodes(source_nodes, posx=0, posy=0, center_x_from_node="NoOp"):
    clear_selection()
    for node in source_nodes:
        node.setSelected(True)

    nuke.nodeCopy("%clipboard%")
    clear_selection()
    nuke.nodePaste("%clipboard%")

    new_nodes = nuke.selectedNodes()
    reference_nodes = [node for node in new_nodes if node.Class() != "Dot"]
    if not reference_nodes:
        reference_nodes = new_nodes

    xs = [node.xpos() for node in reference_nodes]
    ys = [node.ypos() for node in reference_nodes]
    center_x = (min(xs) + max(xs)) / 2
    center_y = (min(ys) + max(ys)) / 2
    reference = next(
        (node for node in new_nodes if node.Class() == center_x_from_node), None
    )
    if reference:
        center_x = reference.xpos()

    offset_x, offset_y = posx - center_x, posy - center_y
    for node in new_nodes:
        node.setXYpos(int(node.xpos() + offset_x), int(node.ypos() + offset_y))

    clear_selection()
    return new_nodes


def add_keyframe(knob, value, frame, dimension=0, interpolation=nuke.HORIZONTAL):
    knob.setAnimated()
    knob.setValueAt(value, frame, dimension)
    curve = knob.animation(dimension)
    last_key = curve.keys()[-1]
    curve.changeInterpolation([last_key], interpolation)
