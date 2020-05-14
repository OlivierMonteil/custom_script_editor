###############################################################################
#       Script for customizing Maya's script editor hightlights and hotkeys.
###############################################################################

__author__ = 'Olivier Monteil'
__version__ = 1.1
__ide_version__ = 'Atom'

import sys
import re

try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide import QtGui, QtCore
    from PySide import QtGui as QtWidgets

try:
    import maya.cmds as mc
    import maya.mel as mel
    import maya.OpenMayaUI as OMUI
except:
    pass

try:
    import shiboken2 as shiboken
except ImportError:
    import shiboken

from tools import menu as tools_menu
import syntax_highlight
import keys
import snippets

reload(tools_menu)
reload(syntax_highlight)
reload(keys)
reload(snippets)

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class ScriptEditorDetector(QtCore.QObject):

    """
    Custom eventFilter installed on Maya's main window that will re-set highlight
    and connections on Script Editor (with evalDeferred).
    """

    def __init__(self, parent=None):
        super(ScriptEditorDetector, self).__init__(parent)

    #--------------------------------------------------------------------------
    def eventFilter(self, obj, event):
        # (no need to run set_customize_on_tab_change and customize_script_editor
        # if the Script Editor is already opened)
        if not script_editor_opened():
            if event.type() == QtCore.QEvent.ChildAdded:
                if event.child().isWidgetType():
                    # defer set_customize_on_tab_change and customize_script_editor to make sure
                    # Script Editor's window is fully created first
                    mc.evalDeferred(set_customize_on_tab_change, lowestPriority=True)
                    mc.evalDeferred(customize_script_editor, lowestPriority=True)

        return False

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def script_editor_opened():
    return True if get_script_editor() else False
#------------------------------------------------------------------------------
def get_script_editor():
    app = QtWidgets.QApplication.instance()
    for widget in app.topLevelWidgets():
        if widget.windowTitle() == 'Script Editor':
            return widget
#------------------------------------------------------------------------------
def set_customize_on_tab_change():
    # connect ScriptEditor > QTabWidget.currentChanged signal to customize_script_editor
    #  --> used to customize all new created tabs, because this signal is
    #      called after each tab creation when the Script Editor automatically
    #      focuses on the new tab

    tabsLay = get_scripts_tab_lay()
    if not tabsLay:
        return

    ptr = OMUI.MQtUtil.findControl(tabsLay)
    qtLay = shiboken.wrapInstance(long(ptr), QtWidgets.QWidget)

    for child in qtLay.children():
        if child.__class__.__name__ == 'QTabWidget':
            child.currentChanged.connect(customize_script_editor)
            break
#------------------------------------------------------------------------------
def get_text_edits(widget):
    # get all QTextEdit found into widget's children

    found = []
    for child in widget.children() or ():
        if isinstance(child, QtGui.QTextDocument):
            found.append(widget.parent())

        found.extend(get_text_edits(child))

    return found
#------------------------------------------------------------------------------
def get_scripts_tab_lay():
    # get Script Editor's tabLayout (detected by the presence of "MEL" and "Python" tabs)

    # get scriptEditor panel if exists
    try:
        panels = mc.lsUI(panels=True)
    except:
        return

    script_editor = [p for p in panels if 'scriptEditor' in p]
    if not script_editor:
        return

    # get all tablayouts that have scriptEditor as parent
    se_tabs = [lay for lay in mc.lsUI(type='tabLayout') \
               if script_editor[0] in mc.layout(lay, q=True, p=True)]

    # get the tablayout that have only MEL and /or Python tabs
    # (there may be also the 'Quick Help' tablayout)
    for lay in se_tabs or ():
        tabs = mc.tabLayout(lay, q=True, tabLabel=True)
        if all(x in ['MEL', 'Python'] for x in tabs):
            return lay
#------------------------------------------------------------------------------
def child_class_needed(widget, className):
    # detect whether <className> exists in widget's children or not
    # (used to detect if eventFilters or SynthaxHighlighters or installed on widget)

    for w in widget.children():
        if w.__class__.__name__ == className:
            return False
    return True
#------------------------------------------------------------------------------
def script_tools_menu(menu):
    # (called on Custom Menu > Script Tools menu added into add_custom_menus func)

    try:
        pos = QtGui.QCursor().pos()
        tools_menu.run(pos)
    except:
        mc.warning('Could not import tools/menu.py')
#------------------------------------------------------------------------------
def palette_editor_menu(menu):
    # (called on Custom Menu > Script Tools menu added into add_custom_menus func)

    try:
        pos = QtGui.QCursor().pos()
        tools_menu.run(pos)
    except:
        mc.warning('Could not import tools/menu.py')
#------------------------------------------------------------------------------
def remove_maya_highlight(widget):
    for syntax_hl in widget.findChildren(QtGui.QSyntaxHighlighter):
        syntax_hl.setDocument(None)
        # child.deleteLater()
        # del syntax_hl
