#-*- coding: utf-8 -*-

"""
Script for customizing Maya's script editor hotkeys.
"""

from PySide2 import QtCore, QtGui

from custom_script_editor.multi_cursors import MultiCursorManager, MultiCursor
from custom_script_editor import constants as kk



def extra_selections_updated(func):
    """
    Decorator that asks MultiCursorManager instance (if any) to update extra
    selections after <func> is executed.
    """

    def wrap(self, *args, **kwargs):
        multi_handler = self.get_multi_handler()

        result = func(self, *args, **kwargs)

        if multi_handler:
            multi_handler.update_extra_selections()

        return result
    return wrap


class KeysHandler(QtCore.QObject):
    """
    Events filter for Keys handling.
    """

    def __init__(self, tab_type, parent=None):
        super(KeysHandler, self).__init__(parent)

        self.tab_type = tab_type
        self.comment_char = '// ' if tab_type == 'MEL' else '# '

    def get_multi_handler(self):
        """
        Returns:
            (MultiCursorManager)

        Get MultiCursorManager instance from QTextEdit.
        """

        txt_edit = self.parent()
        return txt_edit.findChild(MultiCursorManager)

    def get_cursor(self, obj):
        """
        Args:
            obj (QTextEdit)

        Returns:
            (MultiCursor)

        Get new cursor as MultiCursor insance. This cursor will "inherit" from
        current MultiCursorManager's cursors if exists.
        """

        multi_manager = self.get_multi_handler()
        if not multi_manager:
            return MultiCursor([obj.textCursor()], obj)

        return MultiCursor(multi_manager.cursors, obj)

    @extra_selections_updated
    def eventFilter(self, obj, event):
        """
        Args:
            obj (QTextEdit)

        Filter and handle key events (only).
        """

        if event.type() == event.KeyPress:
            # handle "embracing" character if some text is selected

            key = event.key()

            if event.modifiers() == (QtCore.Qt.AltModifier | QtCore.Qt.ControlModifier):
                # add new multi-cursor under current one
                if key == QtCore.Qt.Key_Down:
                    multi_handler = self.get_multi_handler()
                    multi_handler.add_cursor_from_key('down')
                    return True
                # add new multi-cursor above current one
                if key == QtCore.Qt.Key_Up:
                    multi_handler = self.get_multi_handler()
                    multi_handler.add_cursor_from_key('up')
                    return True

            cursor = self.get_cursor(obj)

            if event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier):
                # handle lines duplication on Ctrl+Shift+D
                if key == QtCore.Qt.Key_D:
                    cursor.duplicate_lines()
                    return True

                # extend selections on previous/next word on Ctrl +Shift +Left/Right
                if key in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Right):
                    cursor.extend_selections(key, by_word=True)
                    return True

                return False


            if event.modifiers() == (QtCore.Qt.ControlModifier | QtCore.Qt.KeypadModifier):
                # handle block comments on Ctrl+Shift+/
                if event.key() == QtCore.Qt.Key_Slash:
                    cursor.toggle_block_comment(self.comment_char)
                    return True

                return False


            if event.modifiers() == QtCore.Qt.ControlModifier:
                # move lines on Ctrl +down/up
                if key == QtCore.Qt.Key_Down:
                    return cursor.move_lines('down')
                if key == QtCore.Qt.Key_Up:
                    return cursor.move_lines('up')

                if key in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Right):
                    operation = cursor.get_move_operation_from_key(key, by_word=True)
                    cursor.multi_movePosition(operation, cursor.MoveAnchor)
                    return True

                # paste on Ctrl +V
                if key == QtCore.Qt.Key_V:
                    text = QtGui.QClipboard().text()
                    cursor.insertText(text)
                    return True

                # clear multi-cursors on Ctrl +A and select all
                if key == QtCore.Qt.Key_A:
                    multi_manager = self.get_multi_handler()
                    multi_manager.clear_cursors()
                    cursor = multi_manager.cursors[-1]
                    cursor.movePosition(cursor.Start, cursor.MoveAnchor)
                    cursor.movePosition(cursor.End, cursor.KeepAnchor)
                    self.parent().setTextCursor(cursor)
                    return True

                return False


            if event.modifiers() == QtCore.Qt.ShiftModifier:
                # extend selections on Shift +cursor move
                if key in kk.MOVE_KEYS:
                    cursor.extend_selections(key)
                    return True

            if key in kk.MOVE_KEYS:
                operation = cursor.get_move_operation_from_key(key)
                cursor.multi_movePosition(operation, cursor.MoveAnchor)
                return True

            # handle embracing characters
            if event.text() == '`':
                return cursor.embrace_text_with('`', '`')
            if key == QtCore.Qt.Key_ParenLeft:
                return cursor.embrace_text_with('(', ')')
            if key == QtCore.Qt.Key_BracketLeft:
                return cursor.embrace_text_with('[', ']')
            if key == QtCore.Qt.Key_BraceLeft:
                return cursor.embrace_text_with('{', '}')
            if key == QtCore.Qt.Key_ParenRight:
                return cursor.ignore_if_next(')')
            if key == QtCore.Qt.Key_BracketRight:
                return cursor.ignore_if_next(']')
            if key == QtCore.Qt.Key_BraceRight:
                return cursor.ignore_if_next('}')
            if key == QtCore.Qt.Key_QuoteDbl:
                return cursor.embrace_text_with('"', '"')
            if key == QtCore.Qt.Key_Apostrophe:
                return cursor.embrace_text_with('\'', '\'')

            # handle blocks unindent
            if key == QtCore.Qt.Key_Backtab:
                cursor.unindent()
                return True

            # delete
            if event.key() == QtCore.Qt.Key_Delete:
                cursor.deleteChar()
                block = cursor.block()
                return True

            # backspace
            if event.key() == QtCore.Qt.Key_Backspace:
                return cursor.handle_backspace()

            # any other cases
            text = event.text()
            if text and text in kk.CHARACTERS:
                cursor.insertText(text)
                return True

            if text and text in kk.SPECIAL_CHARS:
                cursor.insertText(text)
                return True


        # handle event as usual if nothing has been filtered ahead
        return False
