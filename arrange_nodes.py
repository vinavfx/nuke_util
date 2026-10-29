# -----------------------------------------------------------
# AUTHOR --------> Francisco Contreras
# OFFICE --------> Senior VFX Compositor, Software Developer
# WEBSITE -------> https://vinavfx.com
# -----------------------------------------------------------
import math
import os
import re

import nuke  # type: ignore

BACKDROP_CLASS = "BackdropNode"
VIEWER_CLASS = "Viewer"
EXCLUDED_CLASSES = ("Dot", BACKDROP_CLASS, "StickyNote", VIEWER_CLASS, "Root")
DEFAULT_NODE_SIZE = (80, 18)
DOT_SIZE = (12, 12)
DEFAULT_GRID_WIDTH = 110.0
MIN_COLUMN_WIDTH = 100.0
ROW_UNIT = 26.0
TIGHT_GAP = 8.0
NORMAL_ROWS = 3
FAN_INPUTS = 4
BLOCK_GAP = 150.0
COLUMN_GAP = 20.0
TREE_GAP_COLUMNS = 1
MAX_ROUTE_COLUMNS = 2
LINE_CLEARANCE = 6.0
EPSILON = 0.5
HIDDEN_DOT_LABEL = "[value input.name]"
MIN_BACKDROP_NODES = 3
BACKDROP_CLUSTER_GAP = 150.0
BACKDROP_PADDING = 40
BACKDROP_FONT = "Verdana"
BACKDROP_FONT_SIZE = 20
BACKDROP_MARGIN = 30
GIZMO_KNOB = "comfyui_gizmo"
GENERATION_SUFFIXES = ("Backup", "Restored")
READ_CLASSES = ("Read", "DeepRead", "ReadGeo", "ReadGeo2")
WRITE_CLASSES = ("Write", "DeepWrite", "WriteGeo")
VIRTUAL_INDEX = -1
STACK_INDEX = -2
STACK_PER_ROW = 10
STACK_COLUMN_SPACING = 100
STACK_ROW_GAP = 20
MAX_LOOSE_CHAIN = 3
LOOSE_PER_ROW = 10
LOOSE_GAP = 10
LOOSE_COLUMN_GAP = 20
LOOSE_ROW_GAP = 40
LOOSE_GROUPS = (("Inputs", 0x5D6B80FF, True), ("Trash", 0x4D4D4DFF, False))
LINK_FLAGS = nuke.INPUTS | nuke.HIDDEN_INPUTS | nuke.EXPRESSIONS | nuke.LINKINPUTS

size_cache = {}
link_cache = {}


class HiddenDot(object):
    def __init__(self, source, target, index):
        self.source = source
        self.target = target
        self.index = index


class RouteDot(HiddenDot):
    pass


class ReadStack(object):
    def __init__(self, reads):
        self.reads = reads
        sizes = [node_size(read) for read in reads]
        columns = min(len(reads), STACK_PER_ROW)
        rows = int(math.ceil(len(reads) / float(STACK_PER_ROW)))
        self.read_height = max(height for _, height in sizes)
        self.pitch = self.read_height + STACK_ROW_GAP
        self.width = (columns - 1) * STACK_COLUMN_SPACING + max(
            width for width, _ in sizes
        )
        self.height = (rows - 1) * self.pitch + self.read_height


class Slots(object):
    def __init__(self):
        self.trunk = None
        self.sides = {}
        self.extras = []
        self.fan = []
        self.stacks = []

    def side_children(self):
        return [(side, self.sides[side]) for side in (-1, 1) if side in self.sides]


class Graph(object):
    def __init__(self, nodes):
        self.nodes = sorted(nodes, key=position_key)
        members = {node: node for node in self.nodes}
        self.inputs = {node: [] for node in self.nodes}
        self.consumers = {node: [] for node in self.nodes}
        self.hidden_sources = set()
        self.linked = set()
        for target in self.nodes:
            hidden = hides_inputs(target)
            for index in range(target.inputs()):
                source = members.get(target.input(index))
                if source is None:
                    continue
                self.linked.update((source, target))
                if hidden:
                    self.hidden_sources.add(source)
                    continue
                self.inputs[target].append((index, source))
                self.consumers[source].append((target, index))
        for owner, reads in generation_reads(self):
            self.add_stack(owner, reads)
        for source, target in related_pairs(self.nodes):
            self.add_virtual_link(source, target)

    def add_edge(self, source, target, index):
        self.inputs[target].insert(0, (index, source))
        self.consumers[source].append((target, index))
        self.linked.update((source, target))

    def add_stack(self, owner, reads):
        stack = ReadStack(reads)
        self.nodes = [node for node in self.nodes if node not in reads]
        self.inputs[stack] = []
        self.consumers[stack] = []
        self.add_edge(stack, owner, STACK_INDEX)

    def add_virtual_link(self, source, target):
        if self.consumers[source]:
            return
        if any(index == VIRTUAL_INDEX for index, _ in self.inputs[target]):
            return
        if target in upstream_nodes(self, source):
            return
        self.add_edge(source, target, VIRTUAL_INDEX)
        link_cache[(source, target)] = True


class Forest(object):
    def __init__(self, graph, chains=()):
        self.loose_width = loose_groups_width(chains)
        self.roots = [node for node in graph.nodes if not graph.consumers[node]]
        self.children = {}
        self.cross_edges = []
        claimed = set()
        sizes = {root: upstream_count(graph, root) for root in self.roots}
        self.sizes = sizes
        claim_order = sorted(
            self.roots,
            key=lambda root: (sizes[root], root.ypos(), root.fullName()),
            reverse=True,
        )
        for root in claim_order:
            claimed.add(root)
            self.claim_upstream(graph, root, claimed)
        self.top_aligned = set(
            root
            for root in self.roots
            if root in graph.hidden_sources or root not in graph.linked
        )
        self.isolated = set(root for root in self.roots if root not in graph.linked)

    def claim_upstream(self, graph, root, claimed):
        stack = [(root, None, None)]
        while stack:
            node, consumer, index = stack.pop()
            if consumer is not None:
                if node in claimed:
                    self.cross_edges.append((node, consumer, index))
                    continue
                claimed.add(node)
                self.children.setdefault(consumer, []).append((index, node))
            for input_index, source in reversed(graph.inputs[node]):
                stack.append((source, node, input_index))

    def children_with(self, hidden):
        children = {key: list(items) for key, items in self.children.items()}
        for (_, target, index), dot in hidden.items():
            if dot is not None:
                children.setdefault(target, []).append((index, dot))
        return children

    def ordered_roots(self, excluded=()):
        roots = [root for root in self.roots if root not in excluded]
        connected = [root for root in roots if root not in self.isolated]
        isolated = [root for root in roots if root in self.isolated]
        return connected + isolated


