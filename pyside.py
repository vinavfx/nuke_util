# -----------------------------------------------------------
# Qt Compatibility Layer - PySide2/PySide6
# -----------------------------------------------------------

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QWidget, QStackedWidget, QApplication, QDialog
    from PySide2.QtGui import QScreen
except ImportError:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QWidget, QStackedWidget, QApplication, QDialog
    from PySide6.QtGui import QScreen
