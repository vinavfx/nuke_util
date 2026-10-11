# -----------------------------------------------------------
# AUTHOR --------> Francisco Contreras
# OFFICE --------> Senior VFX Compositor, Software Developer
# WEBSITE -------> https://vinavfx.com
# -----------------------------------------------------------
import nuke  # type: ignore

from .pyside import QApplication, QDialog, QScreen, QStackedWidget, Qt, QWidget

if not hasattr(nuke, "panels"):
    nuke.panels = {}
if not hasattr(nuke, "float_panels"):
    nuke.float_panels = {}


def register_docked_panel(widget_name, label, stacked_widget=None):
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
        try:
            add_panel()
        finally:
            if last_focus_widget:
                last_focus_widget.setFocus()

    return panel


def show_panel(panel_name, panel, minimum_size=None):
    widget = nuke.panels[panel_name]()
    is_docked = False

    if widget is not None:
        stacked_widget, child = find_stacked_widget_parent(widget)
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


def create_floating_panel(widget, name):
    if name in nuke.float_panels:
        return

    main_widget = widget()
    nuke.float_panels[name] = main_widget


def find_stacked_widget_parent(widget):
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
        super().__init__()

        self.setWindowFlags(Qt.Tool)

    def center_window(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        center = QScreen.availableGeometry(screen).center()
        frame = self.frameGeometry()
        frame.moveCenter(center)
        self.move(frame.topLeft())

    def showEvent(self, event):
        super().showEvent(event)
        self.activateWindow()
        self.setFocus()

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Escape:
            self.close()


class panel_widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.hidden = False
        self.margin = None

    def remove_parents_margin(self):
        stacked_widget, _ = find_stacked_widget_parent(self)

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
        super().showEvent(event)
        self.remove_parents_margin()
