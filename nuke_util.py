# -----------------------------------------------------------
# AUTHOR --------> Francisco Jose Contreras Cuevas
# OFFICE --------> Senior VFX Compositor, Software Developer
# WEBSITE -------> https://vinavfx.com
# -----------------------------------------------------------
import os
import platform
import colorsys
import nuke  # type: ignore
import nukescripts  # type: ignore

if platform.system() == 'Linux':
    user_path = os.path.expanduser('~')
else:
    user_path = os.environ['USERPROFILE'].replace('\\', '/')

nuke_path = '{0}/.nuke'.format(user_path)
vina_path = nuke_path + '/vina_nuke'
dependency_all_nodes = None


def get_connected_nodes(node, visited=None, ignore_disabled=False):
    if visited is None:
        visited = set()

    nodes = []

    for i in range(node.maxInputs()):
        inode = node.input(i)

        if not inode:
            continue

        disable_knob = node.knob('disable')

        if ignore_disabled and not i == 0 and disable_knob:
            if disable_knob.value():
                continue

        if inode not in visited:
            visited.add(inode)
            nodes.append(inode)
            nodes.extend(get_connected_nodes(inode, visited, ignore_disabled))

    return nodes


def get_dependencies(node):
    # Similar a 'get_connected_nodes' pero este
    # incluye los nodos con dependencias de expression
    dependencies = []
    nodes_to_process = node.dependencies()

    while nodes_to_process:
        node = nodes_to_process.pop(0)
        if node not in dependencies:
            dependencies.append(node)
            nodes_to_process.extend(node.dependencies())

    return dependencies


def get_dependent(node):
    nodes = []

    for n in node.dependent():
        if n.Class() == 'Dot':
            nodes.extend(get_dependent(n))
        else:
            nodes.append(n)

    return nodes


def get_user_path():
    return user_path


def get_vina_path():
    return vina_path


def get_topnode(node):
    if not node:
        return

    topnode = node

    for _ in range(100):
        inode = topnode.input(0)
        if not inode:
            break

        topnode = inode

    return topnode


def get_input(node, i, ignore_disabled=True):
    if not node:
        return

    inode = node.input(i)

    for _ in range(100):
        if not inode:
            return

        disable_knob = inode.knob('disable')
        disabled_node = False

        if disable_knob and ignore_disabled:
            disabled_node = inode.knob('disable').value()

        if inode.Class() == 'Dot' or disabled_node:
            if inode.input(0):
                inode = inode.input(0)
                continue
            else:
                return

        return inode


def is_vina_gizmo(gizmo):
    if not hasattr(gizmo, 'nodes'):
        return False

    name = gizmo.knob('_name')

    if not name:
        return False

    if not 'Francisco' in name.value():
        return False

    return True


def get_nuke_path():
    return nuke_path


def get_nuke_executable():
    executable = '/opt/Nuke{}/nuke'.format(nuke.NUKE_VERSION_STRING)

    if os.path.isfile(executable):
        return executable

    executable = '/usr/local/Nuke{}/Nuke{}.{}'.format(
        nuke.NUKE_VERSION_STRING, nuke.NUKE_VERSION_MAJOR, nuke.NUKE_VERSION_MINOR)

    if os.path.isfile(executable):
        return executable

    executable = 'C:/Program Files/Nuke{}/Nuke{}.{}.exe'.format(
        nuke.NUKE_VERSION_STRING, nuke.NUKE_VERSION_MAJOR, nuke.NUKE_VERSION_MINOR)

    return executable


def get_nuke_plugins():
    return os.path.dirname(get_nuke_executable()) + '/plugins'


def declone(clone):
    if not clone.clones():
        return

    xpos = clone.xpos()
    ypos = clone.ypos()

    nukescripts.declone(clone)

    node = nuke.selectedNode()

    node.setSelected(False)
    node.hideControlPanel()
    node.setXYpos(xpos, ypos)

    return node


def force_clone(src, dst, keep_pos=True):
    clone = nuke.clone(src, inpanel=False)
    clone.setSelected(False)

    for i, inode in get_input_nodes(dst):
        clone.setInput(i, inode)

    for i, onode in get_output_nodes(dst):
        onode.setInput(i, clone)

    if keep_pos:
        clone.setXYpos(dst.xpos(), dst.ypos())
    nuke.delete(dst)

    return clone


