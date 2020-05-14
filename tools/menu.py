import maya.cmds as mc
from PySide2 import QtWidgets

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class ToolsMenu(QtWidgets.QMenu):

    def __init__(self):
        super(ToolsMenu, self).__init__()

        self.addAction('Python dir() Navigator', self.open_dir_navigator)
        self.addAction('regex simulator', self.open_regex_simulator)

    #--------------------------------------------------------------------------
    def open_dir_navigator(self):
        try:
            import print_dirs
            reload(print_dirs)
            print_dirs.run()
        except:
            mc.warning('Could not open "Python dir() Navigator".')
    #--------------------------------------------------------------------------
    def open_regex_simulator(self):
        try:
            import regex_simulator
            reload(regex_simulator)
            regex_simulator.run()
        except:
            mc.warning('Could not open "Regex Simulator".')

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def run(pos):
    menu = ToolsMenu()
    menu.exec_(pos)