#-----------------------------------------------------------------------------
def add_custom_menus():
    se_popup_menus = mel.eval("$toto = $gCommandPopupMenus;")

    for menu in se_popup_menus:
        if not mc.menu(menu, q=True, exists=True):
            continue

        main_menu = mc.menuItem('CustomMenu', p=menu, subMenu=True,
                                radialPosition="S", label='Custom Menu')

        mc.menuItem('SnippetBox', p=main_menu, radialPosition="S",
                                 label='Snippets', checkBox=True)
        mc.menuItem('ScriptTools', p=main_menu, radialPosition="W",
                                 label='Script Tools', command=lambda *args: script_tools_menu(menu))
        mc.menuItem('PaletteSetter', p=main_menu, radialPosition="E",
                                 label='set palette...', command=lambda *args: palette_editor_menu(menu))
#------------------------------------------------------------------------------
def customize_script_editor(*args):
    # iterate every tab from ScriptEditor's TabWidget to check if the PythonHighlighter,
    # KeysHandler and SnippetsHandler are to be installed on it

    se_tab_lay = get_scripts_tab_lay()
    if not se_tab_lay:
        return

    # get all ScriptEditor tabs and tab-labels
    labels = mc.tabLayout(se_tab_lay, q=True, tabLabel=True)
    tabs = mc.tabLayout(se_tab_lay, q=True, childArray=True)

    for i, form_lay in enumerate(tabs) or ():
        # do not apply PythonHighlighter on MEL tabs
        apply_highlight = True if labels[i] == 'Python' else False

        ptr = OMUI.MQtUtil.findControl(form_lay)
        widget = shiboken.wrapInstance(long(ptr), QtWidgets.QWidget)
        text_edits = get_text_edits(widget)

        # do not edit "MEL" tabs for now
        if not apply_highlight:
            continue

        for t in text_edits or ():
            try:
                # add PythonHighlighter on QTextEdit if not already added
                if child_class_needed(t, 'PythonHighlighter') and apply_highlight:
                    remove_maya_highlight(t)      # remove maya's default QSyntaxHighlighter
                    # set stylesheet with object name (will not be applied on children)
                    style_body  = 'QTextEdit#' +t.objectName() +'{\n'
                    style_body += '    color: rgb(170, 176, 190);\n'
                    style_body += '    background : rgb(29, 34, 46);\n}'
                    style_body += '    background : rgb(29, 34, 46);\n}'
                    t.setStyleSheet(style_body)
                    highlight = syntax_highlight.PythonHighlighter(t)

                # install KeysHandler filterEvent on QTextEdit if not already installed
                if child_class_needed(t, 'KeysHandler'):
                    key_handle = keys.KeysHandler(parent=t)
                    t.installEventFilter(key_handle)

                # install KeysHandler filterEvent on QTextEdit if not already installed
                if child_class_needed(t, 'SnippetsHandler'):
                    snippets_handle = snippets.SnippetsHandler(t, form_lay)
                    t.installEventFilter(snippets_handle)

            except Exception as e:
                print ('in customize_script_editor', e)

    add_custom_menus()

#------------------------------------------------------------------------------

def run():
    """
    (called by maya's userSetup.mel/py)

    Install event filter on Maya's main window to automate Script Editor
    customization.
    """

    maya_ui = OMUI.MQtUtil.mainWindow()
    maya_ui_qt = shiboken.wrapInstance(long(maya_ui), QtWidgets.QWidget)

    # install ScriptEditorDetector event filter on Maya window if not already
    if child_class_needed(maya_ui_qt, 'ScriptEditorDetector'):
        ui_filter = ScriptEditorDetector(parent=maya_ui_qt)
        maya_ui_qt.installEventFilter(ui_filter)

    # customize Script Editor if already opened and connect ScriptEditor > QTabWidget.currentChanged
    # signal to customize_script_editor. This will allow to customize all new created tabs,
    # because this signal is called after each tab creation when the Script Editor
    # automatically focuses on the new tab
    if script_editor_opened():
        customize_script_editor()
        set_customize_on_tab_change()

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class TestWindow(QtWidgets.QMainWindow):
    def __init__(self, parent):
        super(TestWindow, self).__init__()

        self.setCentralWidget(QtWidgets.QWidget())
        lay = QtWidgets.QVBoxLayout(self.centralWidget())

        self.field = QtWidgets.QTextEdit()
        self.field.setObjectName('TESTFIELD')

        lay.addWidget(self.field)

        self.set_highlight()

        self.resize(500, 600)

    def set_highlight(self):
        import custom_script_editor
        import importlib

        importlib.reload(custom_script_editor)
        custom_script_editor.remove_maya_highlight(self.field)

        style_body  = 'QTextEdit#' +self.field.objectName() +'{\n'
        style_body += '    color: rgb(170, 176, 190);\n'
        style_body += '    background : rgb(29, 34, 46);\n}'
        self.field.setStyleSheet(style_body)
        highlight = custom_script_editor.PythonHighlighter(self.field)

        keyHandle = KeysHandler(parent=self.field)
        self.field.installEventFilter(keyHandle)

#------------------------------------------------------------------------------

def test(parent=None):
    import sys

    try:
        app = QtWidgets.QApplication(sys.argv)

        window = TestWindow(parent)
        window.show()

        sys.exit(app.exec_())
    except:
        window = TestWindow(parent)
        window.show()

    return window

#------------------------------------------------------------------------------

if __name__ == '__main__':
    test()
