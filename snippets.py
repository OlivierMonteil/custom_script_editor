"""
Snippets management file.
"""

import sys
import json
import os
import re

from PySide2 import QtWidgets, QtCore, QtGui

import maya.cmds as mc
from maya import mel
import maya.OpenMayaUI as OMUI

import shiboken2 as shiboken

from custom_script_editor import constants as kk
from custom_script_editor import utils


CUSTOM_JSON = os.path.dirname(__file__).replace('\\', '/') +'/custom_snippets.json'


class SnippetsHandler(QtCore.QObject):

    """
    Custom eventFilter installed on Maya's Script Editor to handle snippets.
    """

    def __init__(self, text_edit, form_lay):
        super(SnippetsHandler, self).__init__(text_edit)

        self.text_edit = text_edit
        self.snippets_box = self.get_snippet_box(form_lay)
        self.trigger_on_cursor_change = True
        self.text_edit.cursorPositionChanged.connect(self.on_cursor_change)
        self.box = None

    def get_snippet_box(self, form_lay):
        """
        Returns:
            form_lay (str)

        Get 'Snippets' menu's chechbox
        """

        script_editor_popup_menus = mel.eval("$toto = $gCommandPopupMenus;")

        popup_menu = [menu for menu in script_editor_popup_menus if form_lay in menu][0]
        return '{}|{}|{}'.format(
            popup_menu, kk.CUSTOM_MENU_NAME, kk.SNIPPETS_BOX_NAME
        )

    def snippets_enabled(self):
        """
        Returns:
            (bool)

        Get Custom Menu > Snippets box checked state.

        (mc.menuItem(self.snippets_box, q=True, checkBox=True) seems to fail,
        so we have to get menuItem as QAction to get the right result)
        """

        ptr = OMUI.MQtUtil.findMenuItem(self.snippets_box)
        if not ptr:
            return False

        qt_box = shiboken.wrapInstance(long(ptr), QtWidgets.QAction)
        return qt_box.isChecked()

    def eventFilter(self, obj, event):
        # close snippet box on RMB and MMB
        # (LMB seems to be handled directly into QTextCursor class)
        try:
            if event.button() and self.box:
                self.kill_box()
        except:
            pass

        # handle snippet box on key press events
        if event.type() == event.KeyPress and self.snippets_enabled():
            self.trigger_on_cursor_change = False

            cursor = self.text_edit.textCursor()

            if self.box:
                if event.key() == QtCore.Qt.Key_Return:
                    self.validate_snippet(self.box.current_item().text())
                    return True

                if event.key() == QtCore.Qt.Key_Down:
                    self.box.go_down()
                    return True
                if event.key() == QtCore.Qt.Key_Up:
                    self.box.go_up()
                    return True

                # close snippet box (will be reconstructed later if necessary)
                self.kill_box()

            to_lower = True
            if event.modifiers():
                if event.modifiers() == QtCore.Qt.ShiftModifier:
                    to_lower = False
                else:
                    return False

            key_as_str = QtGui.QKeySequence(event.key()).toString()
            key_as_str = key_as_str.lower() if to_lower else key_as_str

            # skip if key as string is more than one character (ex: space)
            # except for Backspace, so the snippets would still be triggered
            if key_as_str.lower() != 'backspace' and len(key_as_str) > 1:
                return False

            cursor = self.text_edit.textCursor()
            line = cursor.block().text()

            try:
                 # on alphabetical characters
                if re.match('[a-zA-Z_]', key_as_str) or key_as_str.lower() in ['.', 'backspace']:
                    pos = cursor.positionInBlock()
                    if key_as_str.lower() == 'backspace':
                        pos = min(0, pos -1)
                        key_as_str = ''

                    found_snippets = self.get_snippets(line, pos, key_as_str)

                    # if snippets have been found, show SnippetBox under current word
                    if found_snippets:
                        rect = self.text_edit.cursorRect()
                        pos = QtCore.QPoint(rect.x() +35, rect.y() +15)

                        self.box = SnippetBox(self.text_edit, found_snippets, pos)
                        self.box.itemPressed.connect(lambda x: self.validate_snippet(x.text()))
                        self.box.show()

            except:
                pass

        return False

    def validate_snippet(self, text):
        """
        Args:
            text (str)

        Insert selected completion into QTextEdit and close the snippets box.
        """

        cursor = self.text_edit.textCursor()
        pos = cursor.position()
        cursor.movePosition(cursor.StartOfWord, cursor.MoveAnchor)

        if cursor.position() == pos:
            cursor.movePosition(cursor.PreviousWord, cursor.MoveAnchor)

        cursor.movePosition(cursor.EndOfWord, cursor.KeepAnchor)
        cursor.insertText(text)

        mc.evalDeferred(self.kill_box, lowestPriority=True)

    def kill_box(self):
        """
        Close the snippets box.
        """

        if self.box:
            self.box.close()
        self.box = None

    @utils.catch_error
    def get_custom_snippets(self, line_to_key):
        """
        Args:
            line_to_key (str)

        Returns:
            (list[str])

        Get exception and double underscore snippets.
        """

        custom_snippets = []
        word_to_key = line_to_key.split(' ')[-1]

        # add "Exception" to snippets after except
        custom_snippets.extend(self.get_exception_snippets(line_to_key))
        # add double underscore snippets
        custom_snippets.extend(self.get_double_underscore_snippets(word_to_key))

        if len(word_to_key) > 5:
            for word in self.custom_words() or ():
                if word.lower().startswith(word_to_key.lower()):
                    word_to_key_root = '.'.join(word_to_key.split('.')[:-1])
                    if '.' in word:
                        custom_snippets.append(word[len(word_to_key_root) +1:])
                    else:
                        custom_snippets.append(word[len(word_to_key_root):])

        return custom_snippets

    def get_double_underscore_snippets(self, word_to_key):
        """
        Args:
            word_to_key (str)

        Returns:
            (list[str] or [])

        Get double underscore snippets if<word_to_key> starts with an "_" char .
        """

        if word_to_key.startswith('_'):
            return ['__main__', '__name__', '__class__', '__init__']

        return []

    @utils.catch_error
    def custom_words(self):
        """
        Returns:
            (list[str] or [])

        Get user snippets from custom_snippets.json.
        """

        try:
            with open(CUSTOM_JSON, 'r') as opened_file:
                content = json.load(opened_file)
                return content['user']
        except:
            return []

    @utils.catch_error
    def get_exception_snippets(self, line_to_key):
        """
        Args:
            word_to_key (str)

        Returns:
            (list[str] or [])

        Get "Exception" snippets after "except".
        """

        words_before_key = re.findall('\w+\.*\w*', line_to_key)
        standard_except = 'except Exception as e:'

        if len(words_before_key) == 1:
            if standard_except.startswith(words_before_key[0]):
                return [standard_except]

        if len(words_before_key) != 2 or words_before_key[0] != 'except':
            return []

        errors = [x for x in __builtins__ if any(w in x.lower() for w in ['error', 'exception'])]
        errors = [e for e in errors if e.lower().startswith(words_before_key[1].lower())]

        return sorted([x +' as e:' for x in errors])

    @utils.catch_error
    def get_snippets(self, line, i, key):
        """
        Args:
            line (str)
            i (int)
            key (str)

        Returns:
            (list[str] or [])

        Get snippets list for current word.
        """

        word_before_key = ''

        # retrieve current word begining to new character
        for x in reversed(line[:i]):
            if not re.match('[a-zA-Z\._]', x):
                break

            word_before_key = x +word_before_key

        word_to_key = word_before_key.split('.')[-1] +key
        if not word_to_key:         # for instance, on backspace erasing the first
            return None         # character of a word, we don't want all snippets to rise

        found_snippets = self.get_dir_snippets(word_before_key)
        if not found_snippets:       # == if no dir() snippets
            found_snippets = self.get_modules_snippets()
            found_snippets.extend(self.get_text_snippets())

        if found_snippets:
            found_snippets = sorted(found_snippets)         # sort snippets
            found_snippets = list(set(found_snippets))      # filter duplicate snippets

        # get snippet words that start with word_to_key (no case match)
        matching = [s for s in found_snippets or () if s.lower().startswith(word_to_key.lower()) \
                    and word_to_key.lower() != s.lower()]

        matching.extend(self.get_custom_snippets(line[:i] +key))
        matching.extend(self.get_super_snippets(line[:i] +key))

        return matching

    @utils.catch_error
    def get_super_snippets(self, word):
        """
        Args:
            word (str)

        Get super(Class, self).func expression snippets.
        """

        if not word.strip() in 'super':
            return []

        cursor = self.text_edit.textCursor()

        class_name = self.get_previous_declaration_name(cursor, 'class')
        def_name = self.get_previous_declaration_name(cursor, 'def')

        short_super = 'super({}, self)'.format(class_name)
        long_super = 'super({}, self).{}('.format(class_name, def_name)

        result = [short_super, long_super] if class_name and def_name else \
                 [short_super] if class_name and not def_name else []

        return result

    def get_previous_declaration_name(self, cursor, decl_str):
        """
        Args:
            cursor (QTextCursor)
            decl_str (str) : "class" or "def"

        Retrieve current "class" or "def" name from previous lines.
        """

        doc = cursor.document()
        search_cursor = doc.find(QtCore.QRegExp(decl_str +'\s+(\w+)'),
                                 cursor.position(), doc.FindBackward)

        line = search_cursor.block().text()
        if not line:
            return None

        return line.split(decl_str)[1].split('(')[0].split(':')[0].strip()

    def get_text_snippets(self):
        """
        Returns:
            (list[str])

        Return words from current tab with length > 3.
        """

        text = self.text_edit.toPlainText()
        return [x for x in re.findall('[\w]+', text) if len(x) >3]

    @utils.catch_error
    def get_modules_snippets(self):
        """
        Returns:
            (list[str])

        Get modules snippets from sys.
        """

        imported_modules = [x.split('.')[0] for x in sys.modules]
        return list(set(imported_modules))

    def get_dir_snippets(self, word):
        """
        Returns:
            (list[str])

        Get dir(currentWord) as snippets ( removing the last '\.\w+' part )
        if error return empty list so the other snippets methods will be called.
        """

        if not word:
            return None
        if not '.' in word:
            if word in sys.modules:
                return dir(sys.modules[word])
            return None

        cuts = [x for x in word.split('.')[:-1] if x]
        if not cuts or cuts[0] not in sys.modules:
            return None

        try:
            return dir(eval('.'.join(cuts)))
        except:
            return None

    def on_cursor_change(self):
        """ Close the snippets box if users clicks into the QTextEdit. """
        if self.trigger_on_cursor_change:
            if self.box:
                self.kill_box()

        else:
            self.trigger_on_cursor_change = True



