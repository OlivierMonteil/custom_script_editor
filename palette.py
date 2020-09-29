import os
import json

try:
    from PySide2 import QtWidgets, QtGui
except ImportError:
    from PySide import QtGui
    from PySide import QtGui as QtWidgets

from custom_script_editor import constants as kk


STYLE_PATTERN = """
QTextEdit#%(object_name)s {
    color: rgb%(color)s;
    background : rgb%(background)s;
    selection-color: rgb%(highlight_text)s;
    selection-background-color : rgba%(highlight)s;
    %(paddingLine)s
}
"""

PALETTES_ROOT = os.path.join(os.path.dirname(__file__), 'palettes')


class Palette(object):

    specific_formats = {}

    def __init__(self, widget, padding=True):

        self.root_type = None
        self.widget = widget
        self.palette = {}
        self.padding = padding

    def apply_theme(self, widget, theme):
        theme = self.root_type +'/' +theme if self.root_type else theme
        self.palette = get_palette(theme)
        self.set_stylesheet()

    def set_stylesheet(self):
        if self.padding:
            paddingLine = 'padding-left : {}px;'.format(kk.LEFT_PADDING)
        else:
            paddingLine = ''

        style_body = STYLE_PATTERN % {
            'object_name': self.widget.objectName(),
            'color': self.get_color('normal'),
            'background': self.get_color('background'),
            'highlight': self.get_color('highlight'),
            'highlight_text': self.get_color('highlight_text'),
            'background': self.get_color('background'),
            'paddingLine': paddingLine
        }

        self.widget.setStyleSheet(style_body)

    def char_formatted(self):
        result_dict = {}

        for attr in self.palette or ():
            if self.specific_formats and attr in self.specific_formats:
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

        if key in ('normal', 'background', 'highlight', 'highlight_text'):
            self.set_stylesheet()


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
        Palette.__init__(self, widget, padding=False)
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

    dialog = PaletteEditor('mel', 'default')
    dialog.show()

    sys.exit(app.exec_())
