# -----------------------------------------------------------
# Qt Compatibility Layer - PySide2/PySide6
# -----------------------------------------------------------
import re

try:
    from PySide6 import QtCore, QtGui, QtWidgets

    QtVersion = 6
except ImportError:
    from PySide2 import QtCore, QtGui, QtWidgets  # type: ignore

    QtVersion = 2


class RegexCompatibility:
    def __init__(self, pattern):
        self.pattern = pattern
        self.regex = re.compile(pattern)
        self.last_match = None
        self.last_offset = 0

    def indexIn(self, text, offset=0):
        self.last_offset = offset
        self.last_match = self.regex.search(text, offset)
        if self.last_match:
            return self.last_match.start()
        return -1

    def pos(self, nth=0):
        if self.last_match:
            return self.last_match.start(nth)
        return -1

    def cap(self, nth=0):
        if self.last_match:
            return self.last_match.group(nth) or ""
        return ""

    def matchedLength(self):
        if self.last_match:
            return self.last_match.end() - self.last_match.start()
        return -1


Qt = QtCore.Qt
QEvent = QtCore.QEvent
QSize = QtCore.QSize
QTimer = QtCore.QTimer
QRect = QtCore.QRect
QRectF = QtCore.QRectF
QPoint = QtCore.QPoint
QSortFilterProxyModel = QtCore.QSortFilterProxyModel
QTimeLine = QtCore.QTimeLine

QWidget = QtWidgets.QWidget
QStackedWidget = QtWidgets.QStackedWidget
QApplication = QtWidgets.QApplication
QDialog = QtWidgets.QDialog
QHBoxLayout = QtWidgets.QHBoxLayout
QVBoxLayout = QtWidgets.QVBoxLayout
QComboBox = QtWidgets.QComboBox
QLineEdit = QtWidgets.QLineEdit
QLabel = QtWidgets.QLabel
QPushButton = QtWidgets.QPushButton
QListWidget = QtWidgets.QListWidget
QMenu = QtWidgets.QMenu
QListWidgetItem = QtWidgets.QListWidgetItem
QSplitter = QtWidgets.QSplitter
QTextEdit = QtWidgets.QTextEdit
QPlainTextEdit = QtWidgets.QPlainTextEdit
QWidgetAction = QtWidgets.QWidgetAction
QSizePolicy = QtWidgets.QSizePolicy
QTreeWidget = QtWidgets.QTreeWidget
QTreeWidgetItem = QtWidgets.QTreeWidgetItem
QListView = QtWidgets.QListView
QAbstractItemView = QtWidgets.QAbstractItemView
QCheckBox = QtWidgets.QCheckBox
QSpinBox = QtWidgets.QSpinBox
QSlider = QtWidgets.QSlider

QScreen = QtGui.QScreen
QIcon = QtGui.QIcon
QColor = QtGui.QColor
QTextCursor = QtGui.QTextCursor
QTextCharFormat = QtGui.QTextCharFormat
QFont = QtGui.QFont
QTextOption = QtGui.QTextOption
QPainter = QtGui.QPainter
QTextFormat = QtGui.QTextFormat
QPalette = QtGui.QPalette
QKeySequence = QtGui.QKeySequence
QCursor = QtGui.QCursor
QPixmap = QtGui.QPixmap
QIntValidator = QtGui.QIntValidator
QTransform = QtGui.QTransform
QStandardItemModel = QtGui.QStandardItemModel
QSyntaxHighlighter = QtGui.QSyntaxHighlighter

if QtVersion == 6:
    QRegExp = RegexCompatibility
    QRegularExpression = QtCore.QRegularExpression
    QAction = QtGui.QAction
    QShortcut = QtGui.QShortcut
else:
    from PySide2.QtCore import QRegExp as NativeRegExp  # type: ignore
    from PySide2.QtWidgets import QAction as NativeAction  # type: ignore
    from PySide2.QtWidgets import QShortcut as NativeShortcut  # type: ignore

    QRegExp = NativeRegExp
    QAction = NativeAction
    QShortcut = NativeShortcut
