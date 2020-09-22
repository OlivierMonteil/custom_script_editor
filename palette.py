import os
import json

try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide import QtGui, QtCore
    from PySide import QtGui as QtWidgets


STYLE_PATTERN = """
QTextEdit#%(object_name)s {
    color: rgb%(color)s;
    background : rgb%(background)s;
}
"""

PALETTES_ROOT = os.path.join(os.path.dirname(__file__), 'palettes')



class PaletteEditor(QtWidgets.QMainWindow):
    attributes = {
        'Base color': ('normal', 'Non-highlighted text color.'),
        'Python keywords color': ('keyword', 'def, class, if, for, lambda, etc.'),
        'Python operators color': ('operator', None),
        'Called methods/classes': ('called', None),
        'Functions color': ('def_name', None),
        'Classes color': ('class_name', None),
        'Class inherited objects': ('class_arg', None),
        'Strings color': ('string', None),
        'Comments': ('comments', None),
        '"self" keyword': ('self', None),
        'Decorators': ('decorators', None),
        'Intermediate objects': ('interm', 'Intermediate levels like module.intermediate.method()'),
        'Python builtins': ('special', 'Python builtins and escaped characters.'),
        'Numbers': ('numbers', None)
    }

    font_specs = {
        'comments': 'italic',
        'def_name': 'bold',
        'class_name': 'bold'
    }

    def __init__(self, theme, parent=None):
        super(PaletteEditor, self).__init__(parent=parent)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setWindowTitle('Edit current palette')

        central_widget = QtWidgets.QWidget(self)
        lay = QtWidgets.QGridLayout(central_widget)
        self.setCentralWidget(central_widget)

        palette = get_palette(theme)
        self.buttons = {}
        i = 0

        for attr in self.attributes:
            label = QtWidgets.QLabel(attr, self)
            key, tooltip = self.attributes[attr]

            if not tooltip is None:
                label.setToolTip(tooltip)

            color = palette[key]
            color_button = ColorButton(tuple(color), label, self)

            lay.addWidget(label, i, 0)
            lay.addWidget(color_button, i, 1)

            font = QtGui.QFont("DejaVu Sans Mono", 8)
            if key in self.font_specs:
                if 'bold' in self.font_specs[key]:
                    font.setWeight(font.Bold)
                if 'italic' in self.font_specs[key]:
                    font.setItalic(True)
            label.setFont(font)

            self.buttons[key] = color_button
            i += 1

        self.setStyleSheet(
        """
        QMainWindow {
            background : rgb%s;
            color: rgb%s;
        }""" % \
            (str(tuple(palette['background'])),
            str(tuple(palette['normal'])))
        )

        lay.setRowStretch(i, 10)



        # # add Ok/Cancel buttons
        # button_box = QtWidgets.QDialogButtonBox(parent=self)
        # apply = button_box.addButton('Apply', button_box.ApplyRole)
        # save = button_box.addButton('Save', button_box.ApplyRole)
        # save_as_default = button_box.addButton('Save as default', button_box.ApplyRole)
        #
        # lay.addWidget(button_box)
        #
        #
        # # set buttons sizes
        # for butt in button_box.buttons():
        #     butt.setFixedWidth(40)

        # prevent keys propagation to Maya Window
        self.keyPressEvent = lambda *args: None
        self.keyReleaseEvent = lambda *args: None

        central_widget.setContentsMargins(0, 0, 0, 0)
        lay.setContentsMargins(2, 2, 2, 2)


class ColorButton(QtWidgets.QPushButton):
    """
    Custom QPushButton for color picking.
    """

    counter = 0
    color_changed = QtCore.Signal(list)

    def __init__(self, rgb, label, *args, **kwargs):
        super(ColorButton, self).__init__(*args, **kwargs)

        self._rgb = None
        self.label = label
        self.setMaximumSize(16, 16)
        self.setObjectName('ColorButton' +str(self.counter))

        self.clicked.connect(self.open_color_picker)

        ColorButton.counter += 1
        if rgb:
            self.set_rgb(rgb)

    def open_color_picker(self):
        dialog = QtWidgets.QColorDialog(self)
        if self._rgb:
            dialog.setCurrentColor(QtGui.QColor(*self._rgb))

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

            self.label.setStyleSheet(
                """
                QLabel {
                    background : transparent;
                    color: rgb(%s, %s, %s);
                    padding-left: 3px;
                }""" % ( rgb[0], rgb[1], rgb[2] )
            )
        else:
            self.setStyleSheet('')


class Palette(object):

    specific_formats = {}

    def __init__(self, widget):

        self.root_type = None
        self.widget = widget
        self.palette = {}

    def apply_theme(self, widget, theme):
        theme = self.root_type +'/' +theme if self.root_type else theme
        self.palette = get_palette(theme)
        self.set_stylesheet()

    def set_stylesheet(self):
        style_body = STYLE_PATTERN % {
            'object_name': self.widget.objectName(),
            'color': self.get_color('normal'),
            'background': self.get_color('background')
        }

        self.widget.setStyleSheet(style_body)

    def char_formatted(self):
        result_dict = {}

        for attr in self.palette or ():
            if attr in self.specific_formats:
                result_dict[attr] = char_format(
                    self.get_color(attr),
                    self.specific_formats[attr]
                )

            else:
                result_dict[attr] = char_format(self.get_color(attr))

        return result_dict

    def get_color(self, key):
        return tuple(self.palette[key])

    def set_color(self, key, rgb):
        self.palette[key] = tuple(rgb)


class PythonPalette(Palette):

    specific_formats = {
        'def_name' : 'bold',
        'class_name' : 'bold',
        'comments' : 'italic',
    }

    def __init__(self, widget):

        Palette.__init__(self, widget)
        self.root_type = 'python'
        self.apply_theme(widget, 'default')


class MelPalette(Palette):

    specific_formats = {
        'def_name' : 'bold',
        'class_name' : 'bold',
        'comments' : 'italic',
    }

    def __init__(self, widget):
        Palette.__init__(self, widget)
        self.root_type = 'mel'
        self.apply_theme(widget, 'default')


class LogPalette(Palette):

    specific_formats = {
        'warning' : 'italic',
        'error' : 'bold',
        'success' : 'bold',
    }

    def __init__(self, widget):
        Palette.__init__(self, widget)
        self.root_type = 'log'
        self.apply_theme(widget, 'default')



def char_format(rgb, style=''):
    """
    Args:
        rgb (tuple(int))
        style (str, optional)

    Returns:
        (QtGui.QTextCharFormat)

    Return a QtGui.QTextCharFormat with the given attributes (color, font
    weigth...etc).
    """

    if isinstance(rgb, tuple):
        color = QtGui.QColor(*rgb)
    else:
        color = QtGui.QColor()
        color.setNamedColor(rgb)

    c_format = QtGui.QTextCharFormat()
    c_format.setForeground(color)
    if 'bold' in style:
        c_format.setFontWeight(QtGui.QFont.Bold)
    if 'italic' in style:
        c_format.setFontItalic(True)

    return c_format

def get_palette(theme):
    """
    Args:
        theme (str) : "log/default" for instance

    Get the <theme> palette from the according json file.
    """

    palette_file = os.path.join(PALETTES_ROOT, '{}.json'.format(theme))

    with open(palette_file, 'r') as opened_file:
        return json.load(opened_file)



if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)

    dialog = PaletteEditor('default')
    dialog.show()

    sys.exit(app.exec_())
