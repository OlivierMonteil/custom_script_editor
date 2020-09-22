"""
Custom menu (run from the Script Editor hotbox menu).
"""

import maya.cmds as mc
from PySide2 import QtWidgets


class ToolsMenu(QtWidgets.QMenu):

    def __init__(self, parent=None):
        super(ToolsMenu, self).__init__(parent)

        self.addAction('Python dir() Navigator', self.open_dir_navigator)
        self.addAction('QRegex simulator', self.open_regex_simulator)


    def open_dir_navigator(self):
        try:
            import print_dirs
            reload(print_dirs)
            print_dirs.run()
        except Exception as e:
            print e
            mc.warning('Could not open "Python dir() Navigator".')

    def open_regex_simulator(self):
        try:
            import regex_simulator
            reload(regex_simulator)
            regex_simulator.run()
        except Exception as e:
            print e
            mc.warning('Could not open "QRegex Simulator".')


def run(pos, parent=None):
    menu = ToolsMenu(parent)
    menu.exec_(pos)
