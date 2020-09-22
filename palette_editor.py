import os

from PySide2 import QtWidgets, QtCore, QtGui
import shiboken2 as shiboken


from custom_script_editor import syntax_highlight as sh
from custom_script_editor import palette

from maya.OpenMayaUI import MQtUtil

STYLE_PATTERN = """
QTextEdit#%(object_name)s {
    color: rgb%(color)s;
    background : rgb%(background)s;
}
"""

PALETTES_ROOT = os.path.join(os.path.dirname(__file__), 'palettes')
WINDOW_OBJECT_NAME = 'CSE_paletteEditor'



class PaletteEditor(QtWidgets.QMainWindow):

    def __init__(self, txt_type, theme, parent=None):
        super(PaletteEditor, self).__init__(parent=parent)

        self.highlighter = None

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setWindowTitle('Edit current palette')
        self.setObjectName(WINDOW_OBJECT_NAME)

        central_widget = QtWidgets.QWidget(self)
        self.lay = QtWidgets.QGridLayout(central_widget)
        self.setCentralWidget(central_widget)

        # prevent keys propagation to Maya Window
        self.keyPressEvent = lambda *args: None
        self.keyReleaseEvent = lambda *args: None

        central_widget.setContentsMargins(0, 0, 0, 0)
        self.lay.setContentsMargins(4, 4, 4, 4)

        self.display_palette(txt_type, theme)

    def clear_layout(self):
        pass

    def display_palette(self, txt_type, theme):
        self.clear_layout()

        theme_palette = palette.get_palette('{}/{}'.format(txt_type, theme))
        template_palette = palette.get_palette('{}/template'.format(txt_type))
        attr_dict = template_palette['attributes']
        font_specs = template_palette['font_specs']
        attributes = sorted(attr_dict.keys(), key=lambda x: attr_dict[x][0])

        self.buttons = {}
        i = 0

        for attr in attributes or ():
            label, tooltip = attr_dict[attr]

            label_widget = QtWidgets.QLabel(label, self, toolTip=tooltip)
            color_button = ColorButton(
                tuple(theme_palette[attr]),
                attr,
                label,
                self
            )

            label_widget.setStyleSheet(
            """
            QLabel {
                padding-left: 3px;
            }
            """
            )

            self.lay.addWidget(label_widget, i, 0)
            self.lay.addWidget(color_button, i, 1)

            self.buttons[attr] = color_button
            self.lay.setRowStretch(i, 0)

            color_button.color_changed.connect(self.on_color_changed)

            i += 1

        self.setStyleSheet(
        """
        QMainWindow {
            background : rgb(43, 43, 43);
            color: rgb(180, 180, 190);
        }""")

        self.lay.setRowStretch(i, 10)

        self.add_text_sample(i, txt_type, theme)

    def add_text_sample(self, i, txt_type, theme):
        self.sample_text = QtWidgets.QTextEdit(self, readOnly=True)
        self.sample_text.setObjectName(WINDOW_OBJECT_NAME +'_sampleTextEdit')

        self.sample_text.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.sample_text.viewport().setCursor(QtCore.Qt.ArrowCursor)

        if txt_type == 'mel':
            self.highlighter = sh.MelHighlighter(self.sample_text)
        elif txt_type == 'python':
            self.highlighter = sh.PythonHighlighter(self.sample_text)
        elif txt_type == 'log':
            self.highlighter = sh.LogHighlighter(self.sample_text)

        self.highlighter.set_theme(theme)

        font = QtGui.QFont("DejaVu Sans Mono", 8)
        self.sample_text.setFont(font)

        self.lay.addWidget(self.sample_text, 0, 2, i+1, 1)

        sample_file = os.path.join(PALETTES_ROOT, '{}/sample.txt'.format(txt_type))
        text = ''

        with open(sample_file, 'r') as opened_file:
            try:
                text = opened_file.read()
            except:
                pass

        self.sample_text.setText(text)

    def on_color_changed(self, rgb):
        sender = self.sender()
        attr = self.sender().attr

        self.highlighter.palette.set_color(attr, rgb)
        self.highlighter.update()



class ColorButton(QtWidgets.QPushButton):
    """
    Custom QPushButton for color picking.
    """

    counter = 0
    color_changed = QtCore.Signal(list)

    def __init__(self, rgb, attr, label, *args, **kwargs):
        super(ColorButton, self).__init__(*args, **kwargs)

        self._rgb = None
        self.attr = attr
        self.label = label
        self.setMaximumSize(16, 16)
        self.setObjectName('ColorButton' +str(self.counter))

        self.clicked.connect(self.open_color_picker)

        ColorButton.counter += 1
        if rgb:
            self.set_rgb(rgb)

    def open_color_picker(self):
        dialog = QtWidgets.QColorDialog(self)
        dialog.setOption(dialog.DontUseNativeDialog)
        dialog.setWindowTitle('Select {} color'.format(self.label))

        if self._rgb:
            qcolor = QtGui.QColor(*self._rgb)
            dialog.setCurrentColor(qcolor)

            if not any(dialog.customColor(i) == qcolor for i in range(dialog.customCount())):
                for i in reversed(range(dialog.customCount())):
                    dialog.setCustomColor(i+1, dialog.customColor(i))

                dialog.setCustomColor(0, qcolor)

        if dialog.exec_():
            new_rgb = dialog.currentColor()
            new_rgb = [new_rgb.red(), new_rgb.green(), new_rgb.blue()]
            self.set_rgb(new_rgb)

    def set_rgb(self, rgb):
        if rgb != self._rgb:
            self._rgb = rgb
            self.color_changed.emit(rgb)

        if self._rgb:
            self.setStyleSheet(
                'QPushButton#%s {background-color: rgb(%s, %s, %s)}' % (
                    self.objectName(), rgb[0], rgb[1], rgb[2]
                )
            )
        else:
            self.setStyleSheet('')



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

    window = PaletteEditor('python', 'atom-OneDark', maya_ui_qt)

    window.show()
