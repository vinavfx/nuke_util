# -----------------------------------------------------------
# Qt Compatibility Layer - PySide2/PySide6
# -----------------------------------------------------------

import re as _re

try:
    from PySide6 import QtCore, QtGui, QtWidgets

    QtVersion = 6
except ImportError:
    from PySide2 import QtCore, QtGui, QtWidgets

    QtVersion = 2


class QRegExp:
    def __init__(self, pattern):
        self._pattern = pattern
        self._regex = _re.compile(pattern)
        self._last_match = None
        self._last_offset = 0

    def indexIn(self, text, offset=0):
        self._last_offset = offset
        self._last_match = self._regex.search(text, offset)
        if self._last_match:
            return self._last_match.start()
        return -1

    def pos(self, nth=0):
        if self._last_match:
            return self._last_match.start(nth)
        return -1

    def cap(self, nth=0):
        if self._last_match:
            return self._last_match.group(nth) or ""
        return ""

    def matchedLength(self):
        if self._last_match:
            return self._last_match.end() - self._last_match.start()
        return -1


if QtVersion == 6:
    from PySide6.QtCore import (
        Qt,
        QEvent,
        QSize,
        QTimer,
        QRect,
        QRectF,
        QPoint,
        QRegularExpression,
        QSortFilterProxyModel,
        QTimeLine,
    )

    from PySide6.QtWidgets import (
        QWidget,
        QStackedWidget,
        QApplication,
        QDialog,
        QHBoxLayout,
        QVBoxLayout,
        QComboBox,
        QLineEdit,
        QLabel,
        QPushButton,
        QListWidget,
        QMenu,
        QListWidgetItem,
        QSplitter,
        QTextEdit,
        QPlainTextEdit,
        QWidgetAction,
        QSizePolicy,
        QTreeWidget,
        QTreeWidgetItem,
        QListView,
        QAbstractItemView,
        QCheckBox,
        QSpinBox,
        QSlider,
    )

    from PySide6.QtGui import (
        QAction,
        QScreen,
        QIcon,
        QColor,
        QTextCursor,
        QFont,
        QTextOption,
        QPainter,
        QTextFormat,
        QPalette,
        QKeySequence,
        QCursor,
        QPixmap,
        QIntValidator,
        QTransform,
        QStandardItemModel,
        QSyntaxHighlighter,
        QShortcut,
    )
else:
    from PySide2.QtCore import (
        Qt,
        QEvent,
        QSize,
        QTimer,
        QRect,
        QRectF,
        QPoint,
        QRegExp,
        QSortFilterProxyModel,
        QTimeLine,
    )

    from PySide2.QtWidgets import (
        QWidget,
        QStackedWidget,
        QApplication,
        QDialog,
        QHBoxLayout,
        QVBoxLayout,
        QComboBox,
        QLineEdit,
        QLabel,
        QPushButton,
        QListWidget,
        QMenu,
        QListWidgetItem,
        QSplitter,
        QTextEdit,
        QPlainTextEdit,
        QWidgetAction,
        QSizePolicy,
        QTreeWidget,
        QTreeWidgetItem,
        QListView,
        QAbstractItemView,
        QCheckBox,
        QSpinBox,
        QSlider,
        QAction,
    )

    from PySide2.QtGui import (
        QIcon,
        QColor,
        QTextCursor,
        QFont,
        QTextOption,
        QPainter,
        QTextFormat,
        QPalette,
        QKeySequence,
        QCursor,
        QPixmap,
        QIntValidator,
        QTransform,
        QStandardItemModel,
        QSyntaxHighlighter,
        QShortcut,
    )

    QScreen = None
