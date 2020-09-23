"""
Custom menu (run from the Script Editor hotbox menu).
"""

import maya.cmds as mc
from PySide2 import QtWidgets

from custom_script_editor.tools import regex_simulator
from custom_script_editor.tools import print_dirs


class ToolsMenu(QtWidgets.QMenu):

    def __init__(self, parent=None):
        super(ToolsMenu, self).__init__(parent)

        self.addAction('Python dir() Navigator', self.open_dir_navigator)
        self.addAction('QRegex simulator', self.open_regex_simulator)


    def open_dir_navigator(self):
        try:
            print_dirs.run()
        except Exception as e:
            print e
            mc.warning('Could not run "Python dir() Navigator".')

    def open_regex_simulator(self):
        try:
            regex_simulator.run()
        except Exception as e:
            print e
            mc.warning('Could not run "QRegex Simulator".')


def run(pos, parent=None):
    menu = ToolsMenu(parent)
    menu.exec_(pos)
