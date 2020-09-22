"""
A simple tool made for navigating through modules using dir() method.
"""

import sys
import re
import traceback

from PySide2 import QtWidgets, QtCore

try:
    import maya.OpenMayaUI as OMUI
except:
    pass

import shiboken2 as shiboken

BG_RGB = {
    'success': (89, 166, 61),
    'error' : (217, 82, 82),
    'warning': (204, 191, 128),
    'info': (61, 61, 61)
}

TEXT_RGB = {
    'success': (0, 0, 0),
    'error' : (0, 0, 0),
    'warning': (0, 0, 0),
    'info': (175, 175, 175)
}

WINDOW_NAME = 'Python dir() Navigator'


class DirNavigator(QtWidgets.QMainWindow):
    """
    Main dir() navigation window.
    """

    def __init__(self, parent=None):
        super(DirNavigator, self).__init__(parent)

        self.setWindowTitle(WINDOW_NAME)

        central_widget = QtWidgets.QWidget(self)
        lay = QtWidgets.QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        self.modules_field = QtWidgets.QLineEdit(
            self,
            placeholderText='Enter module/function path...',
            toolTip='(imports will be done if necessary)'
        )

        self.keywords_field = QtWidgets.QLineEdit(
            self,
            placeholderText='Enter keyword...',
            toolTip='Seperate keywords with coma. No case match.'
        )

        self.result_table = ResultTable()

        lay.addWidget(self.modules_field)
        lay.addWidget(self.keywords_field)
        lay.addWidget(QtWidgets.QLabel('Results :', self))
        lay.addWidget(self.result_table)

        self.messageBar = StatusBar(parent=self)
        self.setStatusBar(self.messageBar)

        for obj in [central_widget, self]:
            obj.setContentsMargins(2, 2, 2, 2)
        lay.setContentsMargins(4, 4, 4, 4)

        self.resize(450, 350)

        self.connect_signals()

    def connect_signals(self):
        self.modules_field.returnPressed.connect(self.on_module_entered)
        self.keywords_field.returnPressed.connect(self.on_keyword_entered)
        self.keywords_field.textChanged.connect(self.on_keyword_entered)

        self.result_table.cellDoubleClicked.connect(self.append_to_module)

    def on_module_entered(self):
        """
        (called on module's field.returnPressed signal)
        Set focus on keywords field.
        """

        self.keywords_field.setFocus(QtCore.Qt.MouseFocusReason)

    def on_keyword_entered(self, *args):
        """
        Search for matching items in dir(module) and display result into the ResultTable.
        """

        mod = self.modules_field.text()
        if mod:
            self.get_matching_dirs()
        else:
            self.error('Must enter valid object.')

    def append_to_module(self, row, col):
        """
        Args:
            row (int)
            col (int)

        (called on ResultTable.cellDoubleClicked signal).

        Add double-clicked item to module field, separated with a dot.
        """

        label = self.result_table.cellWidget(row, col).text()
        current_module = self.modules_field.text()

        if not current_module.split('.')[-1] == label:
            # append to modules field
            self.modules_field.setText('{}.{}'.format(current_module, label))
            # clear ResultTable
            self.clear_view()
            # clear keywords field
            self.keywords_field.setText('')
            self.keywords_field.setFocus(QtCore.Qt.MouseFocusReason)

    def get_module(self, mod):
        """
        Args:
            mod (str) : module, method or any object absolute name

        Returns:
            (object, or None)
            (bool) : whether object exists or not.

        Get <mod> object if exists (import its root module if necessary).
        """

        if mod not in sys.modules:
            tokens = mod.split('.')
            root_mod_str = tokens[0]

            if root_mod_str not in sys.modules:
                try:
                    eval('import ' +root_mod_str)
                except:
                    pass

            if root_mod_str not in sys.modules:
                self.error("No module named '{}'.".format(root_mod_str))
                return None, False

            # iterate trhough module levels and check if next level exists
            if len(tokens) > 1:
                for i, _ in enumerate(tokens):
                    if i == len(tokens)-1:
                        break

                    mod_str = '.'.join(tokens[:i+1])

                    if mod_str in sys.modules:
                        mod_object = sys.modules[mod_str]
                    else:
                        mod_object = eval(mod_str)

                    if not hasattr(mod_object, tokens[i+1]):
                        self.error("'{}' has no attribute named '{}'.".format(
                                mod_str, tokens[i+1]
                            )
                        )
                        return mod_str, False

        if mod in sys.modules:
            return sys.modules[mod], True

        return eval(mod), True

    def get_matching_dirs(self):
        """
        Get dir() items from modules field object that match with keywords field
        keyword(s). If no keyword was set, display all results.
        """

        self.info('')

        found_strings = []

        mod_str = self.modules_field.text()
        keywords = self.keywords_field.text()

        try:
            # some easy cases
            if mod_str == 'None':
                found_dirs = dir(None)
            elif mod_str == 'True':
                found_dirs = dir(True)
            elif mod_str == 'False':
                found_dirs = dir(False)
            elif re.match('\d+', mod_str):
                found_dirs = dir(int)
            elif re.match('\d+\.\d*', mod_str):
                found_dirs = dir(float)
            elif mod_str == 'list':
                found_dirs = dir(list)
            elif mod_str == 'tuple':
                found_dirs = dir(tuple)
            elif mod_str == 'set':
                found_dirs = dir(set)
            elif mod_str == 'int':
                found_dirs = dir(int)
            elif mod_str == 'float':
                found_dirs = dir(float)
            elif mod_str == 'str':
                found_dirs = dir(str)
            elif mod_str == 'bool':
                found_dirs = dir(bool)

            else:
                module, valid = self.get_module(mod_str)
                if not valid:  # error has already been displayed
                    # set modules field text with last valid module string
                    if module:
                        self.modules_field.setText(module)
                    self.clear_view()
                    return

                found_dirs = dir(module)

            if not keywords:
                found_strings = found_dirs

            else:
                all_kewords = [x.lower().strip() for x in keywords.split(',')]
                for attr in found_dirs:
                    if any(kw in attr.lower() for kw in all_kewords):
                        found_strings.append(attr)

            self.clear_view()

            if not found_strings:
                self.warning('No match found.')
                return

            for i, attr in enumerate(found_strings) or ():
                self.result_table.insertRow(i)
                label = QtWidgets.QLabel(attr)
                label.setStyleSheet('padding-left : 10px;')
                self.result_table.setCellWidget(i, 0, label)

            self.success('{} match.'.format(len(found_strings)))

        except:
            self.clear_view()
            traceback.print_exc()

    def clear_view(self):
        while self.result_table.rowCount():
            self.result_table.removeRow(0)

    def success(self, message, timeout=5000):
        self.showMessage(message, 'success', timeout=timeout)

    def error(self, message, timeout=5000):
        self.showMessage(message, 'error', timeout=timeout)

    def warning(self, message, timeout=5000):
        self.showMessage(message, 'warning', timeout=timeout)

    def info(self, message, timeout=5000):
        self.showMessage(message, 'info', timeout=timeout)

    def showMessage(self, message, lvl_type, timeout=5000):
        # format message
        line_char = '#' if lvl_type == 'error' else '//'
        message = '{} [Print dirs] {} : {}'.format(
            line_char, lvl_type.capitalize(), message
        )

        # display message
        self.messageBar.set_color(lvl_type)
        self.messageBar.showMessage(message, timeout=timeout)


