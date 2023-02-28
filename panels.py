# Author: Francisco Jose Contreras Cuevas
# Office: VFX Artist - Senior Compositor
# Website: vinavfx.com
import os
import inspect
import nuke
from nukescripts import panels

from PySide2.QtWidgets import QWidget
from PySide2.QtCore import QEvent


def init(panel_widget, label, reload=False):
    module = inspect.getmodule(panel_widget)
    if not module:
        return

    def get_main_widget():

        if not hasattr(module, 'main_widget'):
            module.main_widget = None

        if reload:
            del module.main_widget
            module.main_widget = None

        if not module.main_widget:
            module.main_widget = panel_widget()

        return module.main_widget

    module.get_panel_widget = get_main_widget

    get_panel_widget = '{}.get_panel_widget'.format(
        module.__name__.replace('vina_pipeline.source', 'vina'))

    name = label.lower().replace(' ', '_')

    registered = panels.registerWidgetAsPanel(
        get_panel_widget, label, name, reload)

    if reload:
        panel = nuke.getPaneFor(name)
        registered.addToPane(panel)


class panel_widget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.border = True

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
        self.remove_parents_margin()

        return QWidget.showEvent(self, event)
