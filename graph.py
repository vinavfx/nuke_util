# -----------------------------------------------------------
# AUTHOR --------> Francisco Contreras
# OFFICE --------> Senior VFX Compositor, Software Developer
# WEBSITE -------> https://vinavfx.com
# -----------------------------------------------------------
import nuke  # type: ignore

output_connections_cache = None


def get_output_connection_map(force):
    global output_connections_cache
    if output_connections_cache and not force:
        return output_connections_cache
    output_connections_cache = build_output_connection_map()
    return output_connections_cache


def get_output_connections(node, force=True):
    return get_output_connection_map(force).get(node, [])


def get_upstream_nodes(
    node,
    visited=None,
    ignore_disabled=False,
    continue_at_up_level=False,
    active_switch=False,
):
    nodes = []
    if not node:
        return nodes

    if node.Class() == "Switch" and active_switch:
        which = int(node.knob("which").value())
        input_nodes = [node.input(which)]
    else:
        input_nodes = [node.input(index) for index in range(node.maxInputs())]

    if visited is None:
        visited = set()
        if continue_at_up_level and node.Class() == "Input":
            index = int(node.knob("number").value())
            node = node.parent()
            input_nodes = [None for _ in range(node.maxInputs())]
            input_nodes[index] = node.input(index)

    for input_node in input_nodes:
        if input_node and continue_at_up_level and input_node.Class() == "Input":
            index = int(input_node.knob("number").value())
            input_node = input_node.parent().input(index)

        if not input_node or input_node in visited:
            continue

        disable_knob = input_node.knob("disable")
        disabled = ignore_disabled and disable_knob and disable_knob.value()
        if not disabled:
            visited.add(input_node)
            nodes.append(input_node)

        nodes.extend(
            get_upstream_nodes(
                input_node,
                visited,
                ignore_disabled,
                continue_at_up_level,
                active_switch,
            )
        )

    return nodes


def get_first_input_chain_root(node):
    if not node:
        return

    topnode = node
    for _ in range(100):
        input_node = topnode.input(0)
        if not input_node:
            break
        topnode = input_node
    return topnode


def resolve_input_node(node, i, ignore_disabled=True, active_switch=False):
    if not node:
        return

    input_node = node.input(i)
    for _ in range(100):
        if not input_node:
            return

        disable_knob = input_node.knob("disable")
        disabled = ignore_disabled and disable_knob and disable_knob.value()
        if input_node.Class() == "Dot" or disabled:
            input_node = input_node.input(0)
            continue

        if input_node.Class() == "Switch" and active_switch:
            which = int(input_node.knob("which").value())
            input_node = input_node.input(which)
            continue

        return input_node


def get_input_connections(node):
    input_nodes = []
    for index in range(node.inputs()):
        input_node = node.input(index)
        if input_node:
            input_nodes.append((index, input_node))
    return input_nodes


def build_output_connection_map():
    dependencies = {}
    for node in nuke.allNodes(recurseGroups=True):
        if "FnNukeMultiTypeOpIop" in node.Class():
            continue
        for index, input_node in get_input_connections(node):
            dependencies.setdefault(input_node, []).append((index, node))
    return dependencies