def duplicate_node(node, parent=None):
    node.parent().begin()

    [n.setSelected(False) for n in nuke.selectedNodes()]

    node.setSelected(True)
    nuke.nodeCopy("%clipboard%")
    node.setSelected(False)

    node.parent().end()

    if parent:
        parent.begin()

    [n.setSelected(False) for n in nuke.selectedNodes()]

    nuke.nodePaste("%clipboard%")
    new_node = nuke.selectedNode()
    new_node.setSelected(False)

    if parent:
        parent.end()

    return new_node


def get_input_nodes(node):
    input_nodes = []

    for i in range(node.inputs()):
        inode = node.input(i)
        if inode:
            input_nodes.append((i, inode))

    return input_nodes


def get_dependency_all_nodes(force):
    global dependency_all_nodes

    if dependency_all_nodes and not force:
        return dependency_all_nodes

    nodes = {}

    for node in nuke.allNodes(recurseGroups=True):
        for i, inode in get_input_nodes(node):

            if inode in nodes:
                nodes[inode].append((i, node))
            else:
                nodes[inode] = [(i, node)]

    dependency_all_nodes = nodes
    return nodes


def get_output_nodes(node, force=True):

    deps = get_dependency_all_nodes(force)

    if node in deps:
        return deps[node]
    else:
        return []


def add_key(knob, value, frame, dimension=0, interpolation=nuke.HORIZONTAL):
    knob.setAnimated()
    knob.setValueAt(value, frame, dimension)

    curve = knob.animation(dimension)
    last_key = curve.keys()[-1]
    curve.changeInterpolation([last_key], interpolation)


def set_tile_color(node, hsl):
    h, s, l = hsl
    rgb = colorsys.hsv_to_rgb(h, s, l)

    r = int(rgb[0] * 255)
    g = int(rgb[1] * 255)
    b = int(rgb[2] * 255)

    hex_colour = int('%02x%02x%02x%02x' % (r, g, b, 1), 16)

    node['tile_color'].setValue(hex_colour)


def set_font_color(node, hsl):
    h, s, l = hsl
    rgb = colorsys.hsv_to_rgb(h, s, l)

    r = int(rgb[0] * 255)
    g = int(rgb[1] * 255)
    b = int(rgb[2] * 255)

    hex_colour = int('%02x%02x%02x%02x' % (r, g, b, 1), 16)

    node['note_font_color'].setValue(hex_colour)


def set_hex_color(node, hx, intensity=1.0, sat=1.0):

    hx = hx[1:]

    r = int(hx[0:2], 16) * intensity
    g = int(hx[2:4], 16) * intensity
    b = int(hx[4:6], 16) * intensity

    average = (r + g + b) / 3.0

    r = int((r - average) * sat + average)
    g = int((g - average) * sat + average)
    b = int((b - average) * sat + average)

    hex_colour = int('%02x%02x%02x%02x' %
                     (r, g, b, 1), 16)

    node['tile_color'].setValue(hex_colour)


def get_absolute(filename):
    if not '..' in filename:
        return filename

    return os.path.abspath(nuke.script_directory() + '/' + filename)


def get_project_name(version=True):
    basename = os.path.basename(nuke.root().name())

    if basename == 'Root':
        return 'Untitled'

    if not version:
        return basename[::-1].split('v', 1)[-1][::-1][:-1]

    return basename[:-3]


def knobs_refresh(node):
    # actualiza el knobs si se ocultan o deshabilitan, con esta se actualizan
    node.forceValidate()
    node.lock()
    node.unlock()


def set_pos_backdrop(backdrop, x, y):

    # Old position of Backdrop
    positionX = backdrop.xpos()
    positionY = backdrop.ypos()

    # Select nodes in Backdrop
    backdrop.selectNodes(True)

    # Move Backdrop to new position
    backdrop.setXYpos(x, y)

    # Calculate offset between new and old Backdrop position
    offsetX = positionX - backdrop.xpos()
    offsetY = positionY - backdrop.ypos()

    # Set new position for nodes in Backdrop
    for n in nuke.selectedNodes():
        curXpos = n.xpos()
        curYpos = n.ypos()
        n.setXYpos(curXpos - offsetX, curYpos - offsetY)
        n['selected'].setValue(False)
