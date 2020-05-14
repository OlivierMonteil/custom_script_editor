###############################################################################
#           Script for customizing Maya's script editor hotkeys.
###############################################################################

__author__ = 'Olivier Monteil'
__version__ = 1.1
__ide_version__ = 'Atom'

import re

try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide import QtGui, QtCore
    from PySide import QtGui as QtWidgets

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class KeysHandler(QtCore.QObject):
    def __init__(self, parent=None):
        super(KeysHandler, self).__init__(parent)

    #--------------------------------------------------------------------------
    def eventFilter(self, obj, event):
        if event.type() == event.KeyPress:
            # handle "embracing" character if some text is selected

            key = event.key()

            if event.key() == QtCore.Qt.Key_Backtab:
                self.un_indent(obj)
                return True

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

            if key == QtCore.Qt.Key_Down:
                if event.modifiers() == QtCore.Qt.ControlModifier:
                    return self.move_lines(obj, direction='down')
            if key == QtCore.Qt.Key_Up:
                if event.modifiers() == QtCore.Qt.ControlModifier:
                    return self.move_lines(obj, direction='up')

        # handle event as usual if nothing has been filtered ahead
        return False
    #--------------------------------------------------------------------------
    def move_lines(self, obj, direction=None):
        if not direction in ['up', 'down']:
            return False

        cursor = obj.textCursor()
        sel_start, sel_end, reversed = self.get_sel_start_end_reverse(cursor)

        # get selected lines text, and start/end positions in block (will be used
        # to re-create selection after moving current lines)
        text, start_in_block, end_in_block = self.get_selected_lines(obj, sel_start, sel_end,
                                                  set_selection=True, pos_in_block=True)

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
            self.restore_selection(obj,
                                   line_start +start_in_block,
                                   line_end +end_in_block,
                                   reversed)

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
            self.restore_selection(obj,
                                   line_start +start_in_block,
                                   line_end +end_in_block,
                                   reversed)

        return True
    #--------------------------------------------------------------------------
    def duplicate_lines(self, obj):
        # (called on Ctrl+Shift+D) depluciate selected lines below themselves,
        # or the line with the cursor on if no selection

        cursor = obj.textCursor()
        sel_start, sel_end, reversed = self.get_sel_start_end_reverse(cursor)
        text = self.get_selected_lines(obj, sel_start, sel_end)

        # go at the end of the selected lines and insert the selected lines below
        cursor.setPosition(sel_end, cursor.MoveAnchor)
        cursor.movePosition(cursor.EndOfLine, cursor.MoveAnchor)
        cursor.insertText('\n' +text)

        self.restore_selection(obj, sel_start, sel_end, reversed)
    #--------------------------------------------------------------------------
    def restore_selection(self, obj, start, end, reversed):
        cursor = obj.textCursor()
        # restore the "right order" between <start> and <end> positions, as user may have
        # selected text from a <start> position that his greater than the <end> one and we
        # want to set his selection back without inverting the start/end positions
        new_start = start if not reversed else end
        new_end = end if not reversed else start

        # perform selection into cursor
        cursor.setPosition(new_start, cursor.MoveAnchor)
        cursor.setPosition(new_end, cursor.KeepAnchor)
        # don't forget to set modified cursor on object as, for now, modified
        # cursor variable is just a virtual modification of the initial cursor
        obj.setTextCursor(cursor)
    #--------------------------------------------------------------------------
    def get_sel_start_end_reverse(self, cursor):
        # get start/end positions from selected text, with sel_start <= sel_end.
        # If the order between sel_start and sel_end, return <reversed> value as True
        # so the selection order may be restaured correctly later.
        sel_start = cursor.selectionStart()
        sel_end = cursor.selectionEnd()
        reversed = sel_start == cursor.position()

        return min(sel_start, sel_end), max(sel_start, sel_end), reversed
    #--------------------------------------------------------------------------
    def embrace_text_with(self, obj, open_char, close_char):
        # add <open_char> and <close_char> characters before and after selection, keeping selection
        # (the return value will be propagated to eventFilter's :
        # if case of no selection, the event will not be filtered and the initial
        # key press will be processed as usual)

        cursor = obj.textCursor()
        sel = cursor.selection().toPlainText()

        if sel:
            sel_start, sel_end, reversed = self.get_sel_start_end_reverse(cursor)
            cursor.insertText('{}{}{}'.format(open_char, sel, close_char))

            # offset the selection, due to the adding of a character before
            self.restore_selection(obj, sel_start +1, sel_end +1, reversed)
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
    #--------------------------------------------------------------------------
    def un_indent(self, obj):
        # improve maya un-indent shortcut that stops to the first empty line encountered

        cursor = obj.textCursor()
        sel_start, sel_end, reversed = self.get_sel_start_end_reverse(cursor)

        # retrieve start/end blocks to get the iteration range
        cursor.setPosition(sel_end, cursor.MoveAnchor)
        end_block = cursor.blockNumber()
        cursor.setPosition(sel_start, cursor.MoveAnchor)     # also go to the firstiteration line
        start_block = cursor.blockNumber()

        # go to the start of line (as cursor.NextBlock does) to be sure that
        # cursor.deleteChar() operates on the starting characters of the line
        cursor.movePosition(cursor.StartOfLine, cursor.MoveAnchor)

        for i in range(end_block -start_block +1):
            line = cursor.block().text()

            # go to the next line if line is empty
            if not line:
                cursor.movePosition(cursor.NextBlock, cursor.MoveAnchor)
                continue

            if line[0] == '\t':
                cursor.deleteChar()
                cursor.movePosition(cursor.NextBlock, cursor.MoveAnchor)
                continue

            elif len(line) < 3:
                cursor.movePosition(cursor.NextBlock, cursor.MoveAnchor)
                continue

            # perform line un-indent
            if line[:4] == '    ':
                for x in range(4):
                    cursor.deleteChar()

            # go to the next line
            cursor.movePosition(cursor.NextBlock, cursor.MoveAnchor)
    #--------------------------------------------------------------------------
    def handle_backspace(self, obj):
        if self.indent_backspace(obj):
            return True
        if self.remove_open_close_chars(obj):
            return True
        return False
    #--------------------------------------------------------------------------
    def remove_open_close_chars(self, obj):
        cursor = obj.textCursor()
        pos = cursor.positionInBlock()
        line = cursor.block().text()

        if not line:
            return False

        if pos == 0 or pos == len(line):
            return False

        for open_char, close_char in [('(', ')'), ('[', ']'), ('{', '}'), ('\'', '\''), ('"', '"')]:
            if line[pos-1] == open_char and line[pos] == close_char:
                cursor.deleteChar()
                cursor.deletePreviousChar()
                return True

        return False
    #--------------------------------------------------------------------------
    def indent_backspace(self, obj):
        """
        Input:
            <obj>           Qt widget (most likely in this case, a QTextEdit)

        Return value:
            bool

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
            for i in range(4):
                cursor.deletePreviousChar()
            return True

        return False
    #--------------------------------------------------------------------------
    def ignore_if_next(self, obj, char):
        """
        Inputs:
            <obj>           Qt widget (most likely in this case, a QTextEdit)
            <char>          str

        Return value:
            bool

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
    #--------------------------------------------------------------------------
    def get_selected_lines(self, obj, start, end, set_selection=False, pos_in_block=False):
        """
        Inputs:
            <obj>                   Qt widget (most likely in this case, a QTextEdit)
            <start>                 int
            <end>                   int
            *<set_selection>        bool
            *<pos_in_block>         bool

        Return value:
            str

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
            return cursor.selectedText(), start_in_block, end_in_block
        else:
            return cursor.selectedText()
