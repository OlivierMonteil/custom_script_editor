"""
Color management for Synthax highglighters. These are no QtGui.QPalette objects.
"""

import os
import json

try:
    from PySide2 import QtWidgets, QtGui, QtCore
except ImportError:
    from PySide import QtGui
    from PySide import QtGui as QtWidgets

from custom_script_editor import constants as kk


STYLE_PATTERN = """
QTextEdit#%(object_name)s {
    color: rgb%(color)s;
    background : rgb%(background)s;
    %(paddingLine)s
}
"""

PALETTES_ROOT = os.path.join(os.path.dirname(__file__), 'palettes')


class Palette(object):
    """
    Base class for LogPalette, PythonPalette and MelPalette.
    """

    specific_formats = {}

    def __init__(self, widget, padding=True):

        self.root_type = None
        self.widget = widget
        self.palette = {}
        self.padding = padding

    def apply_theme(self, widget, theme):
        """
        Args:
            widget (QTextEdit)
            theme (str)

        Apply <theme>.json palette on <widget>.
        """

        theme = self.root_type +'/' +theme if self.root_type else theme
        self.palette = get_palette(theme)
        self.set_stylesheet()

    def set_stylesheet(self):
        """
        Set self.widget's style, based on theme's colors.
        """
        if self.padding:
            paddingLine = 'padding-left : {}px;'.format(kk.LEFT_PADDING)
        else:
            paddingLine = ''

        style_body = STYLE_PATTERN % {
            'object_name': self.widget.objectName(),
            'color': self.get_color('normal'),
            'background': self.get_color('background'),
            'paddingLine': paddingLine
        }

        self.widget.setStyleSheet(style_body)

        # get QtGui.QPalette from self.widget (QTextEdit)
        qpalette = self.widget.palette()
        # set no brush on highlighted text (will keep sinthax highlight)
        qpalette.setBrush(
            QtGui.QPalette.HighlightedText,
            QtGui.QBrush(QtCore.Qt.NoBrush)
        )
        qpalette.setBrush(
            QtGui.QPalette.Highlight,
            QtGui.QColor(201, 214, 255, 50)
        )
        # apply new palette on the QTextEdit
        self.widget.setPalette(qpalette)

    def char_formatted(self):
        """
        Get Palette as {'pattern_name': QtGui.QTextCharFormat} dict.
        """

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

    def get_color(self, attr):
        """
        Args:
            attr (str)

        Get dict's color at <attr> key.
        """

        return tuple(self.palette[attr])

    def set_color(self, attr, rgb):
        """
        Args:
            attr (str)
            rgb (tuple or list)

        Get dict's color at <attr> key.
        """

        self.palette[attr] = tuple(rgb)

        # update stylesheet for attributes that are in use in it
        if attr in ('normal', 'background', 'highlight', 'highlight_text'):
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