class ResultTable(QtWidgets.QTableWidget):

    def __init__(self):
        super(ResultTable, self).__init__()

        self.setAcceptDrops(True)

        # set a few flags
        self.setColumnCount(1)
        self.setColumnWidth(0, 20)
        self.setSortingEnabled(False)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        # edit headers
        self.horizontalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setDefaultSectionSize(20)
        self.verticalHeader().hide()

        self.setVerticalScrollMode(self.ScrollPerItem)


class StatusBar(QtWidgets.QStatusBar):

    def __init__(self, parent=None):
        super(StatusBar, self).__init__(parent)

        self.set_color('info')

        self.messageChanged.connect(self.on_message_change)

    def set_color(self, lvl_type):
        """
        Args:
            lvl_type (str) : 'info', 'warning', 'error' or 'success'

        Set QStatusBar background and text colors from <lvl_type>.
        """

        bg_rgb = str(BG_RGB[lvl_type])
        text_rgb = str(TEXT_RGB[lvl_type])

        self.setStyleSheet('background-color: rgb{}; color: rgb{};'.format(
                bg_rgb, text_rgb
            )
        )

    def on_message_change(self, message):
        if not message:
            self.set_color('info')


def killExisting(window_name=None, parent=None):
    # kill existing instance of MainWindow if exist

    if not window_name or not parent:
        return

    for widget in parent.children():
        try:
            if widget.windowTitle() == window_name:
                widget.close()
        except:
            pass

def run():
    # show MainWindow with maya window as parent

    maya_ui = OMUI.MQtUtil.mainWindow()
    maya_ui_qt = shiboken.wrapInstance(long(maya_ui), QtWidgets.QWidget)

    killExisting(window_name=WINDOW_NAME, parent=maya_ui_qt)

    new_window = DirNavigator(parent=maya_ui_qt)
    new_window.show()

def run_standalone():
    app = QtWidgets.QApplication(sys.argv)
    new_window = DirNavigator()
    new_window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    run_standalone()
