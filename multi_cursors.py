"""
MultiCursorManager : events filter that handles multi cursors in QTextEdit.
MultiCursor : QtGui.QTextCursor re-implementation that allow multi-editing.
"""

import re

from PySide2 import QtWidgets, QtCore, QtGui

from custom_script_editor import constants as kk


OPEN_CLOSE_CHARS = [
    ('(', ')'),
    ('[', ']'),
    ('{', '}'),
    ('\'', '\''),
    ('"', '"'),
    ('`', '`')]


class MultiCursorManager(QtCore.QObject):

    """
    Custom eventFilter installed on Maya Script Editor cmdScrollFieldExecuters.
    Allows multi-cursor editing with fake cursors display and keyEvents filtering.
    """

    line_max_length = 80

    events_trigger = [
        QtCore.QEvent.MouseButtonPress,
        QtCore.QEvent.MouseButtonRelease
    ]
    cursor_colors = [
        (94, 132, 255),
        (117, 229, 92)
    ]

    def __init__(self, parent):
        super(MultiCursorManager, self).__init__(parent)

        self.txt_edit = None
        self.cursors = []
        self.multi_cursor = []
        self.overlay = []
        self.repaint_region = None

        # set cursor blinking timer
        self.timer = QtCore.QTimer(interval = 500)
        self.timer.timeout.connect(self.blink_cursors)

        self.cursor_state = True    # used to switch cursor's colors

    def add_cursor_from_key(self, direction):
        """
        Args:
            direction (str) : 'up' or 'down'
        """

        if not direction in ('up', 'down'):
            return True

        new_cursor = self.txt_edit.textCursor()
        if direction == 'up':
            new_cursor.movePosition(new_cursor.Up, new_cursor.MoveAnchor)
        elif direction == 'down':
            new_cursor.movePosition(new_cursor.Down, new_cursor.MoveAnchor)

        already_in = self.cursor_exists(new_cursor)

        if not already_in:
            self.add_cursor(new_cursor)

        return True

    def add_cursor(self, cursor):
        """
        Args:
            cursor (QtGui.QTextCursor)

        Add <cursor> to the current ones.
        """

        # add new_cursor to self.cursors
        self.cursors.append(cursor)
        # start blinking timer if not already active
        if not self.timer.isActive():
            self.timer.start()

        self.update_extra_selections()
        # set QTextEdit cursor on the last one
        self.txt_edit.setTextCursor(self.cursors[-1])

        return True

    def remove_cursor(self, cursor):
        """
        Args:
            cursor (QtGui.QTextCursor)

        Remove <cursor> to the current ones.
        """

        self.cursors.remove(cursor)

        # stop blinking timer if no multi cursors anymore
        if len(self.cursors) == 1:
            self.timer.stop()

        # repaint the removed cursor's area
        self.update_cursors([cursor])
        # set QTextEdit cursor on the last one
        self.txt_edit.setTextCursor(self.cursors[-1])

        self.update_extra_selections()

        return True

    def clear_cursors(self):
        """
        Clear all multi-cursor.
        """

        # remove all multi-cursors on simple LMB click
        self.timer.stop()
        old_cursors = self.cursors
        self.cursors = [self.cursors[-1]]
        # repaint all removed cursors area
        self.update_extra_selections()

        self.txt_edit.setTextCursor(self.cursors[-1])
        self.update_cursors(old_cursors)

    def eventFilter(self, obj, event):
        # (no need to run set_customize_on_tab_change and customize_script_editor
        # if the Script Editor is already opened)

        if not event.type() in self.events_trigger:
            return False

        self.txt_edit = obj.parent()

        if event.type() == QtCore.QEvent.MouseButtonRelease:
            if event.button() == QtCore.Qt.LeftButton:
                # get new QTextCursor at mouse position
                new_cursor = self.txt_edit.textCursor()

                if event.modifiers() == QtCore.Qt.ControlModifier:
                    # check if new_cursor is already in self.cursors
                    already_in = self.cursor_exists(new_cursor)

                    if not already_in:
                        return self.add_cursor(new_cursor)

                    else:
                        # remove from self.cursors if more than one
                        if len(self.cursors) > 1:
                            return self.remove_cursor(already_in)

                        # no need to go any further
                        return True

                else:
                    self.add_cursor(new_cursor)
                    self.clear_cursors()

        # pass the event through
        return False

    def update_extra_selections(self):
        """
        Display multi-selections into QTextEdit.
        """

        if len(self.cursors) > 1:
            # get highlight colors
            highlight_color = self.txt_edit.palette().highlight()
            highlight_txt_color = self.txt_edit.palette().highlightedText()

            extra_selections = []

            for cursor in self.cursors:
                extra_sel = self.txt_edit.ExtraSelection()
                extra_sel.cursor = cursor
                extra_sel.format.setBackground(highlight_color)
                extra_sel.format.setForeground(highlight_txt_color)
                extra_selections.append(extra_sel)

            self.txt_edit.setExtraSelections(extra_selections)

        else:
            # clear extra selections
            self.txt_edit.setExtraSelections([])

    def cursor_exists(self, cursor):
        """
        Args:
            cursor (QtGui.QTextCursor)

        Returns:
            (QtGui.QTextCursor or None)

        Check in self.cursors if any cursor already exists at the same position.
        """

        for c in self.cursors or ():
            if cursor.position() == c.position():
                return c

        return None

    def install(self, txt_edit):
        """
        Args:
            txt_edit (QtWidgets.QTextEdit)

        Install self on <txt_edit>'s viewport and create an overlay widget on
        which will be painted the fake multi-cursors.
        """

        self.txt_edit = txt_edit
        viewport = txt_edit.viewport()
        cursor = txt_edit.textCursor()
        self.txt_edit.setTextCursor(cursor)

        # install the event
        viewport.installEventFilter(self)

        # store txt_edit's QTextCursor and a copy of it that will be used to
        # actually perform the text edits
        self.cursors = [cursor]
        self.multi_cursor = QtGui.QTextCursor(cursor)   # creates a copy

        # create the overlay widget (passes all mouse event)
        overlay = QtWidgets.QWidget(txt_edit)
        overlay.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        self.overlay = overlay
        overlay.show()

        # set overlay's size and position to cover entirely the QTextEdit's viewport
        overlay.resize(kk.INF_WIDTH, kk.INF_HEIGHT)
        overlay.move(viewport.pos())

        # set overlay's paintEvent
        overlay.paintEvent = self.paint_event
        txt_edit.destroyed.connect(self.destroy_on_close)

    def destroy_on_close(self):
        """ Make sure self is destroyed with QTextEdit """
        self.deleteLater()

    def get_line_length_width(self):
        """
        Returns:
            (int)

        Get lines "max-length" width value.
        """

        test_string = '_'*self.line_max_length
        font = self.txt_edit.font()
        metrics = QtGui.QFontMetrics(font)
        return metrics.boundingRect(test_string).width()

    def cursors_color(self):
        return QtGui.QColor(*self.cursor_colors[self.cursor_state])

    def paint_event(self, event):
        """
        (overwrites self.overlay's paintEvent)

        Paint multi-cursors on self.overlay (over the actual cursor).
        """

        painter = QtGui.QPainter(self.overlay)

        # paint "max-length" vertical bar
        painter.setPen(QtGui.QColor(207, 228, 255, 20))
        x = self.get_line_length_width()
        painter.drawLine(x, 0, x, kk.INF_HEIGHT)

        painter.setPen(QtCore.Qt.NoPen)

        if len(self.cursors) > 1:
            for cursor in self.cursors:
                painter.setBrush(QtGui.QColor(*self.cursor_colors[self.cursor_state]))
                try:
                    rect = self.txt_edit.cursorRect(cursor)
                    painter.drawRect(
                        rect.x() +kk.LEFT_PADDING,
                        rect.y(),
                        rect.width(),
                        rect.height()
                    )

                except:
                    pass

        rect = self.txt_edit.cursorRect(self.cursors[-1])
        painter.setBrush(QtGui.QColor(207, 228, 255, 10))
        painter.drawRect(
            0,
            rect.y(),
            kk.INF_WIDTH,
            rect.height()
        )

    def update_cursors(self, cursors=None):
        """
        Args:
            cursors (list[QtGui.QTextCursor], optional)

        Repaint all cursors regions (with offset).
        """

        offset = 5
        cursors = cursors if cursors else self.cursors

        for cursor in cursors or ():
            rect = self.txt_edit.cursorRect(cursor)

            rect = QtCore.QRect(
                0,
                rect.y() -offset,
                kk.INF_WIDTH,
                rect.height() +offset*2
            )

            self.overlay.repaint(rect)

    def blink_cursors(self):
        """
        Toggle self.cursor_state and trigger repaint() on cursors (cursors color
        will be toggled as well).
        """

        self.cursor_state = not self.cursor_state
        self.update_cursors()


