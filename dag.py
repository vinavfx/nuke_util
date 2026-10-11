# -----------------------------------------------------------
# AUTHOR --------> Francisco Contreras
# OFFICE --------> Senior VFX Compositor, Software Developer
# WEBSITE -------> https://vinavfx.com
# -----------------------------------------------------------
import nuke  # type: ignore

from .pyside import QApplication, QCursor, QPoint, QRectF, QTransform

app = QApplication.instance()


def get_dag_widgets(visible=True):
    dags = []
    application = app or QApplication.instance()
    if application is None:
        return dags
    all_widgets = QApplication.allWidgets()
    for widget in all_widgets:
        if "DAG" in widget.objectName():
            if not visible or widget.isVisible():
                dags.append(widget)
    return dags


def get_active_dag_widget():
    visible_dags = get_dag_widgets(visible=True)
    for dag in visible_dags:
        if dag.hasFocus():
            return dag

    if visible_dags:
        return visible_dags[0]


def get_cursor_graph_position():
    dag = get_active_dag_widget()
    if not dag:
        return 0, 0

    dag_rect = dag.geometry()
    transform = QTransform()
    scale = nuke.zoom()
    offset = dag_rect.center() / scale - QPoint(*nuke.center())
    transform.scale(scale, scale)
    transform.translate(offset.x(), offset.y())

    offset = dag.mapToGlobal(QPoint(dag.rect().x(), dag.rect().y()))

    pos = QCursor.pos() - offset
    rect = QRectF(pos.x(), pos.y(), 1, 1)

    inverted_rect = transform.inverted()[0].mapRect(rect)
    return int(inverted_rect.x()), int(inverted_rect.y())
