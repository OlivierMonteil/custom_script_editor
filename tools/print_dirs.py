
#------------------------------------------------------------------------------
#   A simple tool made for navigating through dir(module)
#------------------------------------------------------------------------------
import re
import inspect

try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide import QtGui, QtCore
    from PySide import QtGui as QtWidgets

try:
    import maya.cmds as MC
    import maya.mel as mel
    import maya.OpenMayaUI as OMUI
except ImportError:
    pass

try:
    import shiboken2 as shiboken
except ImportError:
    import shiboken

bgRgb = {'success': (89.25, 165.75, 61.2),
         'error' : (216.75, 81.6, 81.6),
         'warning': (204.0, 191.25, 127.5),
         'info': (61.2, 61.2, 61.2)}

textRgb = {'success': (0, 0, 0),
           'error' : (0, 0, 0),
           'warning': (0, 0, 0),
           'info': (175, 175, 175)}

windowName = 'Python dir() Navigator'

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class DirNavigator(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(DirNavigator, self).__init__(parent)

        self.setWindowTitle(windowName)

        centralWidget = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout()

        self.setCentralWidget(centralWidget)
        centralWidget.setLayout(lay)

        self.modField = QtWidgets.QLineEdit(placeholderText='Enter module/function path...',
                                            toolTip='(imports will be done if necessary)')
        self.kwField = QtWidgets.QLineEdit(placeholderText='Enter keyword...',
                                            toolTip='Seperate keywords with ",". No case match.')
        self.table = ResultTable()

        lay.addWidget(self.modField)
        lay.addWidget(self.kwField)
        lay.addWidget(QtWidgets.QLabel('Results :'))
        lay.addWidget(self.table)

        self.messageBar = StatusBar(parent=self)
        self.setStatusBar(self.messageBar)

        for obj in [centralWidget, lay]:
            self.setContentsMargins(0, 0, 0, 0)

        self.modField.returnPressed.connect(self.moduleEnter)
        self.kwField.returnPressed.connect(self.keywordEnter)
        self.kwField.textChanged.connect(self.keywordEnter)

        self.table.cellDoubleClicked.connect(self.appendToResearch)

        self.resize(450, 350)

    #--------------------------------------------------------------------------
    def moduleEnter(self):
        module = self.modField.text()
        keywords = self.kwField.text()

        self.kwField.setFocus(QtCore.Qt.MouseFocusReason)
    #--------------------------------------------------------------------------
    def keywordEnter(self, *args):
        module = self.modField.text()
        if module:
            self.getMatchingDir()
        else:
            self.error('Must enter valid object.')
    #--------------------------------------------------------------------------
    def appendToResearch(self, row, col):
        label = self.table.cellWidget(row, col).text()
        currentModule = self.modField.text()

        if not currentModule.split('.')[-1] == label:
            self.modField.setText(currentModule +'.' +label)
            self.clearView()
            self.kwField.setText('')
            self.kwField.setFocus(QtCore.Qt.MouseFocusReason)
    #--------------------------------------------------------------------------
    def getExecValue(self, toExecute):
        exec(toExecute)
        return value
    #--------------------------------------------------------------------------
    def getObject(self, module):
        content = 'import ' +module.split('.')[0] +'\nvalue = ' +module
        return self.getExecValue(content)
    #--------------------------------------------------------------------------
    def getMatchingDir(self):
        self.info('')

        foundStrings = []

        moduleStr = self.modField.text()
        keywords = self.kwField.text()

        try:
            module = self.getObject(moduleStr)
            foundDirs = dir(module)

            if not keywords:
                foundStrings = foundDirs

            else:
                allkewords = [x.lower().strip() for x in keywords.split(',')]
                for attr in foundDirs:
                    if any(kw in attr.lower() for kw in allkewords):
                        foundStrings.append(attr)

            self.clearView()

            if not foundStrings:
                self.warning('No match found.')
                return

            for i, attr in enumerate(foundStrings) or ():
                self.table.insertRow(i)
                label = QtWidgets.QLabel(attr)
                label.setStyleSheet('padding-left : 10px;')
                self.table.setCellWidget(i, 0, label)

            self.info('{} match'.format(len(foundStrings)))

        except Exception as e:
            self.clearView()
            self.error(str(e))
    #--------------------------------------------------------------------------
    def clearView(self):
        while self.table.rowCount():
            self.table.removeRow(0)
    #--------------------------------------------------------------------------
    def success(self, message, timeout=3000):
        self.showMessage(message, 'success', timeout=timeout)
    #--------------------------------------------------------------------------
    def error(self, message, timeout=3000):
        self.showMessage(message, 'error', timeout=timeout)
    #--------------------------------------------------------------------------
    def warning(self, message, timeout=3000):
        self.showMessage(message, 'warning', timeout=timeout)
    #--------------------------------------------------------------------------
    def info(self, message, timeout=3000):
        self.showMessage(message, 'info', timeout=timeout)
    #--------------------------------------------------------------------------
    def showMessage(self, message, levelType, timeout=3000):
        self.messageBar.setColor(levelType)
        self.messageBar.showMessage(message, timeout=timeout)

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class ResultTable(QtWidgets.QTableWidget):

    def __init__(self):
        super(ResultTable, self).__init__()

        self.setAcceptDrops(True)

        # set a few flags
        self.setColumnCount(1)
        self.setColumnWidth(0, 20)
        self.setSortingEnabled(False)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        #self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        # edit headers
        self.horizontalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setDefaultSectionSize(20)
        self.verticalHeader().hide()

        self.setVerticalScrollMode(self.ScrollPerItem)

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class StatusBar(QtWidgets.QStatusBar):

    def __init__(self, parent=None):
        super(StatusBar, self).__init__(parent)

        self.setColor('info')

        self.messageChanged.connect(self.onMessageChange)

    #--------------------------------------------------------------------------
    def setColor(self, levelType):
        barRgb = str(bgRgb[levelType])
        barTextRgb = str(textRgb[levelType])

        self.setStyleSheet('background-color: rgb{}; color: rgb{};'.format(barRgb, barTextRgb))
    #--------------------------------------------------------------------------
    def onMessageChange(self, message):
        if not message:
            self.setColor('info')

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
def killExisting(windowName=None, parent=None):
    # kill existing instance of MainWindow if exist

    if not windowName or not parent:
        return

    for widget in parent.children():
        try:
            if widget.windowTitle() == windowName:
                widget.close()
        except:
            pass
#------------------------------------------------------------------------------
def run():
    # show MainWindow with maya window as parent

    mayaUI = OMUI.MQtUtil.mainWindow()
    mayaUIqt = shiboken.wrapInstance(long(mayaUI), QtWidgets.QWidget)

    killExisting(windowName=windowName, parent=mayaUIqt)
    newWin = DirNavigator(parent=mayaUIqt)
    newWin.show()

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    newWin = MainWindow()
    newWin.show()
    sys.exit(app.exec_())
