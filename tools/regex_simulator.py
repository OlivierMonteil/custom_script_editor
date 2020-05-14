import sys
import re

import subprocess

from os.path import expanduser, join, isdir

try:
    from pyside import QtCore, QtGui
    from pyside import QtGui as QtWidgets

except ImportError:
    from PySide2 import QtCore, QtGui, QtWidgets

try: import maya.OpenMayaUI as OMUI
except: pass

try: import shiboken2
except: pass

try:
    import maya.cmds as MC
    import maya.mel as mel
    sys.path.append(mel.eval('getenv OM_STEERISCRIPTS_ROOT').split(';')[0])
except:
    root = __file__.replace('\\', '/').split('/steeriScripts/')[0] +'/steeriScripts/'
    sys.path.append(root)


try:
    from importlib import reload
except:
    pass

from common import textEdit as textEdit
from .. import syntax_highlight
reload(textEdit)
reload(syntax_highlight)

#------------------------------------------------------------------------------

class QRegexSimulator(QtWidgets.QMainWindow):

    def __init__(self):

        super(QRegexSimulator, self).__init__()

        self.syntax = QtCore.QRegExp.RegExp

        self.setWindowTitle('QRegex Simulator')

        # create main "Regular expression" QDockWidget
        mainDock = QtWidgets.QDockWidget(self)
        mainDock.setWindowTitle('Regular expression')
        mainDock.setFeatures(mainDock.NoDockWidgetFeatures)
        self.setCentralWidget(mainDock)

        # add regex field to main QDockWidget
        mainWidget = QtWidgets.QWidget()
        mainWidget.setContentsMargins(0, 0, 0, 0)
        lay = QtWidgets.QVBoxLayout()
        lay.setContentsMargins(0, 0, 0, 0)
        mainWidget.setLayout(lay)
        self.regexField = QtWidgets.QLineEdit()
        self.formattedField = QtWidgets.QLineEdit()
        mainWidget.setFixedHeight(75)
        mainDock.setWidget(mainWidget)
        lay.addWidget(self.regexField)
        lay.addWidget(self.formattedField)

        # create "Test string" QDockWidget
        scriptDock = QtWidgets.QDockWidget(self)
        scriptDock.setWindowTitle('Test string')
        scriptDock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)
        scriptDock.setFeatures(scriptDock.NoDockWidgetFeatures)

        # add test string field to main QDockWidget
        self.testField = textEdit.Custom_QPlainTextEdit()
        scriptDock.setWidget(self.testField)

        # create "Match Informations" QDockWidget
        resultDock = QtWidgets.QDockWidget(self)
        resultDock.setWindowTitle('Match Informations')
        resultDock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)
        resultDock.setFeatures(resultDock.NoDockWidgetFeatures)

        # add test string field to main QDockWidget
        self.resultField = QtWidgets.QPlainTextEdit()
        resultDock.setWidget(self.resultField)

        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, scriptDock)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, resultDock)

        self.regexField.textChanged.connect(self.updateResults)
        self.testField.textChanged.connect(self.updateResults)

        self.resize(1000, 750)

    #--------------------------------------------------------------------------
    def keyBoardEvent(self, event):
        syntaxHLight.keyBoardEvent(self.testField, event)
    #--------------------------------------------------------------------------
    def updateResults(self):
        content = 'No match.'

        try:
            regexText = self.regexField.text()
            if not regexText:
                content = ''
                return

            if self.isCritical(regexText):
                content = 'Invalid regex.'
                return

            regex = QtCore.QRegExp(regexText)

            if not regex.isValid():
                content = 'Invalid regex.'
                return

            regex = QtCore.QRegExp(regexText)
            test = self.testField.toPlainText()
            testCuts = test.split('\n')

            for i in range(len(testCuts)) or ():
                line = testCuts[i]
                index = regex.indexIn(line, 0)

                while index >= 0:
                    content += 'Line ' +str(i) +' at ' +str(index) +' :\n'

                    for nth in range(regex.captureCount() +1):
                        pos = regex.pos(nth)
                        length = len(regex.cap(nth))

                        content += '    group ' +str(nth) +' : ' +line[pos: pos +length] +'\n'

                    index = regex.indexIn(line, pos + length)

                    content += '\n'

            self.formattedField.setText(regexText.replace('b', '\\b'))

        except:
            content = 'An error occured.'
        finally:
            self.resultField.setPlainText(content)
    #--------------------------------------------------------------------------
    def isCritical(self, text):
        if text[-1] == '\\':
            return True

        if text == '\\b':
            return True

        if text == '^':
            return True

        if text[-2:] == '^|':
            return True

        return False

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class NodeInfos(QtWidgets.QWidget):

    processPath = join(expanduser('~AppData'), 'Local/atom/atom.exe')
    resultFile = join(expanduser('~AppData'), 'Local/Temp/connectScript.py')

    def __init__(self):

        super(NodeInfos, self).__init__()

        self.width = 600

        self.clipBoard = QtGui.QClipboard()
        self.connections = ConnectionScript()
        self.nonDefault = NonDefaultScript()

        self.setWindowTitle('Node Infos')
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        lay = QtWidgets.QVBoxLayout()
        self.setLayout(lay)

        self.setContentsMargins(2, 2, 2, 2)
        lay.setContentsMargins(0, 0, 0, 0)

        connButt = QtWidgets.QPushButton('Get connections script')
        valuButt = QtWidgets.QPushButton('Get non-default values script')
        self.scriptView = QtWidgets.QPlainTextEdit()
        self.scriptView.setStyleSheet('color: rgb(170, 176, 190); \
                                      background : rgb(45, 48, 55);')
        highlight = syntax_highlight.PythonHighlighter(self.scriptView.document())
        copyButt = QtWidgets.QPushButton('Copy to clipboard')
        openButt = QtWidgets.QPushButton('Open in file')

        lay.addWidget(connButt)
        lay.addWidget(valuButt)
        lay.addWidget(self.scriptView)
        lay.addWidget(copyButt)
        lay.addWidget(openButt)

        connButt.clicked.connect(lambda : self.getScript(self.connections))
        valuButt.clicked.connect(lambda : self.getScript(self.nonDefault))
        copyButt.clicked.connect(self.copy)
        openButt.clicked.connect(self.openInFile)

        self.resize(1000, 750)
    #--------------------------------------------------------------------------
    def openInFile(self, *args):
        try:
            subprocess.Popen("%s %s" % (self.processPath,
                                        self.resultFile))
        except:
            subprocess.Popen("%s %s" % ('notepad.exe', self.resultFile))
    #--------------------------------------------------------------------------
    def copy(self):
        self.clipBoard.setText(self.scriptView.toPlainText())
    #--------------------------------------------------------------------------
    def getScript(self, scriptClass):
        sel = MC.ls(sl=True)

        if not sel:
            MC.error('No selected node.')
            return

        result = scriptClass.get(sel[0])

        with open(self.resultFile, 'w') as openedFile:
            openedFile.write(result)

        self.scriptView.setPlainText(result)

        MC.select(sel[0])

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class ConnectionScript(object):
    """
    Get connections script as string to re-create all existing connections
    from obj to connection-relatives :

    def setConnections(obj, relative1, relative2):
        MC.connectAttr(obj +'.output1', relative1 +'.input1')
        MC.connectAttr(obj +'.output1', relative2 +'.input1')
        ...

    """

    shortenRegex = re.compile('.+?(?:(?<=[a-z])(?=[A-Z])|(?=[0-9])|(?<=[A-Z])(?=[A-Z][a-z])|$)')

    #--------------------------------------------------------------------------
    def get(self, selObj, fromClass=False):
        # return setConnections function as string to be pasted into
        # another python script

        shortObj = self.incrementArg(self.shortenName(selObj), [])

        arguments = [selObj]
        shortArgs = [shortObj]
        commentLines = [self.objComment(shortObj, selObj)]
        scriptLines = []

        connects = MC.listConnections(selObj, c=True, p=True)
        if not connects:
            return

        for i in range(len(connects)/2):
            # get output and input
            output = connects[i]
            input = connects[i+1]
            # get output and input objects
            outputObj = output.split('.')[0]
            inputObj = input.split('.')[0]

            shortNames = []

            for obj in [outputObj, inputObj]:
                short = self.incrementArg(self.shortenName(obj), [])
                shortNames.append(short)

                if obj not in arguments:
                    arguments.append(obj)

                    short = self.incrementArg(self.shortenName(obj), shortArgs)
                    shortArgs.append(short)

                    commentLines.append(self.objComment(short, obj))

            output = output.replace(outputObj, shortNames[0] +' +\'')
            input = input.replace(inputObj, shortNames[1] +' +\'')

            scriptLines.append('    MC.connectAttr(' +output +'\', ' +input +'\')')

        # set function's declaration line
        declareLine = 'def setConnections(' +', '.join(shortArgs) +'):\n'

        if fromClass:
            declareLine = declareLine.replace('(', '(self, ')

        result = declareLine +'    \"\"\"\n' +'\n'.join(commentLines) +'\n    \"\"\"\n\n' +'\n'.join(scriptLines)

        return '# Connections script for ' +selObj +':\n\n' +result
    #--------------------------------------------------------------------------
    def incrementArg(self, newArg, shortArgs):
        newArg = self.endDigitsRemoved(newArg)
        similars = [arg for arg in shortArgs
                    if self.endDigitsRemoved(arg) == newArg]

        return newArg +str(len(similars)) if similars else newArg
    #--------------------------------------------------------------------------
    def endDigitsRemoved(self, obj):
        # remove end digits froms obj
        endDigits = self.getEndDigits(obj)
        return obj[:-len(endDigits)] if endDigits else obj
    #--------------------------------------------------------------------------
    def getEndDigits(self, obj):
        endDigits = re.search('\d+$', obj)
        return endDigits.group(0) if endDigits else ''
    #--------------------------------------------------------------------------
    def shortenName(self, obj):
        matches = re.finditer(self.shortenRegex, obj)
        matches = [m.group(0) for m in matches]

        result = ''

        if len(matches) > 1:
            for i in range(len(matches) -1):
                result += matches[i][0].lower()
            result += matches[-1]
        else:
            result = matches[0]

        return result
    #--------------------------------------------------------------------------
    def objComment(self, shortObj, obj):
        return '    ' +shortObj +' = \'' +obj +'\''

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class NonDefaultScript(object):
    def get(self, node):
        # return all modified values from node into dictionnary

        # create a node from same type (holds all default values)
        defaultNode = MC.createNode(MC.nodeType(node))

        modified = {}

        # compare all node attributes with defaultNode's,
        # add attributes and values in dict if not default
        for attr in MC.listAttr(node):
            try:
                value = MC.getAttr(node +'.' +attr)

                try:
                    if value != MC.getAttr(defaultNode +'.' +attr):
                        modified[attr] = value
                except:
                    modified[attr] = value
            except Exception as e:
                print e
                continue


        defaultParent = MC.listRelatives(defaultNode, p=True, f=True)

        # delete default node's parent if defaultNode has parent
        if defaultParent:
            MC.delete(defaultParent)
        # else delete default node
        else:
            MC.delete(defaultNode)

        result = 'No non-default value found on ' +node +'.'

        if modified:
            # set function's declaration line
            result = 'def setNodeValues(node):\n'

            for attr in modified:
                value = modified[attr]

                if isinstance(value, unicode):
                    result += '\n    MC.setAttr(node +\'.' +attr +'\', \"\"\"' +str(value) +'\"\"\", type=\'string\')'
                else:
                    result += '\n    MC.setAttr(node +\'.' +attr +'\', ' +str(value) +')'


        return '# Non-default values script for ' +node +':\n\n' +result

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class createLogFile(object):
    def __init__(self):

        self.filePath = expanduser('~/maya/scripts/Utility')
        self.file = join(self.filePath, 'toLogFile.py')
        self.tmpFile = join(self.filePath, 'tmpToLogFile.py')
        self.processPath = join(expanduser('~AppData'), 'Local/atom/atom.exe')

        self.window = 'toLogFile_Window'
        self.w, self.h = 260, 84

    #--------------------------------------------------------------------------
    def UI(self):
        if MC.window(self.window, query=True, exists=True):
            MC.deleteUI(self.window)
        if MC.windowPref(self.window, query=True, exists=True):
            MC.windowPref(self.window, rms=True)

        wh = (350, 200)

        MC.window(self.window, title='Log file Writing', widthHeight=(self.w, self.h), tlb=True, rtf=False, s=False)
        MC.window(self.window, edit=True, widthHeight=(self.w, self.h))

        MC.rowLayout('TLF_mainRowLay', p=self.window, numberOfColumns=3)
        MC.text(p='TLF_mainRowLay', w=2, label='')
        MC.columnLayout('TLF_mainLay', p='TLF_mainRowLay')
        MC.text(p='TLF_mainRowLay', w=2, label='')
        MC.text(p='TLF_mainLay', h=4, label='')

        MC.checkBox('TLF_checkBox', p='TLF_mainLay', label='To be written', annotation='If so, each line will be written as logfile.write(<line>).', value=0)

        MC.text(p='TLF_mainLay', h=4, label='')
        MC.button('TLF_openButt', p='TLF_mainLay', w=248, label='Open file', command=self.openFile)
        MC.text(p='TLF_mainLay', h=4, label='')
        MC.button('TLF_runButt', p='TLF_mainLay', w=248, label='RUN', command=self.run)
        MC.text(p='TLF_mainLay', h=2, label='')

        MC.setParent('..')
        MC.showWindow(self.window)

        print (self.window)
    #--------------------------------------------------------------------------
    def openFile(self, *args):
        try:
            import subprocess
            subprocess.Popen("%s %s" % (self.processPath, self.file))

        except:
            subprocess.Popen("%s %s" % ('notepad.exe', self.file))
    #--------------------------------------------------------------------------
    def run(self, *args):
        if not isdir(self.filePath):
            MC.sysFile(makeDir=self.filePath)

        MC.sysFile(self.file, copy=self.tmpFile)

        tmpLogfile = open(self.tmpFile, 'w')
        tmpLogfile.truncate()
        logfile = open(self.file, 'r')

        topMessage = 'Logfile result :'
        toWriteTop = '\n' +topMessage +'\n\n'

        for line in logfile:
            if not topMessage in line:
                tmpLogfile.write(line)
            else:
                toWriteTop = topMessage +'\n\n'
                break

        tmpLogfile.write(toWriteTop)

        tmpLogfile = open(self.tmpFile, 'a')
        logfile = open(self.file, 'r')

        logLines = logfile.readlines()
        lastLine = logLines[len(logLines)-1]

        lineBegin = 'logfile.write(' if MC.checkBox('TLF_checkBox', q=True, value=True) else ''
        lineEnd = ')' if MC.checkBox('TLF_checkBox', q=True, value=True) else ''

        for line in logLines:
            if topMessage in line:
                break

            elif line is lastLine:
                line = line[:-2]
                line = line.replace('\\', '\\\\')
                line = line.replace('"', '\\"')
                line = line.replace('\'', '\\\'')
                line = line.replace('\t', '\\t')
                tmpLogfile.write(lineBegin +'\'' +line +'\\n\'' +lineEnd)
            else:
                line = line[:-2]
                line = line.replace('\\', '\\\\')
                line = line.replace('"', '\\"')
                line = line.replace('\'', '\\\'')
                line = line.replace('\t', '\\t')
                tmpLogfile.write(lineBegin +'\'' +line +'\\n\'' +lineEnd +'\n')

        tmpLogfile.flush()
        tmpLogfile.close()
        logfile.flush()
        logfile.close()

        MC.sysFile(self.file, delete=True )
        MC.sysFile(self.tmpFile, rename=self.file)

        self.openFile()

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

if __name__ == '__main__':
    # create QApplication instance
    app = QtWidgets.QApplication.instance()

    niWin = NodeInfos()
    niWin.show()


    sys.exit(app.exec_())