class SnippetBox(QtWidgets.QWidget):

    """
    Custom QWidget with QListWidget that will hold completion words, and arrow keys loop
    (up at row 0 will set selection at the end and reverse)
    """

    itemPressed = QtCore.Signal(QtWidgets.QListWidgetItem)

    def __init__(self, parent, list, pos):
        super(SnippetBox, self).__init__(parent)

        self.setStyleSheet('border : transparent;')

        lay = QtWidgets.QVBoxLayout(self)
        self.view = QtWidgets.QListWidget()
        lay.addWidget(self.view)

        for word in list:
            self.add_item(word)

        self.move(pos)
        self.set_current_item(self.item(0))

        for w in [self, self.layout()]:
            w.setContentsMargins(0, 0, 0, 0)

        view_width = self.size_hint_for_column(0) + 2 * self.frame_width()
        view_height = self.size_hint_for_row(0) * self.count() + 2 * self.frame_width()
        self.setMaximumSize(view_width +16, view_height +2)

        self.view.itemPressed.connect(self.itemPressed.emit)

    def add_item(self, name):
        return self.view.addItem(name)

    def current_item(self):
        return self.view.currentItem()

    def set_current_item(self, item):
        return self.view.setCurrentItem(item)

    def item(self, index):
        return self.view.item(index)

    def frame_width(self):
        return self.view.frameWidth()

    def size_hint_for_column(self, col):
        return self.view.sizeHintForColumn(col)

    def size_hint_for_row(self, row):
        return self.view.sizeHintForRow(row)

    def set_current_row(self, row):
        return self.view.setCurrentRow(row)

    def current_row(self):
        return self.view.currentRow()

    def count(self):
        return self.view.count()

    def go_down(self):
        """
        Go an item down. If current item is already the last one, got to the top.
        """

        currRow = self.current_row()
        if currRow +1 < self.count():
            self.set_current_row(currRow +1)
        else:
            self.set_current_row(0)

    def go_up(self):
        """
        Go an item up. If current item is already the first one, got to the bottom.
        """

        currRow = self.current_row()
        if currRow -1 > 0:
            self.set_current_row(currRow -1)
        else:
            self.set_current_row(self.count() -1)
