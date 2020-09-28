"""
Test Window with a single QTextEdit for quick tests out of Maya.
"""

import os
import sys

from PySide2 import QtWidgets, QtGui

ROOT = os.path.dirname(os.path.dirname(__file__))
if not ROOT in sys.path:
    sys.path.append(ROOT)

from custom_script_editor.multi_cursors import MultiCursorManager
from custom_script_editor import syntax_highlight
from custom_script_editor import keys


SAMPLE_TEXT = """word = self.lineEdit.text()

        extraSelections = []

        self.plainTextEdit.moveCursor(QtGui.QTextCursor.Start)
        while(self.plainTextEdit.find(word,QtGui.QTextDocument.FindWholeWords)):
            '''
            selection = QtWidgets.QTextEdit.ExtraSelection()
            selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.plainTextEdit.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
            '''
            cursor = self.plainTextEdit.textCursor()
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
            currentWord = QtWidgets.QTextEdit.ExtraSelection()
            Color = QtGui.QColor(191, 191, 191, 189)
            currentWord.format.setBackground(Color)
            currentWord.cursor = cursor
            extraSelections.append(currentWord)

        self.plainTextEdit.setExtraSelections(extraSelections)
        self.plainTextEdit.setFocus()
"""


class MultiEditText(QtWidgets.QWidget):

    def __init__(self, parent=None):

        super(MultiEditText, self).__init__(parent)
        lay = QtWidgets.QHBoxLayout(self)
        self.txt_edit = QtWidgets.QTextEdit(self)
        self.txt_edit.setObjectName('TestQTextEdit')
        lay.addWidget(self.txt_edit)
        self.txt_edit.setText(SAMPLE_TEXT)

        # add PythonHighlighter on QTextEdit if not already added
        if child_class_needed(self.txt_edit, syntax_highlight.PythonHighlighter):

            highlight = syntax_highlight.PythonHighlighter(self.txt_edit)

        # install KeysHandler filterEvent on QTextEdit if not already installed
        if child_class_needed(self.txt_edit, keys.KeysHandler):
            key_handle = keys.KeysHandler('Python', parent=self.txt_edit)
            self.txt_edit.installEventFilter(key_handle)

        if child_class_needed(self.txt_edit, MultiCursorManager):
            mcursors_handle = MultiCursorManager(self.txt_edit)
            mcursors_handle.install(self.txt_edit)

        self.resize(500, 300)


def child_class_needed(widget, target_class):
    """
    Args:
        widget (QWidget)
        target_class (class)

    Returns:
        (bool)

    Check whether <target_class> is found in <widget>'s children or not.
    (used to detect if eventFilters or SynthaxHighlighters are installed on widget)
    """

    for child in widget.children():
        if isinstance(child, target_class):
            return False
    return True


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    text = MultiEditText()
    text.show()

    sys.exit(app.exec_())
