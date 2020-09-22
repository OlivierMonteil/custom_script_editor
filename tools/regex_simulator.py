"""
Script for QRegex testing.
"""

from PySide2 import QtCore, QtWidgets
import shiboken2 as shiboken

from maya.OpenMayaUI import MQtUtil

from custom_script_editor import syntax_highlight
from custom_script_editor import keys

WINDOW_OBJECT_NAME = 'QRegexSimulatorWindow'


class QRegexSimulator(QtWidgets.QMainWindow):

    def __init__(self, parent=None):

        super(QRegexSimulator, self).__init__(parent)

        self.syntax = QtCore.QRegExp.RegExp

        self.setWindowTitle('QRegex Simulator')
        self.setObjectName(WINDOW_OBJECT_NAME)

        # create main "Regular expression" QDockWidget
        main_dock = QtWidgets.QDockWidget(self)
        main_dock.setWindowTitle('Regular expression')
        main_dock.setFeatures(main_dock.NoDockWidgetFeatures)
        self.setCentralWidget(main_dock)

        # add regex field to main QDockWidget
        main_widget = QtWidgets.QWidget(self)
        main_dock.setWidget(main_widget)
        lay = QtWidgets.QGridLayout(main_widget)

        self.regex_field = QtWidgets.QLineEdit(self)
        self.formatted_field = QtWidgets.QLineEdit(self, readOnly=True)

        lay.addWidget(QtWidgets.QLabel('Input regex :', self), 0, 0)
        lay.addWidget(self.regex_field, 0, 1)
        lay.addWidget(QtWidgets.QLabel('Formatted regex :', self), 1, 0)
        lay.addWidget(self.formatted_field, 1, 1)

        # create "Test string" QDockWidget
        script_dock = QtWidgets.QDockWidget(self)
        script_dock.setWindowTitle('Test string')
        script_dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)
        script_dock.setFeatures(script_dock.NoDockWidgetFeatures)

        # add test string field to main QDockWidget
        self.script_field = QtWidgets.QTextEdit(self)
        self.script_field.setObjectName('{}_scriptField'.format(WINDOW_OBJECT_NAME))
        # add keys handler
        keys_handler = keys.KeysHandler('Python', self.script_field)
        self.script_field.installEventFilter(keys_handler)
        highlight = syntax_highlight.PythonHighlighter(self.script_field)

        script_dock.setWidget(self.script_field)

        # create "Match Informations" QDockWidget
        result_dock = QtWidgets.QDockWidget(self)
        result_dock.setWindowTitle('Match Informations')
        result_dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)
        result_dock.setFeatures(result_dock.NoDockWidgetFeatures)

        # add test string field to main QDockWidget
        self.result_field = QtWidgets.QPlainTextEdit()
        result_dock.setWidget(self.result_field)

        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, script_dock)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, result_dock)

        self.regex_field.textChanged.connect(self.update_results)
        self.script_field.textChanged.connect(self.update_results)

        main_widget.setFixedHeight(52)
        main_widget.setContentsMargins(0, 0, 0, 0)
        lay.setContentsMargins(4, 4, 4, 4)

        self.resize(1000, 750)

    def update_results(self):
        """
        Log regex matches.
        """

        content = ''

        try:
            regex_txt = self.regex_field.text()
            if not regex_txt:
                content = ''
                return

            if self.is_critical(regex_txt):
                content = 'Invalid regex.'
                return

            regex = QtCore.QRegExp(regex_txt)

            if not regex.isValid():
                content = 'Invalid regex.'
                return

            regex = QtCore.QRegExp(regex_txt)
            test = self.script_field.toPlainText()
            test_cuts = test.split('\n')

            for i in range(len(test_cuts)) or ():
                line = test_cuts[i]
                index = regex.indexIn(line, 0)

                while index >= 0:
                    content += 'Line ' +str(i) +' at ' +str(index) +' :\n'

                    for nth in range(regex.captureCount() +1):
                        pos = regex.pos(nth)
                        length = len(regex.cap(nth))

                        content += '    group ' +str(nth) +' : ' +line[pos: pos +length] +'\n'

                    index = regex.indexIn(line, pos + length)

                    content += '\n'

            self.formatted_field.setText(regex_txt.replace('b', '\\b'))

        except:
            content = 'An error occured.'

        finally:
            self.result_field.setPlainText(content)

    def is_critical(self, text):
        """
        Args:
            text (str) : regex string

        Returns:
            (bool)

        Check whether regex string is critical.
        """

        if text[-1] == '\\':
            return True

        if text == '\\b':
            return True

        if text == '^':
            return True

        if text[-2:] == '^|':
            return True

        return False

def closeExisting(maya_ui_qt):
    """
    Args:
        maya_ui_qt (QtWidgets.QMainWindow) : wrapped instance of Maya's main window

    Close existing MainWindow instance in Maya.
    """

    for widget in maya_ui_qt.children():
        if widget.objectName() == WINDOW_OBJECT_NAME:
            widget.setParent(None)
            widget.close()
            widget.deleteLater()    # avoids QMenu memory leak
            del widget
            break


def run():
    maya_ui = MQtUtil.mainWindow()
    maya_ui_qt = shiboken.wrapInstance(long(maya_ui), QtWidgets.QMainWindow)

    closeExisting(maya_ui_qt)

    window = QRegexSimulator(maya_ui_qt)

    window.show()