class Placement(object):
    def __init__(self):
        self.columns = {}
        self.rows = {}
        self.centers = {}
        self.segments = []
        self.row_centers = {}
        self.rects = {}
        self.routes = {}
        self.origin = 0.0
        self.anchor = None
        self.last_height = DEFAULT_NODE_SIZE[1]


def upstream_nodes(graph, root):
    visited = set([root])
    stack = [root]
    while stack:
        for _, source in graph.inputs[stack.pop()]:
            if source not in visited:
                visited.add(source)
                stack.append(source)
    return visited


def upstream_count(graph, root):
    return len(upstream_nodes(graph, root))


def is_generation_read(node, gizmo):
    if node.Class() not in READ_CLASSES:
        return False
    name = node.fullName()
    prefix = gizmo.fullName()
    return any(name.startswith(prefix + suffix) for suffix in GENERATION_SUFFIXES)


def stack_order(node):
    return node.ypos(), node.xpos(), node.fullName()


def generation_reads(graph):
    by_name = {node.fullName(): node for node in graph.nodes}
    for gizmo in [node for node in graph.nodes if is_gizmo(node)]:
        reads = [
            node
            for node in graph.nodes
            if node not in graph.linked and is_generation_read(node, gizmo)
        ]
        if reads:
            owner = by_name.get(gizmo.fullName() + "Read", gizmo)
            yield owner, sorted(reads, key=stack_order)


def file_key(node):
    path = nuke.filename(node) or ""
    path = re.sub(r"%0?(\d*)d", lambda match: "#" * int(match.group(1) or 1), path)
    return os.path.normcase(os.path.normpath(path)) if path else None


def is_isolated(node, names, is_top):
    if len(connected_indices(node)) != (0 if is_top else 1):
        return False
    links = node.dependent(LINK_FLAGS, True) + node.dependencies(LINK_FLAGS)
    return all(
        other.fullName() in names or other.Class() in EXCLUDED_CLASSES
        for other in links
    )


def loose_chain(graph, bottom):
    chain = [bottom]
    while graph.inputs[chain[0]]:
        inputs = graph.inputs[chain[0]]
        if len(chain) >= MAX_LOOSE_CHAIN or len(inputs) != 1 or inputs[0][0] < 0:
            return None
        source = inputs[0][1]
        if len(graph.consumers[source]) != 1:
            return None
        chain.insert(0, source)
    is_input = chain[0].Class() in READ_CLASSES
    if is_input and any(connected_indices(node) not in ([], [0]) for node in chain):
        return None
    names = set(node.fullName() for node in chain)
    if all(is_isolated(node, names, node is chain[0]) for node in chain):
        return chain


def take_loose_chains(graph):
    roots = [node for node in graph.nodes if not graph.consumers[node]]
    chains = [loose_chain(graph, root) for root in roots]
    chains = [chain for chain in chains if chain]
    loose = set(node for chain in chains for node in chain)
    graph.nodes = [node for node in graph.nodes if node not in loose]
    return sorted(chains, key=lambda chain: stack_order(chain[0]))


def is_gizmo(node):
    return node.knob(GIZMO_KNOB) is not None


def written_file(node):
    if node.Class() in WRITE_CLASSES:
        return file_key(node)
    if isinstance(node, nuke.Group):
        for inner in node.nodes():
            if inner.Class() in WRITE_CLASSES:
                return file_key(inner)


def related_pairs(nodes):
    by_name = {node.fullName(): node for node in nodes}
    reads = {}
    for node in nodes:
        if node.Class() in READ_CLASSES:
            reads.setdefault(file_key(node), node)
    reads.pop(None, None)
    for node in nodes:
        main_read = by_name.get(node.fullName() + "Read")
        if is_gizmo(node) and main_read is not None:
            yield node, main_read
        elif written_file(node) in reads:
            yield node, reads[written_file(node)]


def position_key(node):
    return node.xpos(), node.ypos(), node.fullName()


def hides_inputs(node):
    knob = node.knob("hide_input")
    return knob is not None and bool(knob.value())


def connected_inputs(node):
    return [node.input(index) for index in range(node.inputs()) if node.input(index)]


def node_size(key):
    if isinstance(key, HiddenDot):
        return DOT_SIZE
    if isinstance(key, ReadStack):
        return key.width, key.read_height
    if key not in size_cache:
        size_cache[key] = measure_node(key)
    return size_cache[key]


def measure_node(node):
    width, height = node.screenWidth(), node.screenHeight()
    if width > 0 and height > 0:
        return width, height
    if node.Class() == "Dot":
        return DOT_SIZE
    return DEFAULT_NODE_SIZE


def mask_input_index(node):
    if isinstance(node, (HiddenDot, ReadStack)):
        return None
    has_mask = any(
        node.knob(name) is not None for name in ("maskChannelInput", "maskChannel")
    )
    if has_mask and node.minInputs() >= 2:
        return node.minInputs() - 1


def grid_width():
    preferences = nuke.toNode("preferences") if nuke.GUI else None
    knob = preferences.knob("GridWidth") if preferences is not None else None
    if knob is None:
        return DEFAULT_GRID_WIDTH
    return max(float(knob.value()), 1.0)


def connected_indices(node):
    return [index for index in range(node.inputs()) if node.input(index)]


def is_tight_link(child, parent):
    if isinstance(child, HiddenDot) or isinstance(parent, HiddenDot):
        return False
    if (child, parent) not in link_cache:
        link_cache[(child, parent)] = measure_tight_link(child, parent)
    return link_cache[(child, parent)]


def measure_tight_link(child, parent):
    return connected_inputs(parent) == [child]


def column_step(grid_width):
    return grid_width * math.ceil(MIN_COLUMN_WIDTH / grid_width)


def new_balance():
    return {-1: 0, 1: 0}


def choose_side(slots, balance, blocked, is_mask):
    preference = (1, -1) if is_mask else (-1, 1)
    sides = [side for side in preference if side != blocked]
    sides = [side for side in sides if side not in slots.sides]
    if not sides:
        return None
    return min(sides, key=lambda side: (balance[side], preference.index(side)))


def center_out(items):
    ordered = []
    for position, item in enumerate(items):
        if position % 2:
            ordered.insert(0, item)
        else:
            ordered.append(item)
    return ordered


