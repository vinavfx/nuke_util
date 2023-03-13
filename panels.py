# Author: Francisco Jose Contreras Cuevas
# Office: VFX Artist - Senior Compositor
# Website: vinavfx.com
import nuke

from PySide2.QtWidgets import QWidget, QStackedWidget

nuke.panels = {}


def init(widget_name, label, stacked_widget=None):
    from nukescripts import PythonPanel, registerPanel

    class Panel(PythonPanel):
        def __init__(self, label, name, widget):
            PythonPanel.__init__(self, label, name)

            self.customKnob = nuke.PyCustom_Knob(
                name, "", "__import__('nukescripts').panels.WidgetKnob({})".format(widget))

            nuke.panels[name] = lambda: self.customKnob.getObject(
            ).widget if self.customKnob.getObject() else None

            self.addKnob(self.customKnob)

    name = label.lower().replace(' ', '_')

    panel = Panel(label, name, widget_name)

    def add_panel():
        return panel.addToPane()

    menu = nuke.menu('Pane')
    menu.addCommand(label, add_panel)
    registerPanel(name, add_panel)

    if stacked_widget:
        stacked_widget.setFocus()
        add_panel()


def close_panel(panel_name):
    if not panel_name in nuke.panels:
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


class panel_widget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.border = True
        self.prev_stacked_widget = None
        self.hidden = False

    def remove_parents_margin(self):
        parents = []

        pwidgt = self
        for _ in range(6):
            pwidgt = pwidgt.parentWidget()
            parents.append(pwidgt)

        for widget in parents:
            try:
                if not self.border:
                    widget.setStyleSheet('QWidget {border: none}')
                widget.layout().setContentsMargins(0, 0, 0, 0)
            except:
                pass

    def showEvent(self, event):
        super().showEvent(event)
        self.remove_parents_margin()
