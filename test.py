import sys

ROOT = r'C:\Users\Olivier\Documents\maya\scripts\custom_script_editor'
if not ROOT in sys.path:
    sys.path.append(ROOT)

from multi_cursors import MultiCursor
import keys

from PySide2 import QtWidgets

TEXT = """word = self.lineEdit.text()

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
        txt_edit = QtWidgets.QTextEdit(self)
        txt_edit.setObjectName('TestQTextEdit')
        lay.addWidget(txt_edit)
        txt_edit.setText(TEXT)

        mcursors_handle = get_multi_cursors_handle(self)
        if not mcursors_handle:
            mcursors_handle = MultiCursor(self)

        mcursors_handle.install_if_not_already(txt_edit)


def get_multi_cursors_handle(widget):
    for child in widget.children() or ():
        if isinstance(child, MultiCursor):
            return child


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    text = MultiEditText()
    text.show()

    sys.exit(app.exec_())
