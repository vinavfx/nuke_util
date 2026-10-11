# -----------------------------------------------------------
# AUTHOR --------> Francisco Contreras
# OFFICE --------> Senior VFX Compositor, Software Developer
# WEBSITE -------> https://vinavfx.com
# -----------------------------------------------------------
import nuke  # type: ignore

from .dag import get_active_dag_widget


def get_current_group():
    dag = get_active_dag_widget()
    if not dag:
        return
    title = dag.windowTitle().strip()
    if title == "Node Graph" or not title:
        return nuke.root()
    return nuke.toNode("root." + title.split()[0])


def get_selected_nodes():
    current_group = get_current_group()
    if not current_group:
        return
    current_group.begin()
    try:
        return nuke.selectedNodes()
    finally:
        current_group.end()


def get_selected_node():
    nodes = get_selected_nodes()
    if nodes is None:
        return
    if len(nodes) != 1:
        nuke.message("Select only one node !")
        return
    return nodes[0]
