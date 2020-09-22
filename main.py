"""
Script for customizing Maya's script editor hightlights and hotkeys.
"""


import re

try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide import QtGui, QtCore
    from PySide import QtGui as QtWidgets

try:
    import maya.cmds as mc
    from maya import mel
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
import palette

VALID_TABS_REGEX = ['MEL', 'Python', '[\w\-_]+(.py)$']



class ScriptEditorDetector(QtCore.QObject):

    """
    Custom eventFilter installed on Maya's main window that will re-set highlight
    and connections on Script Editor (with evalDeferred).
    """

    def __init__(self, parent=None):
        super(ScriptEditorDetector, self).__init__(parent)

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


def script_editor_opened():
    return True if get_script_editor() else False

def get_script_editor():
    """
    Returns:
        (QtWidgets.QWidget)

    Gets the Script Editor window.
    """

    app = QtWidgets.QApplication.instance()
    for widget in app.topLevelWidgets():
        if widget.windowTitle() == 'Script Editor':
            return widget

def set_customize_on_tab_change():
    """
    Connect ScriptEditor > QTabWidget.currentChanged signal to customize_script_editor().
    Used to customize new created tabs, as this signal is called after each tab
    creation.
    """

    tabsLay = get_scripts_tab_lay()
    if not tabsLay:
        return

    ptr = OMUI.MQtUtil.findControl(tabsLay)
    qtLay = shiboken.wrapInstance(long(ptr), QtWidgets.QWidget)

    for child in qtLay.children():
        if isinstance(child, QtWidgets.QTabWidget):
            child.currentChanged.connect(customize_script_editor)
            break

def get_logs_text_edit():
    """
    Returns:
         (QTextEdit)

    Get logs QTextEdit from Script Editor panel.
    """

    script_editor = get_script_editor()
    text_edits = get_text_edits(script_editor)

    for te in text_edits:
        if 'cmdScrollFieldReporter1' in te.objectName():
            return te

def get_text_edits(widget):
    """
    Args:
        widget (QWidget)

    Get all QTextEdit found into widget's children.
    """

    found = []
    for child in widget.children() or ():
        if isinstance(child, QtGui.QTextDocument):
            found.append(widget.parent())

        found.extend(get_text_edits(child))

    return found

def get_scripts_tab_lay():
    """
    Returns:
        (str or None) : tabLayout

    Get Script Editor's tabLayout that is holding script tabs (not the "Quick Help" one).
    """

    # get scriptEditor panel if exists
    try:
        panels = mc.lsUI(panels=True)
    except:
        return None

    script_editor = [p for p in panels if 'scriptEditor' in p]
    if not script_editor:
        return None

    # get all tablayouts that have scriptEditor as parent
    se_tabs = [lay for lay in mc.lsUI(type='tabLayout') \
               if script_editor[0] in mc.layout(lay, q=True, p=True)]

    # get the tablayout that have only MEL and /or Python tabs
    # (there may be also the 'Quick Help' tablayout)
    for lay in se_tabs or ():
        tabs = mc.tabLayout(lay, q=True, tabLabel=True)
        if all(is_valid_tab_name(x) for x in tabs):
            return lay

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

def script_tools_menu(menu):
    """ Run "Script Tools" menu. """

    pos = QtGui.QCursor().pos()
    tools_menu.run(pos)

def palette_editor_menu(menu):
    """ Run "Edit palette..." menu. """

    print '// "Edit palette..." not Implemented yet.'

def remove_maya_highlight(widget):
    """
    Args:
        widget (QWidget)

    Remove QtGui.QSyntaxHighlighter from <widget>.
    """

    for syntax_hl in widget.findChildren(QtGui.QSyntaxHighlighter):
        syntax_hl.setDocument(None)

def add_custom_menus():
    """ Add custom menus to the Script Editor's tabs hotbox menu. """

    se_popup_menus = mel.eval("$toto = $gCommandPopupMenus;")

    for menu in se_popup_menus:
        if not mc.menu(menu, q=True, exists=True):
            continue

        main_menu = mc.menuItem('CustomMenu', p=menu, subMenu=True,
                                radialPosition="S", label='Custom Menu')

        mc.menuItem('SnippetBox', p=main_menu, radialPosition="S",
                                 label='Snippets', checkBox=True)
        mc.menuItem('ScriptTools', p=main_menu, radialPosition="W",
                                 label='Script Tools', command=script_tools_menu)
        mc.menuItem('PaletteSetter', p=main_menu, radialPosition="E",
                                 label='Edit palette...', command=palette_editor_menu)

