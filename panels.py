# Author: Francisco Jose Contreras Cuevas
# Office: VFX Artist - Senior Compositor
# Website: vinavfx.com
import nuke
from nukescripts import PythonPanel, registerPanel

from PySide2.QtWidgets import QWidget


class Panel(PythonPanel):
    def __init__(self, label, name, widget):
        PythonPanel.__init__(self, label, name)

        self.customKnob = nuke.PyCustom_Knob(
            name, "", "__import__('nukescripts').panels.WidgetKnob({})".format(widget))

        self.addKnob(self.customKnob)


def init(widget_name, label):
    name = label.lower().replace(' ', '_')

    panel = Panel(label, name, widget_name)

    def add_panel():
        return panel.addToPane()

    menu = nuke.menu('Pane')
    menu.addCommand(label, add_panel)
    registerPanel(name, add_panel)


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