def assign_fan(node, items, blocked, weights):
    slots = Slots()
    by_weight = sorted(items, key=lambda item: (weights.get(item[1], 1), item[0]))
    lateral = [item for item in by_weight if item[0] != 0][:2]
    mask = mask_input_index(node)
    lateral.sort(key=lambda item: (item[0] == mask, item[0]))
    for side, (_, child) in zip((-1, 1), lateral):
        if side != blocked:
            slots.sides[side] = child
    used = list(slots.sides.values())
    rest = [item for item in by_weight if all(item[1] is not x for x in used)]
    rest.sort(key=lambda item: (-weights.get(item[1], 1), item[0]))
    ordered = center_out(rest)
    primary = next((item for item in ordered if item[0] == 0), None)
    if primary is not None:
        ordered.remove(primary)
        ordered.insert(len(ordered) // 2, primary)
    slots.fan = [child for _, child in ordered]
    return slots


def assign_slots(node, items, blocked, balance, weights):
    inputs = [item for item in items if item[0] != STACK_INDEX]
    if len(inputs) >= FAN_INPUTS:
        slots = assign_fan(node, inputs, blocked, weights)
    else:
        slots = assign_inputs(node, inputs, blocked, balance, weights)
    slots.stacks = [child for index, child in items if index == STACK_INDEX]
    return slots


def assign_inputs(node, items, blocked, balance, weights):
    slots = Slots()
    mask = mask_input_index(node)
    ordered = sorted(items, key=lambda item: item[0])
    candidates = [item for item in ordered if item[0] != mask]
    primary = [item for item in candidates if item[0] == 0]
    virtual = [item for item in candidates if item[0] == VIRTUAL_INDEX]
    if primary:
        slots.trunk = primary[0][1]
    elif virtual:
        slots.trunk = virtual[0][1]
    elif candidates:
        slots.trunk = max(candidates, key=lambda item: weights.get(item[1], 1))[1]
    balance = dict(balance)
    side_items = [item for item in ordered if item[1] is not slots.trunk]
    for index, child in sorted(side_items, key=lambda item: -weights.get(item[1], 1)):
        side = choose_side(slots, balance, blocked, index == mask)
        if side is None:
            slots.extras.append(child)
            continue
        slots.sides[side] = child
        balance[side] += weights.get(child, 1)
    return slots


def commit_balance(slots, balance, weights):
    for side, child in slots.side_children():
        balance[side] += weights.get(child, 1)


def insert_elbow(key, link, children, slots, weights):
    parent, index, side = link
    elbow = RouteDot(key, parent, index)
    children[parent] = [
        (item_index, elbow if item is key else item)
        for item_index, item in children[parent]
    ]
    children[elbow] = [(0, key)]
    slots[parent].sides[side] = elbow
    weights[elbow] = weights.get(key, 1)
    items = children[elbow]
    slots[elbow] = assign_slots(elbow, items, -side, new_balance(), weights)


def subtree_weights(root, children):
    weights = {}
    for key in post_order(root, children):
        items = children.get(key, ())
        weights[key] = 1 + sum(weights[child] for _, child in items)
    return weights


def compute_slots(root, children):
    weights = subtree_weights(root, children)
    slots = {}
    stack = []
    stack.append((root, 0, None, new_balance()))
    while stack:
        key, blocked, link, balance = stack.pop()
        items = children.get(key, [])
        current = assign_slots(key, items, blocked, balance, weights)
        if current.extras and blocked:
            insert_elbow(key, link, children, slots, weights)
            current = assign_slots(key, items, 0, balance, weights)
        commit_balance(current, balance, weights)
        slots[key] = current
        if current.trunk is not None:
            stack.append((current.trunk, 0, None, balance))
        for side, child in current.side_children():
            index = child_index(children, key, child)
            stack.append((child, -side, (key, index, side), new_balance()))
        for child in current.extras + current.fan + current.stacks:
            stack.append((child, 0, None, new_balance()))
    return slots


def child_index(children, parent, child):
    for index, item in children.get(parent, ()):
        if item is child:
            return index


def side_offset(contour, child_contour, side, row_shift, step):
    distance = step
    for row, (left, right) in child_contour.items():
        parent_row = contour.get(row + row_shift)
        if parent_row is None:
            continue
        if side < 0:
            needed = right + COLUMN_GAP - parent_row[0]
        else:
            needed = parent_row[1] + COLUMN_GAP - left
        distance = max(distance, needed)
    return side * math.ceil(distance / step - 1e-9) * step


def merge_contour(contour, child_contour, offset, row_shift):
    for row, (left, right) in child_contour.items():
        bounds = contour.setdefault(row + row_shift, [left + offset, right + offset])
        bounds[0] = min(bounds[0], left + offset)
        bounds[1] = max(bounds[1], right + offset)


def attach_child(child, offset, row_shift, contour, contours, relative):
    relative[child] = (offset, row_shift)
    merge_contour(contour, contours.pop(child), offset, row_shift)


def fan_rows(offsets, step):
    reach = max(abs(offsets[0]), abs(offsets[-1]))
    return NORMAL_ROWS + int(math.ceil(reach / step - 1e-9))


def pack_row(children, contours, step):
    row = {}
    offsets = []
    for child in children:
        offset = side_offset(row, contours[child], 1, 0, step) if offsets else 0.0
        merge_contour(row, contours[child], offset, 0)
        offsets.append(offset)
    middle = offsets[(len(offsets) - 1) // 2]
    return [offset - middle for offset in offsets]


def layout_fan(contour, slots, contours, relative, step):
    offsets = pack_row(slots.fan, contours, step)
    rows = fan_rows(offsets, step)
    for child, offset in zip(slots.fan, offsets):
        attach_child(child, offset, -rows, contour, contours, relative)
    reserve_link(contour, -rows, offsets[0])
    reserve_link(contour, -rows, offsets[-1])
    edges = {-1: min(offsets[0], -step), 1: max(offsets[-1], step)}
    for side, child in slots.side_children():
        offset = side_offset(contour, contours[child], side, 0, step)
        offset = side * max(abs(offset), abs(edges[side]))
        attach_child(child, offset, 0, contour, contours, relative)


def with_spine(contour, child_contour, row_shift):
    spine = {row: list(bounds) for row, bounds in contour.items()}
    for row in child_contour:
        if row + row_shift < 0:
            bounds = spine.setdefault(row + row_shift, [0.0, 0.0])
            bounds[0] = min(bounds[0], -LINE_CLEARANCE)
            bounds[1] = max(bounds[1], LINE_CLEARANCE)
    return spine


def collides(contour, child_contour, row_shift):
    for row, (left, right) in child_contour.items():
        bounds = contour.get(row + row_shift)
        if bounds and left - COLUMN_GAP < bounds[1] and bounds[0] < right + COLUMN_GAP:
            return True
    return False


def block_gap_rows():
    return int(math.ceil(BLOCK_GAP / ROW_UNIT - 1e-9))


def padded_contour(contour):
    padded = {}
    for row, (left, right) in contour.items():
        rows = range(row - block_gap_rows(), row + 1) if row < 0 else (row,)
        for target in rows:
            bounds = padded.setdefault(target, [left, right])
            bounds[0] = min(bounds[0], left)
            bounds[1] = max(bounds[1], right)
    return padded


def trunk_shift(contour, child_contour, start):
    if not collides(contour, child_contour, start):
        return start
    padded = padded_contour(contour)
    shift = start - 1
    while collides(padded, child_contour, shift):
        shift -= 1
    return shift


def stack_contour(stack):
    half_width = stack.width / 2.0
    rows = int(math.ceil(stack.height / ROW_UNIT)) + 1
    return {row: [-half_width, half_width] for row in range(rows)}


def layout_node(key, slots, contours, relative, step):
    if isinstance(key, ReadStack):
        return stack_contour(key)
    half_width = node_size(key)[0] / 2.0
    contour = {0: [-half_width, half_width]}
    if slots.fan:
        layout_fan(contour, slots, contours, relative, step)
    else:
        layout_inputs(key, contour, slots, contours, relative, step)
    for child in slots.stacks:
        offset = side_offset(contour, contours[child], 1, 0, step)
        attach_child(child, offset, 0, contour, contours, relative)
    return contour


def layout_inputs(key, contour, slots, contours, relative, step):
    for side, child in slots.side_children():
        spine = with_spine(contour, contours[child], 0)
        offset = side_offset(spine, contours[child], side, 0, step)
        attach_child(child, offset, 0, contour, contours, relative)
    if slots.trunk is not None:
        start = -1 if is_tight_link(slots.trunk, key) else -NORMAL_ROWS
        shift = trunk_shift(contour, contours[slots.trunk], start)
        attach_child(slots.trunk, 0.0, shift, contour, contours, relative)
        reserve_link(contour, shift, 0.0)
    for child in slots.extras:
        offset = side_offset(contour, contours[child], -1, -NORMAL_ROWS, step)
        attach_child(child, offset, -NORMAL_ROWS, contour, contours, relative)
        reserve_link(contour, -NORMAL_ROWS, offset)


def reserve_link(contour, row_shift, offset):
    left = min(offset, 0.0) - LINE_CLEARANCE
    right = max(offset, 0.0) + LINE_CLEARANCE
    for row in range(row_shift + 1, 0):
        bounds = contour.setdefault(row, [left, right])
        bounds[0] = min(bounds[0], left)
        bounds[1] = max(bounds[1], right)


def post_order(root, children):
    order = []
    stack = [(root, False)]
    while stack:
        key, expanded = stack.pop()
        if expanded:
            order.append(key)
            continue
        stack.append((key, True))
        for _, child in children.get(key, ()):
            stack.append((child, False))
    return order


def resolve_tree(root, children, relative):
    absolute = {root: (0.0, 0)}
    stack = [root]
    while stack:
        key = stack.pop()
        column, row = absolute[key]
        for _, child in children.get(key, ()):
            offset, row_offset = relative[child]
            absolute[child] = (column + offset, row + row_offset)
            stack.append(child)
    return absolute


def layout_tree(root, children, step):
    slots = compute_slots(root, children)
    contours = {}
    relative = {}
    for key in post_order(root, children):
        contours[key] = layout_node(key, slots[key], contours, relative, step)
    return contours[root], resolve_tree(root, children, relative)


def tree_shift(contour, cursor, step):
    left = min(bounds[0] for bounds in contour.values())
    if cursor is None:
        return 0.0
    return math.ceil((cursor - left) / step - 1e-9) * step


def place_trees(forest, children, step, pendants):
    trees = []
    principal = main_output(forest)
    roots = forest.ordered_roots(pendants)
    roots = [principal] + [root for root in roots if root is not principal]
    for root in roots:
        contour, absolute = layout_tree(root, children, step)
        trees.append((root, contour, absolute))
    secondary_bottom = min(trees[0][1]) - math.ceil(BLOCK_GAP / ROW_UNIT)
    placement = Placement()
    cursor = None
    for root, contour, absolute in trees:
        row_shift = 0 if root is principal else secondary_bottom
        shift = tree_shift(contour, cursor, step)
        right = max(bounds[1] for bounds in contour.values()) + shift
        if root is principal and forest.loose_width:
            left = min(bounds[0] for bounds in contour.values()) + shift
            right = max(right, left + forest.loose_width)
        cursor = right + COLUMN_GAP + TREE_GAP_COLUMNS * step
        for key, (column, row) in absolute.items():
            placement.columns[key] = column + shift
            placement.rows[key] = row + row_shift
    return placement


def row_heights(placement):
    heights = {}
    for key, row in placement.rows.items():
        heights[row] = max(heights.get(row, 0), node_size(key)[1])
    return heights


def row_pitch(upper_height, lower_height, row_grid):
    return max(row_grid, upper_height / 2.0 + lower_height / 2.0 + TIGHT_GAP)


def row_offsets(placement, row_grid):
    nodes_by_row = {}
    for key, row in placement.rows.items():
        nodes_by_row.setdefault(row, []).append(key)
    first, last = min(nodes_by_row), max(nodes_by_row)
    offsets = {}
    previous = []
    for row in range(first, last + 1):
        offset = offsets[row - 1] + row_grid if row > first else 0.0
        current = []
        for key in nodes_by_row.get(row, ()):
            width, height = node_size(key)
            column = placement.columns[key]
            left, right = column - width / 2.0, column + width / 2.0
            for upper_left, upper_right, bottom in previous:
                if left < upper_right and upper_left < right:
                    offset = max(offset, bottom + TIGHT_GAP + height / 2.0)
            current.append((left, right, height / 2.0))
        offsets[row] = offset
        previous.extend((left, right, offset + half) for left, right, half in current)
    return offsets


def resolve_centers(placement, anchor, row_grid):
    width, height = node_size(anchor)
    anchor_x = anchor.xpos() + width / 2.0
    anchor_y = anchor.ypos() + height / 2.0
    offsets = row_offsets(placement, row_grid)
    anchor_offset = offsets[placement.rows[anchor]]
    placement.origin = anchor_x - placement.columns[anchor]
    for row, offset in offsets.items():
        placement.row_centers[row] = anchor_y + offset - anchor_offset
    placement.last_height = row_heights(placement)[max(offsets)]
    for key, row in placement.rows.items():
        center_x = placement.origin + placement.columns[key]
        placement.centers[key] = (center_x, placement.row_centers[row])


def row_center(placement, row, row_grid):
    centers = placement.row_centers
    last = max(centers)
    upper_height = placement.last_height
    while row > last:
        pitch = row_pitch(upper_height, DEFAULT_NODE_SIZE[1], row_grid)
        centers[last + 1] = centers[last] + pitch
        upper_height = DEFAULT_NODE_SIZE[1]
        last += 1
    return centers[row]


def rects_overlap(first, second):
    horizontal = first[0] < second[2] and second[0] < first[2]
    return horizontal and first[1] < second[3] and second[1] < first[3]


def set_position(placement, key, column, row, row_grid):
    placement.columns[key] = column
    placement.rows[key] = row
    center_y = row_center(placement, row, row_grid)
    placement.centers[key] = (placement.origin + column, center_y)
    placement.rects.pop(key, None)


def remove_position(placement, key):
    values_list = (
        placement.columns,
        placement.rows,
        placement.centers,
        placement.rects,
    )
    for values in values_list:
        values.pop(key, None)


def is_free(placement, key):
    rect = node_rect(placement, key)
    for other in placement.centers:
        if other is not key and rects_overlap(rect, node_rect(placement, other)):
            return False
    return True


def route_is_clear(placement, route):
    if not (is_free(placement, route) and is_free(placement, route.target)):
        return False
    for source, target in ((route.source, route), (route, route.target)):
        if not path_is_clear(placement, source, target):
            return False
    return True


def route_columns(base, step):
    columns = []
    for distance in range(1, MAX_ROUTE_COLUMNS + 1):
        columns.extend((base + distance * step, base - distance * step))
    return columns


def place_route(placement, edge, row_grid, step):
    source, pendant, index = edge
    route = RouteDot(source, pendant, index)
    row = placement.rows[source]
    for column in route_columns(placement.columns[source], step):
        set_position(placement, route, column, row, row_grid)
        set_position(placement, pendant, column, row + NORMAL_ROWS, row_grid)
        if route_is_clear(placement, route):
            add_segment(placement, source, route)
            add_segment(placement, route, pendant)
            placement.routes[edge] = route
            return True
        remove_position(placement, route)
        remove_position(placement, pendant)
    return False


def find_pendants(forest, children, hidden):
    pendants = []
    for root in forest.roots:
        if root in forest.top_aligned or children.get(root):
            continue
        edges = [edge for edge in forest.cross_edges if edge[1] is root]
        if len(edges) == 1 and edges[0] not in hidden:
            pendants.append((root, edges[0]))
    return pendants


def pendant_order(placement, pendant, source):
    return placement.rows[source], placement.columns[source], pendant.fullName()


def place_pendants(placement, pendants, row_grid, step):
    failed = []
    ordered = sorted(
        pendants, key=lambda item: pendant_order(placement, item[0], item[1][0])
    )
    for _, edge in ordered:
        if not place_route(placement, edge, row_grid, step):
            failed.append(edge)
    return failed


def add_segment(placement, source, target):
    start = placement.centers[source]
    end = placement.centers[target]
    placement.segments.append((source, target, start, end))


def collect_segments(placement, children):
    for parent, items in children.items():
        for index, child in items:
            if index != STACK_INDEX:
                add_segment(placement, child, parent)


def compact_hidden_dots(placement):
    for dot in placement.centers:
        if not isinstance(dot, HiddenDot) or isinstance(dot, RouteDot):
            continue
        center_x, original_y = placement.centers[dot]
        target_x, target_y = placement.centers[dot.target]
        if abs(center_x - target_x) > EPSILON:
            continue
        center_y = target_y - NORMAL_ROWS * ROW_UNIT
        while center_y > original_y:
            placement.centers[dot] = (center_x, center_y)
            placement.rects.pop(dot, None)
            if is_free(placement, dot) and path_is_clear(placement, dot, dot.target):
                break
            center_y -= ROW_UNIT
        else:
            placement.centers[dot] = (center_x, original_y)
            placement.rects.pop(dot, None)


def compute_placement(forest, hidden, grid):
    children = forest.children_with(hidden)
    step = column_step(grid)
    pendants = find_pendants(forest, children, hidden)
    pendant_nodes = [pendant for pendant, _ in pendants]
    placement = place_trees(forest, children, step, pendant_nodes)
    anchor = main_output(forest)
    placement.anchor = anchor
    resolve_centers(placement, anchor, ROW_UNIT)
    compact_hidden_dots(placement)
    collect_segments(placement, children)
    failed = place_pendants(placement, pendants, ROW_UNIT, step)
    return placement, failed


def orientation(first, second, third):
    value = (second[0] - first[0]) * (third[1] - first[1]) - (second[1] - first[1]) * (
        third[0] - first[0]
    )
    if value > 1e-9:
        return 1
    if value < -1e-9:
        return -1
    return 0


def on_segment(first, second, point):
    within_x = min(first[0], second[0]) - 1e-9 <= point[0]
    within_x = within_x and point[0] <= max(first[0], second[0]) + 1e-9
    within_y = min(first[1], second[1]) - 1e-9 <= point[1]
    within_y = within_y and point[1] <= max(first[1], second[1]) + 1e-9
    return within_x and within_y


def segments_cross(first, second, third, fourth):
    turns = (
        orientation(first, second, third),
        orientation(first, second, fourth),
        orientation(third, fourth, first),
        orientation(third, fourth, second),
    )
    if turns[0] != turns[1] and turns[2] != turns[3]:
        return True
    touching = (
        (turns[0] == 0 and on_segment(first, second, third)),
        (turns[1] == 0 and on_segment(first, second, fourth)),
        (turns[2] == 0 and on_segment(third, fourth, first)),
        (turns[3] == 0 and on_segment(third, fourth, second)),
    )
    return any(touching)


def node_rect(placement, key):
    if key not in placement.rects:
        placement.rects[key] = measure_rect(placement, key)
    return placement.rects[key]


def measure_rect(placement, key):
    center_x, center_y = placement.centers[key]
    width, height = node_size(key)
    if isinstance(key, ReadStack):
        left = center_x - width / 2.0 - LINE_CLEARANCE
        top = center_y - height / 2.0 - LINE_CLEARANCE
        bottom = top + key.height + 2 * LINE_CLEARANCE
        return left, top, left + width + 2 * LINE_CLEARANCE, bottom
    half_width = width / 2.0 + LINE_CLEARANCE
    half_height = height / 2.0 + LINE_CLEARANCE
    return (
        center_x - half_width,
        center_y - half_height,
        center_x + half_width,
        center_y + half_height,
    )


def segment_hits_rect(start, end, rect):
    left, top, right, bottom = rect
    if max(start[0], end[0]) < left or min(start[0], end[0]) > right:
        return False
    if max(start[1], end[1]) < top or min(start[1], end[1]) > bottom:
        return False
    for point in (start, end):
        if left <= point[0] <= right and top <= point[1] <= bottom:
            return True
    corners = ((left, top), (right, top), (right, bottom), (left, bottom))
    for index, corner in enumerate(corners):
        following = corners[(index + 1) % 4]
        if segments_cross(start, end, corner, following):
            return True
    return False


def is_orthogonal(placement, edge):
    source, target, _ = edge
    source_x, source_y = placement.centers[source]
    target_x, target_y = placement.centers[target]
    if abs(source_x - target_x) < EPSILON:
        return source_y < target_y
    return abs(source_y - target_y) < EPSILON


def path_is_clear(placement, source, target):
    start = placement.centers[source]
    end = placement.centers[target]
    for key in placement.centers:
        if key is source or key is target:
            continue
        if segment_hits_rect(start, end, node_rect(placement, key)):
            return False
    for first, second, other_start, other_end in placement.segments:
        if any(key is source or key is target for key in (first, second)):
            continue
        if segments_cross(start, end, other_start, other_end):
            return False
    return True


def rejected_edges(forest, hidden, placement):
    rejected = []
    for edge in forest.cross_edges:
        if edge in hidden or edge in placement.routes:
            continue
        source, target, _ = edge
        orthogonal = is_orthogonal(placement, edge)
        if orthogonal and path_is_clear(placement, source, target):
            add_segment(placement, source, target)
        else:
            rejected.append(edge)
    return rejected


def hidden_marker(edge):
    source, target, index = edge
    if len(connected_inputs(target)) == 1:
        return None
    return HiddenDot(source, target, index)


def solve_layout(forest, grid):
    hidden = {}
    while True:
        placement, failed = compute_placement(forest, hidden, grid)
        rejected = failed or rejected_edges(forest, hidden, placement)
        if not rejected:
            return placement, hidden
        for edge in rejected:
            hidden[edge] = hidden_marker(edge)


def create_dot(dot, select):
    context = dot.target.parent()
    if context.fullName() == nuke.thisGroup().fullName():
        node = nuke.nodes.Dot()
    else:
        with context:
            node = nuke.nodes.Dot()
    node.setInput(0, dot.source)
    dot.target.setInput(dot.index, node)
    node.setSelected(select)
    return node


def create_hidden_dot(dot, select):
    node = create_dot(dot, select)
    node["hide_input"].setValue(True)
    node["label"].setValue(HIDDEN_DOT_LABEL)
    return node


def place_stack(stack, center):
    left = center[0] - stack.width / 2.0
    top = center[1] - stack.read_height / 2.0
    for index, read in enumerate(stack.reads):
        row, column = divmod(index, STACK_PER_ROW)
        x = left + column * STACK_COLUMN_SPACING
        read.setXYpos(int(round(x)), int(round(top + row * stack.pitch)))
    return stack.reads


def apply_placement(placement, hidden, select):
    nodes = {key: key for key in placement.centers if not isinstance(key, ReadStack)}
    for edge, dot in hidden.items():
        if dot is None:
            edge[1]["hide_input"].setValue(True)
        else:
            nodes[dot] = create_hidden_dot(dot, select)
    for key in placement.centers:
        if isinstance(key, RouteDot):
            nodes[key] = create_dot(key, select)
    for key, (center_x, center_y) in placement.centers.items():
        if isinstance(key, ReadStack):
            nodes.update(
                (read, read) for read in place_stack(key, (center_x, center_y))
            )
            continue
        width, height = node_size(key)
        x = int(round(center_x - width / 2.0))
        y = int(round(center_y - height / 2.0))
        nodes[key].setXYpos(x, y)
    return list(nodes.values())


def bypass_dot(dot):
    source = dot.input(0)
    name = dot.fullName()
    for consumer in dot.dependent(nuke.INPUTS | nuke.HIDDEN_INPUTS, False):
        for index in range(consumer.inputs()):
            node = consumer.input(index)
            if node is not None and node.fullName() == name:
                consumer.setInput(index, source)
    nuke.delete(dot)


def remove_dots(candidates):
    for node in candidates:
        if node.Class() == "Dot":
            bypass_dot(node)


def reset_hidden_inputs(nodes):
    names = set(node.fullName() for node in nodes)
    for node in nodes:
        sources = connected_inputs(node)
        if not hides_inputs(node) or not sources:
            continue
        if all(source.fullName() in names for source in sources):
            node["hide_input"].setValue(False)


def node_bounds(node):
    width, height = node_size(node)
    return node.xpos(), node.ypos(), node.xpos() + width, node.ypos() + height


def backdrop_bounds(backdrop):
    left, top = backdrop.xpos(), backdrop.ypos()
    right = left + int(backdrop["bdwidth"].value())
    return left, top, right, top + int(backdrop["bdheight"].value())


def contains_center(bounds, node):
    left, top, right, bottom = node_bounds(node)
    center_x, center_y = (left + right) / 2.0, (top + bottom) / 2.0
    return bounds[0] <= center_x <= bounds[2] and bounds[1] <= center_y <= bounds[3]


def area(bounds):
    return (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])


def encloses(outer, inner):
    return (
        outer[0] <= inner[0]
        and outer[1] <= inner[1]
        and (inner[2] <= outer[2] and inner[3] <= outer[3])
    )


def record_backdrops(backdrops, nodes):
    size_cache.clear()
    bounds = {backdrop: backdrop_bounds(backdrop) for backdrop in backdrops}
    by_area = sorted(backdrops, key=lambda backdrop: area(bounds[backdrop]))
    members = {backdrop: [] for backdrop in backdrops}
    for node in nodes:
        holders = [key for key in by_area if contains_center(bounds[key], node)]
        for backdrop in holders:
            if backdrop is holders[0] or encloses(bounds[backdrop], bounds[holders[0]]):
                members[backdrop].append(node)
    records = []
    for backdrop in backdrops:
        nested = [
            other
            for other in backdrops
            if encloses(bounds[backdrop], bounds[other])
            or encloses(bounds[other], bounds[backdrop])
        ]
        inner = [
            other
            for other in nested
            if other is not backdrop and encloses(bounds[backdrop], bounds[other])
        ]
        records.append((backdrop, members[backdrop], nested, inner))
    return records


def are_close(first, second):
    horizontal = max(first[0] - second[2], second[0] - first[2])
    vertical = max(first[1] - second[3], second[1] - first[3])
    return max(horizontal, vertical) <= BACKDROP_CLUSTER_GAP


def largest_cluster(nodes):
    bounds = [node_bounds(node) for node in nodes]
    remaining = set(range(len(nodes)))
    best = []
    while remaining:
        stack = [remaining.pop()]
        cluster = []
        while stack:
            index = stack.pop()
            cluster.append(index)
            near = [
                other for other in remaining if are_close(bounds[index], bounds[other])
            ]
            remaining.difference_update(near)
            stack.extend(near)
        if len(cluster) > len(best):
            best = cluster
    return [nodes[index] for index in sorted(best)]


def fitted_bounds(nodes, inner=()):
    bounds = [node_bounds(node) for node in nodes] + list(inner)
    return (
        min(item[0] for item in bounds) - BACKDROP_PADDING,
        min(item[1] for item in bounds) - BACKDROP_PADDING - BACKDROP_FONT_SIZE,
        max(item[2] for item in bounds) + BACKDROP_PADDING,
        max(item[3] for item in bounds) + BACKDROP_PADDING,
    )


def overlap_area(first, second):
    width = min(first[2], second[2]) - max(first[0], second[0])
    height = min(first[3], second[3]) - max(first[1], second[1])
    return max(width, 0) * max(height, 0)


def total_overlap(bounds, placed):
    return sum(overlap_area(bounds, other) for other in placed)


def without_overlap(nodes, placed):
    cluster = largest_cluster(nodes)
    while len(cluster) >= MIN_BACKDROP_NODES:
        if not total_overlap(fitted_bounds(cluster), placed):
            return cluster
        candidates = [
            [node for node in cluster if node is not removed] for removed in cluster
        ]
        best = min(
            candidates,
            key=lambda rest: total_overlap(fitted_bounds(rest), placed),
        )
        cluster = largest_cluster(best)
    return []


def fit_backdrop(backdrop, bounds):
    left, top, right, bottom = bounds
    backdrop.setXYpos(int(left), int(top))
    backdrop["bdwidth"].setValue(int(right - left))
    backdrop["bdheight"].setValue(int(bottom - top))
    label = backdrop["label"]
    label.setValue(re.sub(r"<[^>]*>", "", label.value()).strip())
    backdrop["note_font"].setValue(BACKDROP_FONT)
    backdrop["note_font_size"].setValue(BACKDROP_FONT_SIZE)


def choose_clusters(records):
    clusters = [(record, largest_cluster(record[1])) for record in records]
    clusters.sort(key=lambda item: (len(item[1]), item[0][0].fullName()))
    placed = {}
    chosen = []
    for record, cluster in clusters:
        backdrop, nested, inner = record[0], record[2], record[3]
        others = [bounds for key, bounds in placed.items() if key not in nested]
        cluster = without_overlap(cluster, others)
        if not cluster:
            nuke.delete(backdrop)
            continue
        children = [placed[key] for key in inner if key in placed]
        placed[backdrop] = fitted_bounds(cluster, children)
        chosen.append((backdrop, cluster, [key for key in inner if key in placed]))
    return chosen


def fit_boxes(chosen):
    boxes = {}
    for backdrop, cluster, inner in chosen:
        boxes[backdrop] = fitted_bounds(cluster, [boxes[key] for key in inner])
    return boxes


def owned_nodes(chosen):
    owned = {}
    for backdrop, cluster, inner in chosen:
        names = set(node.fullName() for node in cluster)
        for key in inner:
            names.update(owned[key])
        owned[backdrop] = names
    return owned


def expand(bounds, margin):
    left, top, right, bottom = bounds
    return left - margin, top - margin, right + margin, bottom + margin


def push_options(rect, box):
    center_x = (rect[0] + rect[2]) / 2.0
    center_y = (rect[1] + rect[3]) / 2.0
    options = []
    if center_x < box[0]:
        options.append((rect[2] + BACKDROP_MARGIN - box[0], 0, -1, box[0]))
    if center_x > box[2]:
        options.append((box[2] + BACKDROP_MARGIN - rect[0], 0, 1, box[2]))
    if center_y < box[1]:
        options.append((rect[3] + BACKDROP_MARGIN - box[1], 1, -1, box[1]))
    if center_y > box[3]:
        options.append((box[3] + BACKDROP_MARGIN - rect[1], 1, 1, box[3]))
    return options


def find_conflict(chosen, boxes, nodes):
    owned = owned_nodes(chosen)
    for backdrop, _, _ in chosen:
        box = boxes[backdrop]
        for node in nodes:
            if node.fullName() in owned[backdrop]:
                continue
            rect = node_bounds(node)
            if rects_overlap(rect, expand(box, BACKDROP_MARGIN - 1)):
                options = push_options(rect, box)
                if options:
                    return min(options)
    return None


def push_nodes(nodes, conflict, step):
    distance, axis, direction, cut = conflict
    unit = step if axis == 0 else ROW_UNIT
    offset = direction * math.ceil(distance / unit - 1e-9) * unit
    for node in nodes:
        rect = node_bounds(node)
        center = (rect[axis] + rect[axis + 2]) / 2.0
        if (center - cut) * direction > 0:
            if axis == 0:
                node.setXYpos(int(node.xpos() + offset), node.ypos())
            else:
                node.setXYpos(node.xpos(), int(node.ypos() + offset))


def restore_backdrops(records, nodes, anchor):
    chosen = choose_clusters(records)
    step = column_step(grid_width())
    origin = (anchor.xpos(), anchor.ypos()) if anchor else (0, 0)
    for _ in range(len(nodes) + 1):
        conflict = find_conflict(chosen, fit_boxes(chosen), nodes)
        if conflict is None:
            break
        push_nodes(nodes, conflict, step)
    offset_x = origin[0] - anchor.xpos() if anchor else 0
    offset_y = origin[1] - anchor.ypos() if anchor else 0
    if offset_x or offset_y:
        for node in nodes:
            node.setXYpos(node.xpos() + offset_x, node.ypos() + offset_y)
    for backdrop, bounds in fit_boxes(chosen).items():
        fit_backdrop(backdrop, bounds)
    return [backdrop for backdrop, _, _ in chosen]


def arrange_candidates(candidates, select_new_dots=False, replace_viewer=False):
    nodes = [node for node in candidates if node.Class() not in EXCLUDED_CLASSES]
    backdrops = [node for node in candidates if node.Class() == BACKDROP_CLASS]
    skipped = ("Dot", BACKDROP_CLASS) + ((VIEWER_CLASS,) if replace_viewer else ())
    untouched = [
        node
        for node in candidates
        if node.Class() in EXCLUDED_CLASSES and node.Class() not in skipped
    ]
    viewers = [node for node in candidates if node.Class() == VIEWER_CLASS]
    records = record_backdrops(backdrops, nodes)
    remove_dots(candidates)
    if not nodes:
        return backdrops + untouched
    placed, anchor, chains, output, principal = arrange(nodes, select_new_dots)
    loose = set(node.fullName() for chain in chains for node in chain)
    records = [
        (record[0], [node for node in record[1] if node.fullName() not in loose])
        + record[2:]
        for record in records
    ]
    restored = restore_backdrops(records, placed, anchor)
    grouped = place_loose(chains, principal, select_new_dots)
    if replace_viewer:
        untouched.append(replace_viewers(viewers, nodes[0].parent(), output))
    return placed + restored + grouped + untouched


def replace_viewers(viewers, context, output):
    for viewer in viewers:
        nuke.delete(viewer)
    with context:
        viewer = nuke.nodes.Viewer()
    if output is not None:
        viewer.setInput(0, output)
        width, height = node_size(output)
        x = output.xpos() + (width - node_size(viewer)[0]) / 2.0
        y = output.ypos() + height + TIGHT_GAP
        viewer.setXYpos(int(round(x)), int(round(y)))
    return viewer


def main_output(forest):
    roots = [root for root in forest.roots if root not in forest.isolated]
    return max(
        roots or forest.roots,
        key=lambda root: (forest.sizes[root], root.ypos(), root.fullName()),
    )


def chain_size(chain):
    sizes = [node_size(node) for node in chain]
    height = sum(size[1] for size in sizes) + (len(chain) - 1) * LOOSE_GAP
    return max(size[0] for size in sizes), height


def layout_chains(chains, left, bottom):
    pitch = max(chain_size(chain)[0] for chain in chains) + LOOSE_COLUMN_GAP
    starts = range(0, len(chains), LOOSE_PER_ROW)
    rows = [chains[start:][:LOOSE_PER_ROW] for start in starts]
    heights = [max(chain_size(chain)[1] for chain in row) for row in rows]
    top = bottom - sum(heights) - (len(rows) - 1) * LOOSE_ROW_GAP
    for row, height in zip(rows, heights):
        for column, chain in enumerate(row):
            center_x = left + column * pitch + (pitch - LOOSE_COLUMN_GAP) / 2.0
            y = top
            for node in chain:
                width, node_height = node_size(node)
                node.setXYpos(int(round(center_x - width / 2.0)), int(round(y)))
                y += node_height + LOOSE_GAP
        top += height + LOOSE_ROW_GAP


def create_backdrop(context, label, color, select):
    with context:
        backdrop = nuke.nodes.BackdropNode(label=label, tile_color=color)
    backdrop.setSelected(select)
    return backdrop


def loose_group_width(chains):
    columns = min(len(chains), LOOSE_PER_ROW)
    pitch = max(chain_size(chain)[0] for chain in chains) + LOOSE_COLUMN_GAP
    return columns * pitch - LOOSE_COLUMN_GAP + 2 * BACKDROP_PADDING


def loose_groups_width(chains):
    groups = [
        [chain for chain in chains if (chain[0].Class() in READ_CLASSES) is is_input]
        for _, _, is_input in LOOSE_GROUPS
    ]
    widths = [loose_group_width(group) for group in groups if group]
    return sum(widths) + max(len(widths) - 1, 0) * BACKDROP_MARGIN * 2


def layout_bounds(chains, principal):
    if not principal:
        bounds = [node_bounds(node) for chain in chains for node in chain]
        return min(item[0] for item in bounds), max(item[3] for item in bounds)
    bounds = [node_bounds(node) for node in principal]
    left = min(item[0] for item in bounds)
    bottom = min(item[1] for item in bounds) - BLOCK_GAP - BACKDROP_PADDING
    return left + BACKDROP_PADDING, bottom


def place_loose(chains, principal, select):
    if not chains:
        return []
    left, bottom = layout_bounds(chains, principal)
    context = chains[0][0].parent()
    grouped = []
    for label, color, is_input in LOOSE_GROUPS:
        group = [
            chain for chain in chains if (chain[0].Class() in READ_CLASSES) is is_input
        ]
        if not group:
            continue
        layout_chains(group, left, bottom)
        members = [node for chain in group for node in chain]
        bounds = fitted_bounds(members)
        backdrop = create_backdrop(context, label, color, select)
        fit_backdrop(backdrop, bounds)
        left = bounds[2] + BACKDROP_MARGIN * 2 + BACKDROP_PADDING
        grouped += members + [backdrop]
    return grouped


def arrange(nodes, select_new_dots=False):
    size_cache.clear()
    link_cache.clear()
    reset_hidden_inputs(nodes)
    graph = Graph(nodes)
    chains = take_loose_chains(graph)
    if not graph.nodes:
        return [], None, chains, None, []
    forest = Forest(graph, chains)
    placement, hidden = solve_layout(forest, grid_width())
    placed = apply_placement(placement, hidden, select_new_dots)
    output = main_output(forest)
    principal = []
    for key in upstream_nodes(graph, output):
        principal.extend(key.reads if isinstance(key, ReadStack) else [key])
    return placed, placement.anchor, chains, output, principal


def main():
    selected = nuke.selectedNodes()
    candidates = selected or nuke.allNodes()
    has_nodes = any(node.Class() not in EXCLUDED_CLASSES for node in candidates)
    undo = nuke.Undo()
    undo.begin("Arrange Nodes")
    try:
        arrange_candidates(candidates, bool(selected), not selected)
    finally:
        undo.end()
    if not has_nodes:
        nuke.message("No nodes to arrange.")