class MultiCursor(QtGui.QTextCursor):
    """
    QtGui.QTextCursor re-implementation that allows multi-editing.
    """

    def __init__(self, cursors, txt_edit):
        super(MultiCursor, self).__init__(cursors[-1])

        self.cursors = cursors
        self.txt_edit = txt_edit

    def embrace_text_with(self, open_char, close_char):
        """
        Args:
            open_char (str)
            close_char (str)

        Returns:
            (bool) : True

        Add <open_char> and <close_char> characters before and after selection.
        The return value will be propagated to eventFilter's.
        """

        self.beginEditBlock()

        for cursor in self.cursors:
            sel = cursor.selection().toPlainText()

            if sel:
                sel_start, sel_end, is_reversed = self.get_sel_start_end_reverse(cursor)
                cursor.insertText('{}{}{}'.format(open_char, sel, close_char))

                # offset the selection, due to the adding of a character before
                self.restore_selection(cursor, sel_start +1, sel_end +1, is_reversed)

            else:
                if not self.char_is_next(open_char, cursor):
                    cursor.insertText('{}{}'.format(open_char, close_char))
                    cursor.setPosition(cursor.position() -1, cursor.MoveAnchor)
                    self.txt_edit.setTextCursor(cursor)

        self.endEditBlock()

        return True

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

    def ignore_if_next(self, char):
        """
        Args:
            char (str)

        Returns:
            (bool) : True

        For each cursor, move the cursor forward if next character is the same as
        the input <char>, else insert it.
        """

        self.beginEditBlock()

        for cursor in self.cursors:
            if not self.char_is_next(char, cursor):
                cursor.insertText(char)

        self.endEditBlock()

        return True

    def char_is_next(self, char, cursor):
        """
        Args:
            char (str)

        Returns:
            (bool)

        Move the cursor forward if next character (from <cursor>) is the same as
        the input <char>.
        """

        line = cursor.block().text()
        pos = cursor.positionInBlock()

        if len(line) > pos and line[pos] == char:
            cursor.setPosition(cursor.position() +1, self.MoveAnchor)
            self.txt_edit.setTextCursor(cursor)
            return True

        return False

    def unindent(self):
        """
        Un-indent all cursors selections.
        """

        self.beginEditBlock()

        for cursor in self.cursors:
            sel_start, sel_end, _ = self.get_sel_start_end_reverse(cursor)

            # retrieve start/end blocks to get the iteration range
            cursor.setPosition(sel_end, cursor.MoveAnchor)
            end_block = cursor.blockNumber()
            # also go to the firstiteration line
            cursor.setPosition(sel_start, cursor.MoveAnchor)
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

        self.endEditBlock()

    def restore_selection(self, cursor, start, end, is_reversed):
        """
        Args:
            cursor (QtGui.QTextCursor)
            start (int)
            end (int)
            is_reversed (bool) : whether the user selected from <end> to <start> or not

        Restore user's selection after manipulations.
        """

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
        self.txt_edit.setTextCursor(cursor)

    def toggle_block_comment(self, char):
        """
        Args:
            char (str)

        (called on Ctrl +/)

        For all cursors, toggle comments on selected block.
        """

        self.beginEditBlock()

        for cursor in self.cursors:
            # get current selected text and positions
            sel_start, sel_end, is_reversed = self.get_sel_start_end_reverse(cursor)
            text = self.get_selected_lines(cursor, sel_start, sel_end)

            pos, number = self.get_block_min_indent(text)
            if pos is None:
                return

            # extend selection to whole lines.
            cursor.setPosition(sel_start, cursor.MoveAnchor)
            cursor.movePosition(cursor.StartOfLine, cursor.MoveAnchor)
            cursor.setPosition(sel_end, cursor.KeepAnchor)
            cursor.movePosition(cursor.EndOfLine, cursor.KeepAnchor)

            # replace lines with comment-toggled ones
            new_text, inserted = self.comment_toggled_text(text, pos, char)
            cursor.insertText(new_text)

            # restore selection
            if inserted:
                sel_start += len(char)
                sel_end += len(char)*number
            else:
                sel_start -= len(char)
                sel_end -= len(char)*number

            self.restore_selection(cursor, sel_start, sel_end, is_reversed)

        self.endEditBlock()

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

    def comment_toggled_text(self, text, pos, char):
        """
        Args:
            text (str)
            pos (int)
            char (str)

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
                if not line[pos:pos+len(char)] == char:
                    insert = True
                    break

        if insert:
            for line in lines:
                # insert '# ' at pos if line is not empty
                if not self.is_empty(line) and len(line) > pos:
                    new_lines.append(
                        line[:pos] +char +line[pos:]
                    )
                else:
                    new_lines.append(line)

        else:
            for line in lines:
                # remove '# ' at pos if line is not empty
                if not self.is_empty(line) and len(line) > pos:
                    new_lines.append(
                        line[:pos] +line[pos+len(char):]
                    )
                else:
                    new_lines.append(line)

        return '\n'.join(new_lines), insert

    def is_empty(self, line):
        """
        Args:
            line (str)

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

    def get_selected_lines(self, cursor, start, end, pos_in_block=False):
        """
        Args:
            cursor (QtGui.QTextCursor)
            start (int)
            end (int)
            pos_in_block (bool, optional)

        Returns:
            (str)

        Get lines froms selection :

            - if no selection, return the content of the line with cursor on it
            - if some text is selected, extend the returned text to the start of
              the first line and the end of the last line.

            - if <pos_in_block> : return start/end positions in block
        """

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

        if pos_in_block:
            return (
                cursor.selectedText().replace(u'\u2029', '\n'),
                start_in_block,
                end_in_block
            )

        return cursor.selectedText().replace(u'\u2029', '\n')

    def handle_backspace(self):
        """
        Returns:
            (bool) : True

        Handle backspace on identation or open/close chars as parenthesis, brackets,
        string quotes, etc.
        """

        self.beginEditBlock()

        for cursor in self.cursors:
            if self.indent_backspace(cursor):
                continue
            if self.remove_open_close_chars(cursor):
                continue
            cursor.deletePreviousChar()

        self.endEditBlock()

        return True

    def remove_open_close_chars(self, cursor):
        """
        Args:
            cursor (QtGui.QTextCursor)

        Returns:
            (bool)

        If <cursor>'s previous character is an opening one, remove aslo the next
        one if is a closing one.
        """

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

    def indent_backspace(self, cursor):
        """
        Args:
            cursor (QtGui.QTextCursor)

        Returns:
            (bool)

        Handle indentation on backspace :

            - remove the four last characters if they are all white space characters,
              and current cursor position is at n*4 from the start of the line.
        """

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

    def move_lines(self, direction):
        """
        Args:
            direction (str) : 'up' or 'down'

        Returns:
            (bool)

        Move up/down selected lines on up/down keys.
        """

        if not direction in ['up', 'down']:
            return False

        self.beginEditBlock()

        for cursor in self.cursors:
            sel_start, sel_end, is_reversed = self.get_sel_start_end_reverse(cursor)

            # get selected lines text, and start/end positions in block (will be used
            # to re-create selection after moving current lines)
            text, start_in_block, end_in_block = self.get_selected_lines(
                cursor,
                sel_start,
                sel_end,
                pos_in_block=True
            )

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
                    cursor,
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
                    cursor,
                    line_start +start_in_block,
                    line_end +end_in_block,
                    is_reversed
                )

        self.endEditBlock()

        return True

    def duplicate_lines(self):
        """
        (called on Ctrl+Shift+D)

        Duplicate selected lines, or the line with the cursor on if no selection.
        """

        blocks = []
        to_be_edited = []

        for cursor in self.cursors:
            block = cursor.block()
            if not block in blocks:
                blocks.append(block)
                to_be_edited.append(True)
            else:
                to_be_edited.append(False)

        self.beginEditBlock()

        for i, cursor in enumerate(self.cursors):
            if not to_be_edited[i]:
                continue

            sel_start, sel_end, is_reversed = self.get_sel_start_end_reverse(cursor)
            text = self.get_selected_lines(cursor, sel_start, sel_end)

            # go at the end of the selected lines and insert the selected lines below
            cursor.setPosition(sel_end, cursor.MoveAnchor)
            cursor.movePosition(cursor.EndOfLine, cursor.MoveAnchor)
            cursor.insertText('\n' +text)

            self.restore_selection(cursor, sel_start, sel_end, is_reversed)

        self.endEditBlock()

    def exec_on_cursors(self, func, *args, **kwargs):
        """
        Run <func> on each cursor, grouping all these actions under a single
        edit block (single undo/redo chunk).
        """

        self.beginEditBlock()

        for cursor in self.cursors:
            if cursor.hasSelection():
                # set the same selection
                self.setPosition(cursor.selectionStart(), self.MoveAnchor)
                self.setPosition(cursor.selectionEnd(), self.KeepAnchor)
            else:
                # move cursor at the same position
                self.setPosition(cursor.position(), self.MoveAnchor)

            # run
            func(cursor, *args, **kwargs)

        self.endEditBlock()

    def get_move_operation_from_key(self, key, by_word=False):
        if key == QtCore.Qt.Key_Right:
            if by_word:
                return QtGui.QTextCursor.NextWord
            else:
                return QtGui.QTextCursor.NextCharacter

        elif key == QtCore.Qt.Key_Left:
            if by_word:
                return QtGui.QTextCursor.PreviousWord
            else:
                return QtGui.QTextCursor.PreviousCharacter

        elif key == QtCore.Qt.Key_Home:
            return QtGui.QTextCursor.StartOfBlock

        elif key == QtCore.Qt.Key_End:
            return QtGui.QTextCursor.EndOfBlock

        elif key == QtCore.Qt.Key_Down:
            return QtGui.QTextCursor.Down

        elif key == QtCore.Qt.Key_Up:
            return QtGui.QTextCursor.Up


    def extend_selections(self, key, by_word=False):
        """
        Args:
            key (QtCore.Qt.Key)
            by_word (bool, optional)

        Edit all cursors selection on move keys.
        """

        operation = self.get_move_operation_from_key(key, by_word=by_word)
        self.multi_movePosition(operation, self.KeepAnchor)

    def multi_movePosition(self, operation, mode, n=1):
        """
        Args:
            operation (QtGui.QTextCursor.MoveOperation)
            mode (QtGui.QTextCursor.MoveMode)
            n (int)

        Specific "Qt re-implementation" for multi-movePosition, as already used
        within self.exec_on_cursors (would run infinite loop).
        """

        for cursor in self.cursors:
            # specific case on start-of-line : first go to the start of the line
            # indentation, then if pressed again, go to the start of the line.
            if operation == QtGui.QTextCursor.StartOfBlock:
                pos = cursor.positionInBlock()
                line = cursor.block().text()
                if not pos:
                    continue

                whitespace_match = re.match('\s+', line[:pos])

                # all previous characters are whitespaces, go the start of the line
                if whitespace_match and len(whitespace_match.group(0)) == pos:
                    cursor.movePosition(QtGui.QTextCursor.StartOfBlock, mode, n)

                else:
                    # line has indentation, go to the start of the line, then to
                    # the start of the first word in line
                    if whitespace_match:
                        cursor.movePosition(QtGui.QTextCursor.StartOfBlock, mode, n)
                        cursor.movePosition(QtGui.QTextCursor.NextWord, mode, n)
                    else:
                        # line has no indentation, go to the start of the line
                        cursor.movePosition(QtGui.QTextCursor.StartOfBlock, mode, n)

            else:
                cursor.movePosition(operation, mode, n)

            # triggers the cursor's new area to be repainted, and makes sure the
            # last cursor of the loop is set on the QTextEdit
            self.txt_edit.setTextCursor(cursor)

    #################################################################
    #                    Qt re-implementations                      #
    #################################################################

    def deleteChar(self):
        self.exec_on_cursors(QtGui.QTextCursor.deleteChar)

    def deletePreviousChar(self):
        self.exec_on_cursors(QtGui.QTextCursor.deletePreviousChar)

    def insertBlock(self, *args, **kwargs):
        self.exec_on_cursors(QtGui.QTextCursor.insertBlock, *args, **kwargs)

    def insertFragment(self, *args, **kwargs):
        self.exec_on_cursors(QtGui.QTextCursor.insertFragment, *args, **kwargs)

    def insertFrame(self, *args, **kwargs):
        self.exec_on_cursors(QtGui.QTextCursor.insertFrame, *args, **kwargs)

    def insertHtml(self, *args, **kwargs):
        self.exec_on_cursors(QtGui.QTextCursor.insertHtml, *args, **kwargs)

    def insertImage(self, *args, **kwargs):
        self.exec_on_cursors(QtGui.QTextCursor.insertImage, *args, **kwargs)

    def insertList(self, *args, **kwargs):
        self.exec_on_cursors(QtGui.QTextCursor.insertList, *args, **kwargs)

    def insertTable(self, *args, **kwargs):
        self.exec_on_cursors(QtGui.QTextCursor.insertTable, *args, **kwargs)

    def insertText(self, *args, **kwargs):
        self.exec_on_cursors(QtGui.QTextCursor.insertText, *args, **kwargs)

    def removeSelectedText(self, *args, **kwargs):
        self.exec_on_cursors(QtGui.QTextCursor.removeSelectedText, *args, **kwargs)
