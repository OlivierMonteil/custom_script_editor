"""
Test Window with a single QTextEdit for quick tests out of Maya.
"""

import os
import sys

from PySide2 import QtWidgets, QtGui, QtCore

ROOT = os.path.dirname(os.path.dirname(__file__))
if not ROOT in sys.path:
    sys.path.append(ROOT)

from custom_script_editor.multi_cursors import MultiCursorManager
from custom_script_editor.syntax_highlight import PythonHighlighter
from custom_script_editor.keys import KeysHandler
from blocks_collapse import set_collapse_widget

SAMPLE_FILE = os.path.join(os.path.dirname(__file__), 'blocks_collapse.py')


class MultiEditWindow(QtWidgets.QWidget):
    """
    Simple test window with single QTextEdit. May be run with Python3.
    """

    def __init__(self, parent=None):
        super(MultiEditWindow, self).__init__(parent)

        lay = QtWidgets.QHBoxLayout(self)
        self.txt_edit = MultiEditText(self)
        self.txt_edit.setObjectName('TestQTextEdit')
        lay.addWidget(self.txt_edit)
        self.txt_edit.setText(sample_text())
        self.txt_edit.setWordWrapMode(QtGui.QTextOption.NoWrap)

        self.resize(500, 300)

        # add PythonHighlighter
        PythonHighlighter(self.txt_edit)

        # install KeysHandler filterEvent on QTextEdit
        key_handle = KeysHandler('Python', parent=self.txt_edit)
        self.txt_edit.installEventFilter(key_handle)

        # install MultiCursorManager filterEvent on QTextEdit
        mcursors_handle = MultiCursorManager(self.txt_edit)
        mcursors_handle.install(self.txt_edit)

        # install MultiCursorManager filterEvent on QTextEdit
        set_collapse_widget(self.txt_edit)


class MultiEditText(QtWidgets.QTextEdit):
    """
    Custom QTextEdit with zooming feature on wheelEvent.
    """

    def wheelEvent(self, event):
        if event.modifiers() & QtCore.Qt.ControlModifier:
            self.zoom(event.delta())
        else:
            QtWidgets.QTextEdit.wheelEvent(self, event)

    def zoom(self, delta):
        if delta < 0:
            self.zoomOut(1)
        elif delta > 0:
            self.zoomIn(1)


def sample_text():
    with open(SAMPLE_FILE, 'r') as opened_file:
        return opened_file.read()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    text = MultiEditWindow()
    text.show()

    sys.exit(app.exec_())
