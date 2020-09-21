"""
Script for customizing Maya's script editor hotkeys.
"""

import re

try:
    from PySide2 import QtCore
except ImportError:
    from PySide import QtCore

OPEN_CLOSE_CHARS = [
    ('(', ')'),
    ('[', ']'),
    ('{', '}'),
    ('\'', '\''),
    ('"', '"'),
    ('`', '`')
]

class KeysHandler(QtCore.QObject):

    def __init__(self, tab_type, parent=None):
        super(KeysHandler, self).__init__(parent)

        self.tab_type = tab_type
        self.comment_char = '// ' if tab_type == 'MEL' else '# '

    def eventFilter(self, obj, event):
        """
        Filter and handle key events (only).
        """

        if event.type() == event.KeyPress:
            # handle "embracing" character if some text is selected

            key = event.key()

            if event.text() == '`':
                return self.embrace_text_with(obj, '`', '`')

            if key == QtCore.Qt.Key_Backtab:
                self.un_indent(obj)
                return True

            if event.key() == QtCore.Qt.Key_Slash:
                if event.modifiers() == QtCore.Qt.ControlModifier | QtCore.Qt.KeypadModifier:
                    self.toggle_block_comment(obj)
                    return True
                return False

            if event.key() == QtCore.Qt.Key_Backspace:
                return self.handle_backspace(obj)

            if key == QtCore.Qt.Key_ParenLeft:
                return self.embrace_text_with(obj, '(', ')')
            if key == QtCore.Qt.Key_BracketLeft:
                return self.embrace_text_with(obj, '[', ']')
            if key == QtCore.Qt.Key_BraceLeft:
                return self.embrace_text_with(obj, '{', '}')
            if key == QtCore.Qt.Key_ParenRight:
                return self.ignore_if_next(obj, ')')
            if key == QtCore.Qt.Key_BracketRight:
                return self.ignore_if_next(obj, ']')
            if key == QtCore.Qt.Key_BraceRight:
                return self.ignore_if_next(obj, '}')
            if key == QtCore.Qt.Key_QuoteDbl:
                return self.embrace_text_with(obj, '"', '"')
            if key == QtCore.Qt.Key_Apostrophe:
                return self.embrace_text_with(obj, '\'', '\'')

            # handle lines duplication on Ctrl+Shift+D
            if key == QtCore.Qt.Key_D:
                if event.modifiers() == QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier:
                    self.duplicate_lines(obj)
                    return True
                return False

            if key == QtCore.Qt.Key_Down:
                if event.modifiers() == QtCore.Qt.ControlModifier:
                    return self.move_lines(obj, direction='down')
                return False

            if key == QtCore.Qt.Key_Up:
                if event.modifiers() == QtCore.Qt.ControlModifier:
                    return self.move_lines(obj, direction='up')
                return False

        # handle event as usual if nothing has been filtered ahead
        return False

    def move_lines(self, obj, direction=None):
        """
        Args:
            obj (QtWidgets.QtextEdit)
            direction (str) : 'up' or 'down'

        Returns:
            (bool)

        Move up/down selected lines on up/down keys.
        """

        if not direction in ['up', 'down']:
            return False

        cursor = obj.textCursor()
        sel_start, sel_end, is_reversed = self.get_sel_start_end_reverse(cursor)

        # get selected lines text, and start/end positions in block (will be used
        # to re-create selection after moving current lines)
        text, start_in_block, end_in_block = self.get_selected_lines(
            obj,
            sel_start,
            sel_end,
            set_selection=True,
            pos_in_block=True
        )

        # get new textCursor (modified by get_selected_lines)
        cursor = obj.textCursor()
        # remove selected lines
        cursor.removeSelectedText()

        if direction == 'up':
            # remove previous '\n' character (we are now at the end the previous line)
            cursor.deletePreviousChar()
            # move cursor to the start of the line, and get this previous line
            # position (for selection re-creating)
            cursor.movePosition(cursor.StartOfLine, cursor.MoveAnchor)
            line_start = cursor.position()
            # insert removed text and add a '\n' (we are now at the start of the
            # line after the moved lines, due to the '\n')
            cursor.insertText(text +'\n')
            # go back to the start of the last moved line and get the position
            # of the line (still for selection re-creating)
            cursor.movePosition(cursor.PreviousBlock, cursor.MoveAnchor)
            cursor.movePosition(cursor.StartOfLine, cursor.MoveAnchor)
            line_end = cursor.position()

            # re-create selection starting from moved start/end lines and adding
            # start/end initial positions in block
            self.restore_selection(
                obj,
                line_start +start_in_block,
                line_end +end_in_block,
                is_reversed
            )

        else:
            # remove next '\n' character (we are now at the start of the next line)
            cursor.deleteChar()
            # move cursor to the end of the line, and get the next line position
            # by adding 1 to the current position (for selection re-creating)
            cursor.movePosition(cursor.EndOfLine, cursor.MoveAnchor)
            line_start = cursor.position() +1    # the 1 added corresponds to the '\n' at the end of line
            # insert removed text after a '\n' (we are now at the end of the
            # last moved lines)
            cursor.insertText('\n' +text)
            # go to the start of the last moved line and get the position
            # of the line (still for selection re-creating)
            cursor.movePosition(cursor.StartOfLine, cursor.MoveAnchor)
            line_end = cursor.position()
            # re-create selection starting from moved start/end lines and adding
            # start/end initial positions in block
            self.restore_selection(
                obj,
                line_start +start_in_block,
                line_end +end_in_block,
                is_reversed
            )

        return True

    def toggle_block_comment(self, obj):
        """
        Args:
            obj (QtWidgets.QtextEdit)

        (called on Ctrl+/)

        Toggle comments on selected block.
        """

        # get current selected text and positions
        cursor = obj.textCursor()
        sel_start, sel_end, is_reversed = self.get_sel_start_end_reverse(cursor)
        text = self.get_selected_lines(obj, sel_start, sel_end)

        pos, number = self.get_block_min_indent(text)
        if pos is None:
            return

        # extend selection to whole lines.
        cursor.setPosition(sel_start, cursor.MoveAnchor)
        cursor.movePosition(cursor.StartOfLine, cursor.MoveAnchor)
        cursor.setPosition(sel_end, cursor.KeepAnchor)
        cursor.movePosition(cursor.EndOfLine, cursor.KeepAnchor)

        # replace lines with comment-toggled ones
        new_text, inserted = self.comment_toggled_text(text, pos)
        cursor.insertText(new_text)

        # restore selection
        if inserted:
            sel_start += len(self.comment_char)
            sel_end += len(self.comment_char)*number
        else:
            sel_start -= len(self.comment_char)
            sel_end -= len(self.comment_char)*number

        self.restore_selection(obj, sel_start, sel_end, is_reversed)

    def get_block_min_indent(self, text):
        """
        Args:
            text (str)

        Returns:
            (int): number of indentation white spaces
            (int): number of comment chars to insert/remove

        Get minimum indentation level (x4 space chars) from text.
        """

        indent = None
        number = 0

        for line in text.split('\n'):
            # skip empty lines
            if self.is_empty(line):
                continue

            idnt_txt = re.search('^\s+', line)
            # line has no indentation
            if not idnt_txt:
                indent = 0
                number += 1
                continue

            # do not bother inspecting lines if minimum indent is already 0
            if indent == 0:
                number += 1
                continue

            idnt_txt = idnt_txt.group(0)

            indent = min(indent, len(idnt_txt)) if indent is not None else len(idnt_txt)
            number += 1

        return indent, number

    def comment_toggled_text(self, text, pos):
        """
        Args:
            text (str)

        Returns:
            (str): the new text
            (bool): the insert/remove mode

        Get comment-inserted/removed text.
        """

        new_lines = []
        lines = text.split('\n')
        insert = False

        # check if comments has to be inserted or removed
        for line in lines:
            if not self.is_empty(line) and len(line) > pos:
                if not line[pos:pos+len(self.comment_char)] == self.comment_char:
                    insert = True
                    break

        if insert:
            for line in lines:
                # insert '# ' at pos if line is not empty
                if not self.is_empty(line) and len(line) > pos:
                    new_lines.append(
                        line[:pos] +self.comment_char +line[pos:]
                    )
                else:
                    new_lines.append(line)

        else:
            for line in lines:
                # remove '# ' at pos if line is not empty
                if not self.is_empty(line) and len(line) > pos:
                    new_lines.append(
                        line[:pos] +line[pos+len(self.comment_char):]
                    )
                else:
                    new_lines.append(line)

        return '\n'.join(new_lines), insert

    def is_empty(self, line):
        """
        Returns:
            (bool)

        Check if line is empty (or whitespaces only).
        """

        if not line or line == '\n':
            return True

        idnt_txt = re.match('\s+', line)
        if idnt_txt and len(idnt_txt.group(0)) == len(line):
            return True

        return False

    def duplicate_lines(self, obj):
        """
        Args:
            obj (QtWidgets.QtextEdit)

        (called on Ctrl+Shift+D)

        Duplicate selected lines, or the line with the cursor on if no selection.
        """

        cursor = obj.textCursor()
        sel_start, sel_end, is_reversed = self.get_sel_start_end_reverse(cursor)
        text = self.get_selected_lines(obj, sel_start, sel_end)

        # go at the end of the selected lines and insert the selected lines below
        cursor.setPosition(sel_end, cursor.MoveAnchor)
        cursor.movePosition(cursor.EndOfLine, cursor.MoveAnchor)
        cursor.insertText('\n' +text)

        self.restore_selection(obj, sel_start, sel_end, is_reversed)

    def restore_selection(self, obj, start, end, is_reversed):
        """
        Args:
            obj (QtWidgets.QtextEdit)
            start (int)
            end (int)
            is_reversed (bool) : whether the user selected from <end> to <start> or not

        Restore user's selection after manipulations.
        """

        cursor = obj.textCursor()
        # restore the "right order" between <start> and <end> positions, as user may have
        # selected text from a <start> position that his greater than the <end> one and we
        # want to set his selection back without inverting the start/end positions
        new_start = start if not is_reversed else end
        new_end = end if not is_reversed else start

        # perform selection into cursor
        cursor.setPosition(new_start, cursor.MoveAnchor)
        cursor.setPosition(new_end, cursor.KeepAnchor)
        # don't forget to set modified cursor on object as, for now, modified
        # cursor variable is just a virtual modification of the initial cursor
        obj.setTextCursor(cursor)

    def get_sel_start_end_reverse(self, cursor):
        """
        Args:
            cursor (QtGui.QTextCursor)

        Returns:
            (int, int, bool)

        Get start/end positions from selected text, with sel_start <= sel_end.
        If the order between sel_start and sel_end, return <is_reversed> as True,
        so the selection order may be restaured correctly later.
        """

        sel_start = cursor.selectionStart()
        sel_end = cursor.selectionEnd()
        is_reversed = sel_start == cursor.position()

        return min(sel_start, sel_end), max(sel_start, sel_end), is_reversed

    def embrace_text_with(self, obj, open_char, close_char):
        """
        Args:
            obj (QtWidgets.QtextEdit)
            open_char (str)
            close_char (str)

        Returns:
            bool

        Add <open_char> and <close_char> characters before and after selection.
        The return value will be propagated to eventFilter's.
        """

        cursor = obj.textCursor()
        sel = cursor.selection().toPlainText()

        if sel:
            sel_start, sel_end, is_reversed = self.get_sel_start_end_reverse(cursor)
            cursor.insertText('{}{}{}'.format(open_char, sel, close_char))

            # offset the selection, due to the adding of a character before
            self.restore_selection(obj, sel_start +1, sel_end +1, is_reversed)
            return True

        else:
            if self.ignore_if_next(obj, open_char):
                return True

            pos = cursor.positionInBlock()
            line = cursor.block().text()

            if open_char in ['\'', '"']:
                if pos >= 2 and line[pos-2:pos] == 2*open_char:
                    # skip two or more similar characters before (last quote of
                    # a triplequote, for instance)
                    return False

            # skip if next character is not a space character or in ()[]{}'"
            if pos < len(line) -1 and not re.match('\s*\(*\)*\[*\]*\{*\}*\'*\"*', line[pos]):
                return False

            cursor.insertText('{}{}'.format(open_char, close_char))
            cursor.setPosition(cursor.position() -1, cursor.MoveAnchor)
            obj.setTextCursor(cursor)
            return True

        return False

    def un_indent(self, obj):
        """
        Args:
            obj (QtWidgets.QtextEdit)

        Improve maya un-indent shortcut that stops to the first empty line
        encountered.
        """

        cursor = obj.textCursor()
        sel_start, sel_end, _ = self.get_sel_start_end_reverse(cursor)

        # retrieve start/end blocks to get the iteration range
        cursor.setPosition(sel_end, cursor.MoveAnchor)
        end_block = cursor.blockNumber()
        cursor.setPosition(sel_start, cursor.MoveAnchor)     # also go to the firstiteration line
        start_block = cursor.blockNumber()

        # go to the start of line (as cursor.NextBlock does) to be sure that
        # cursor.deleteChar() operates on the starting characters of the line
        cursor.movePosition(cursor.StartOfLine, cursor.MoveAnchor)

        for _ in range(end_block -start_block +1):
            line = cursor.block().text()

            # go to the next line if line is empty
            if not line:
                cursor.movePosition(cursor.NextBlock, cursor.MoveAnchor)
                continue

            if line[0] == '\t':
                cursor.deleteChar()
                cursor.movePosition(cursor.NextBlock, cursor.MoveAnchor)
                continue

            if len(line) < 3:
                cursor.movePosition(cursor.NextBlock, cursor.MoveAnchor)
                continue

            # perform line un-indent
            if line[:4] == '    ':
                for i in range(4):
                    cursor.deleteChar()

            # go to the next line
            cursor.movePosition(cursor.NextBlock, cursor.MoveAnchor)

    def handle_backspace(self, obj):
        """
        Args:
            obj (QtWidgets.QtextEdit)

        Returns:
            (bool)

        Handle backspace on identation or open/close chars as parenthesis, brackets,
        string quotes, etc.
        """

        if self.indent_backspace(obj):
            return True
        if self.remove_open_close_chars(obj):
            return True
        return False

    def remove_open_close_chars(self, obj):
        """
        Args:
            obj (QtWidgets.QtextEdit)

        Returns:
            (bool)
        """

        cursor = obj.textCursor()
        pos = cursor.positionInBlock()
        line = cursor.block().text()

        if not line:
            return False

        if pos == 0 or pos == len(line):
            return False

        for open_char, close_char in OPEN_CLOSE_CHARS:
            if line[pos-1] == open_char and line[pos] == close_char:
                cursor.deleteChar()
                cursor.deletePreviousChar()
                return True

        return False

    def indent_backspace(self, obj):
        """
        Args:
            obj (QtWidgets.QtextEdit)

        Returns:
            (bool)

        Handle indentation on backspace :

            - remove the four last characters if they are all white space characters,
              and current cursor position is at n*4 from the start of the line.
        """

        cursor = obj.textCursor()
        if cursor.selectedText():
            return False

        pos = cursor.positionInBlock()
        line_to_cursor = cursor.block().text()[:pos]

        # skip if line is shorter than 4 characters
        if not line_to_cursor and len(line_to_cursor) < 4:
            return False

        # skip if current position is not a multiple of 4
        if len(line_to_cursor)%4:
            return False

        # remove the four last whitespace characters
        if line_to_cursor[-4:] == '    ':
            for _ in range(4):
                cursor.deletePreviousChar()
            return True

        return False

    def ignore_if_next(self, obj, char):
        """
        Args:
            obj (QtWidgets.QtextEdit)
            char (str)

        Returns:
            (bool)

        Move the cursor forward if next character (from cursor) is the same as
        the input <char>.
        """

        cursor = obj.textCursor()
        line = cursor.block().text()
        pos = cursor.positionInBlock()

        if len(line) > pos and line[pos] == char:
            cursor.setPosition(cursor.position() +1, cursor.MoveAnchor)
            obj.setTextCursor(cursor)
            return True

        return False

    def get_selected_lines(self, obj, start, end, set_selection=False, pos_in_block=False):
        """
        Args:
            obj (QtWidgets.QtextEdit)
            start (int)
            end (int)
            set_selection (bool, optional)
            pos_in_block (bool, optional)

        Returns:
            (str)

        Get lines froms selection :

            - if no selection, return the content of the line with cursor on it
            - if some text is selected, extend the returned text to the start of
              the first line and the end of the last line.

            - if <set_selection> : set selection as the whole lines
            - if <pos_in_block> : return start/end positions in block
        """

        cursor = obj.textCursor()

        # move to <start>
        cursor.setPosition(start, cursor.MoveAnchor)
        # get block-relative position of <start>
        start_in_block = cursor.positionInBlock()
        # move start position to the start of the line
        cursor.movePosition(cursor.StartOfLine, cursor.MoveAnchor)
        # move to <end> keeping anchor
        cursor.setPosition(end, cursor.KeepAnchor)
        # get block-relative position of <end>
        end_in_block = cursor.positionInBlock()
        # move start position to the end of the line
        cursor.movePosition(cursor.EndOfLine, cursor.KeepAnchor)

        if set_selection:
            obj.setTextCursor(cursor)

        if pos_in_block:
            return (
                cursor.selectedText().replace(u'\u2029', '\n'),
                start_in_block,
                end_in_block
            )

        return cursor.selectedText().replace(u'\u2029', '\n')
