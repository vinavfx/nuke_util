# -----------------------------------------------------------
# AUTHOR --------> Francisco Contreras
# OFFICE --------> Senior VFX Compositor, Software Developer
# WEBSITE -------> https://vinavfx.com
# -----------------------------------------------------------
import nuke  # type: ignore

from .pyside import (  # type: ignore
    Qt,  # type: ignore
    QApplication,  # type: ignore
    QWidget,  # type: ignore
    QStackedWidget,  # type: ignore
    QDialog,  # type: ignore
    QScreen,  # type: ignore
)

if not hasattr(nuke, "panels"):
    nuke.panels = {}
    nuke.float_panels = {}


def init(widget_name, label, stacked_widget=None):
    if not nuke.GUI:
        return

    from nukescripts import PythonPanel, registerPanel  # type: ignore

    class Panel(PythonPanel):
        def __init__(self, label, name, widget):
            PythonPanel.__init__(self, label, name)

            self.customKnob = nuke.PyCustom_Knob(
                name,
                "",
                "__import__('nukescripts').panels.WidgetKnob({})".format(widget),
            )

            nuke.panels[name] = lambda: (
                self.customKnob.getObject().widget
                if self.customKnob.getObject()
                else None
            )

            self.addKnob(self.customKnob)

    name = label.lower().replace(" ", "_")

    panel = Panel(label, name, widget_name)

    def add_panel():
        return panel.addToPane()

    menu = nuke.menu("Pane")
    menu.addCommand(label, add_panel)
    registerPanel(name, add_panel)

    if stacked_widget:
        last_focus_widget = QApplication.focusWidget()
        stacked_widget.setFocus()
        add_panel()

        if last_focus_widget:
            last_focus_widget.setFocus()

    return panel


def show_panel(panel_name, panel, minimum_size=None):
    widget = nuke.panels[panel_name]()
    is_docked = False

    if widget is not None:
        stacked_widget, child = get_stacked_widget(widget)
        if stacked_widget and child:
            stacked_widget.setCurrentWidget(child)
            is_docked = True

    if not is_docked and (widget is None or not widget.isVisible()):
        if panel is None:
            return

        panel.show()
        widget = nuke.panels[panel_name]()
        if widget is not None and minimum_size:
            window = widget.window()
            width, height = minimum_size
            window.resize(max(window.width(), width), max(window.height(), height))
            screen = QApplication.primaryScreen()
            if screen:
                frame = window.frameGeometry()
                frame.moveCenter(screen.availableGeometry().center())
                window.move(frame.topLeft())

    return widget


def init_float_panel(widget, name):
    if name in nuke.float_panels:
        return

    main_widget = widget()
    nuke.float_panels[name] = main_widget


def close_panel(panel_name):
    if panel_name not in nuke.panels:
        return

    widget = nuke.panels[panel_name]()
    if not widget:
        return

    stacked_widget, child = get_stacked_widget(widget)

    if stacked_widget and child:
        stacked_widget.removeWidget(child)

    return stacked_widget


def get_stacked_widget(widget):
    pwidget = widget

    for _ in range(10):
        widget = pwidget
        if not widget:
            break

        pwidget = widget.parent()

        if isinstance(pwidget, QStackedWidget):
            return pwidget, widget

    return None, None


class float_panel_widget(QDialog):
    def __init__(self):
        super(float_panel_widget, self).__init__()

        self.setWindowFlags(Qt.Tool)

    def center_window(self):
        centerPoint = QScreen.availableGeometry(QApplication.primaryScreen()).center()

        fg = self.frameGeometry()
        fg.moveCenter(centerPoint)

        self.move(fg.topLeft())

    def showEvent(self, event):
        super(float_panel_widget, self).showEvent(event)
        self.activateWindow()
        self.setFocus()

    def keyPressEvent(self, event):
        super(float_panel_widget, self).keyPressEvent(event)
        if event.key() == Qt.Key_Escape:
            self.close()


class panel_widget(QWidget):
    def __init__(self, parent=None):
        super(panel_widget, self).__init__(parent)

        self.hidden = False
        self.margin = None

    def remove_parents_margin(self):
        stacked_widget, _ = get_stacked_widget(self)

        if not stacked_widget:
            return

        stacked_widget.setStyleSheet("QScrollArea {border: none}")

        if self.margin is None:
            return

        pwidget = self
        for _ in range(4):
            pwidget = pwidget.parentWidget()
            pwidget.layout().setContentsMargins(0, 0, 0, 0)

        pwidget.layout().setContentsMargins(
            self.margin, self.margin, self.margin, self.margin
        )

    def updateValue(self):
        return

    def showEvent(self, event):
        super(panel_widget, self).showEvent(event)
        self.remove_parents_margin()