def is_valid_tab_name(name, exlude_mel=False):
    """
    Args:
        name (str)
        exlude_mel (bool, optional)

    Returns:
        (bool)
    """

    tabs_regex = VALID_TABS_REGEX[1:] if exlude_mel else VALID_TABS_REGEX
    return True if any(re.match(regex, name) for regex in tabs_regex) else False

def customize_script_editor(*args):
    """
    Iterate every tab from Script Editor and apply PythonHighlighter,
    KeysHandler and SnippetsHandler if required.
    """

    # highlight the Script Editor logs panel
    log_field = get_logs_text_edit()
    if log_field and child_class_needed(log_field, syntax_highlight.LogHighlighter):
        remove_maya_highlight(log_field)      # remove maya's default QSyntaxHighlighter
        highlight = syntax_highlight.LogHighlighter(log_field)

        mc.evalDeferred(highlight.rehighlight, lp=True)

    se_tab_lay = get_scripts_tab_lay()
    if not se_tab_lay:
        return

    # get all ScriptEditor tabs and tab-labels
    labels = mc.tabLayout(se_tab_lay, q=True, tabLabel=True)
    tabs = mc.tabLayout(se_tab_lay, q=True, childArray=True)

    for i, form_lay in enumerate(tabs) or ():
        # do not apply PythonHighlighter on MEL tabs
        is_mel_tab = False if is_valid_tab_name(labels[i], exlude_mel=True) else True

        ptr = OMUI.MQtUtil.findControl(form_lay)
        widget = shiboken.wrapInstance(long(ptr), QtWidgets.QWidget)
        text_edits = get_text_edits(widget)

        for t in text_edits or ():
            try:

                if is_mel_tab:
                    # add PythonHighlighter on QTextEdit if not already added
                    if child_class_needed(t, syntax_highlight.MelHighlighter):
                        remove_maya_highlight(t)      # remove maya's default QSyntaxHighlighter
                        highlight = syntax_highlight.MelHighlighter(t)
                else:
                    # add PythonHighlighter on QTextEdit if not already added
                    if child_class_needed(t, syntax_highlight.PythonHighlighter):
                        remove_maya_highlight(t)      # remove maya's default QSyntaxHighlighter
                        highlight = syntax_highlight.PythonHighlighter(t)

                # install KeysHandler filterEvent on QTextEdit if not already installed
                if child_class_needed(t, keys.KeysHandler):
                    tab_type = 'MEL' if is_mel_tab else 'Python'
                    key_handle = keys.KeysHandler(tab_type, parent=t)
                    t.installEventFilter(key_handle)

                # install SnippetsHandler filterEvent on QTextEdit if not already installed
                if child_class_needed(t, snippets.SnippetsHandler):
                    snippets_handle = snippets.SnippetsHandler(t, form_lay)
                    t.installEventFilter(snippets_handle)

            except Exception as e:
                print 'in customize_script_editor', e

    add_custom_menus()


def run():
    """
    (called by maya's userSetup.mel/py)

    Install event filter on Maya's main window to automate Script Editor
    customization.
    """

    maya_ui = OMUI.MQtUtil.mainWindow()
    maya_ui_qt = shiboken.wrapInstance(long(maya_ui), QtWidgets.QWidget)

    # install ScriptEditorDetector event filter on Maya window if not already
    if child_class_needed(maya_ui_qt, ScriptEditorDetector):
        ui_filter = ScriptEditorDetector(parent=maya_ui_qt)
        maya_ui_qt.installEventFilter(ui_filter)

    # customize Script Editor if already opened and connect ScriptEditor > QTabWidget.currentChanged
    # signal to customize_script_editor. This will allow to customize all new created tabs,
    # because this signal is called after each tab creation when the Script Editor
    # automatically focuses on the new tab

    if script_editor_opened():
        mc.evalDeferred(customize_script_editor, lp=True)
        mc.evalDeferred(set_customize_on_tab_change, lp=True)