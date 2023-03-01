# Author: Francisco Jose Contreras Cuevas
# Office: VFX Artist - Senior Compositor
# Website: vinavfx.com
import os
import platform
import nuke
import nukescripts

if platform.system() == 'Linux':
    user_path = os.path.expanduser('~')
else:
    user_path = os.environ['USERPROFILE'].replace('\\', '/')

nuke_path = '{0}/.nuke'.format(user_path)
vina_path = nuke_path + '/vina_pipeline'


def get_connected_nodes(node):
    nodes = []

    for i in range(node.inputs()):
        inode = node.input(i)

        if not inode:
            continue

        nodes.append(inode)

        for n in get_connected_nodes(inode):
            if not n in nodes:
                nodes.append(n)

    return nodes


def get_user_path():
    return user_path


def get_input_nodes(node):
    input_nodes = []

    for i in range(node.inputs()):
        _input = node.input(i)
        if _input:
            input_nodes.append((i, _input))

    return input_nodes


def get_vina_path():
    return vina_path


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

    nuke.nodePaste("%clipboard%")
    new_node = nuke.selectedNode()
    new_node.setSelected(False)

    if parent:
        parent.end()

    return new_node


def get_output_nodes(node):
    nodes = []

    for onode in node.dependent():
        for i in range(onode.inputs()):

            inode = onode.input(i)
            if not inode:
                continue

            if inode.name() == node.name():
                nodes.append((i, onode))

    return nodes


def add_key(knob, value, frame, dimension=0, interpolation=nuke.HORIZONTAL):
    knob.setAnimated()
    knob.setValueAt(value, frame, dimension)

    curve = knob.animation(dimension)
    last_key = curve.keys()[-1]
    curve.changeInterpolation([last_key], interpolation)


def set_tile_color(node, h, s, l):
    rgb = hsl_to_rgb(h, s, l)

    r = int(rgb[0] * 255)
    g = int(rgb[1] * 255)
    b = int(rgb[2] * 255)

    hex_colour = int('%02x%02x%02x%02x' % (r, g, b, 1), 16)

    node['tile_color'].setValue(hex_colour)


def set_font_color(node, h, s, l):
    rgb = hsl_to_rgb(h, s, l)

    r = int(rgb[0] * 255)
    g = int(rgb[1] * 255)
    b = int(rgb[2] * 255)

    hex_colour = int('%02x%02x%02x%02x' % (r, g, b, 1), 16)

    node['note_font_color'].setValue(hex_colour)


def set_hex_color(node, hx, intensity=1.0, sat=1.0):

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


def hsl_to_rgb(h, s, l):
    def clamp(value, min_value, max_value):
        return max(min_value, min(max_value, value))

    def saturate(value):
        return clamp(value, 0.0, 1.0)

    def hue_to_rgb(h):
        r = abs(h * 6.0 - 3.0) - 1.0
        g = 2.0 - abs(h * 6.0 - 2.0)
        b = 2.0 - abs(h * 6.0 - 4.0)
        return saturate(r), saturate(g), saturate(b)

    l /= 2.0

    r, g, b = hue_to_rgb(h)
    c = (1.0 - abs(2.0 * l - 1.0)) * s
    r = (r - 0.5) * c + l
    g = (g - 0.5) * c + l
    b = (b - 0.5) * c + l
    return r, g, b


def get_absolute(filename):
    if not '..' in filename:
        return filename

    return os.path.abspath(nuke.script_directory() + '/' + filename)


def get_project_name(version=True):
    basename = os.path.basename(nuke.root().name())

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
