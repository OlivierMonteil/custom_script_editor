###############################################################################
#       Script for customizing Maya's script editor hightlights and hotkeys.
###############################################################################

__author__ = 'Olivier Monteil'
__version__ = 1.1
__ide_version__ = 'Atom'

import sys
import re

try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide import QtGui, QtCore
    from PySide import QtGui as QtWidgets

try:
    import maya.cmds as MC
    import maya.mel as mel
    import maya.OpenMayaUI as OMUI
except:
    pass

try:
    import shiboken2 as shiboken
except ImportError:
    import shiboken

TRIPLE_QUOTES = ["'''", '"""']
TRIPLE_STATES = [2, 3]
SINGLE_QUOTES = ["'", '"']
SINGLE_STATES = [0, 1]

#------------------------------------------------------------------------------

def char_format(rgb, style=''):
    # return a QtGui.QTextCharFormat with the given attributes (color, font weigth...etc)

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

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class PythonHighlighter (QtGui.QSyntaxHighlighter):
    """
    Syntax highlighter for the Python language (colors from Atom editor).
    """

    # python keywords
    keywords = ['and', 'as', 'assert', 'async', 'await', 'break', 'class',
                'continue', 'def', 'del', 'elif', 'else', 'except', 'finally',
                'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
                'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try',
                'while', 'with', 'yield']

    builtins_words = ['ArithmeticError', 'AssertionError', 'AttributeError',
                     'BaseException', 'BlockingIOError', 'BrokenPipeError',
                     'BufferError', 'BytesWarning', 'ChildProcessError',
                     'ConnectionAbortedError', 'ConnectionError',
                     'ConnectionRefusedError', 'ConnectionResetError',
                     'DeprecationWarning', 'EOFError', 'Ellipsis',
                     'EnvironmentError', 'Exception', 'FileExistsError',
                     'FileNotFoundError', 'FloatingPointError', 'FutureWarning',
                     'GeneratorExit', 'IOError', 'ImportError', 'ImportWarning',
                     'IndentationError', 'IndexError', 'InterruptedError',
                     'IsADirectoryError', 'KeyError', 'KeyboardInterrupt',
                     'LookupError', 'MemoryError', 'ModuleNotFoundError',
                     'NameError', 'NotADirectoryError', 'NotImplemented',
                     'NotImplementedError', 'OSError', 'OverflowError',
                     'PendingDeprecationWarning', 'PermissionError',
                     'ProcessLookupError', 'RecursionError', 'ReferenceError',
                     'ResourceWarning', 'RuntimeError', 'RuntimeWarning',
                     'StopAsyncIteration', 'StopIteration', 'SyntaxError',
                     'SyntaxWarning', 'SystemError', 'SystemExit', 'TabError',
                     'TimeoutError', 'TypeError', 'UnboundLocalError',
                     'UnicodeDecodeError', 'UnicodeEncodeError', 'UnicodeError',
                     'UnicodeTranslateError', 'UnicodeWarning', 'UserWarning',
                     'ValueError', 'Warning', 'WindowsError', 'ZeroDivisionError',
                     '__build_class__', '__debug__', '__doc__', '__import__',
                     '__loader__', '__name__', '__package__', '__spec__', 'abs',
                     'all', 'any', 'ascii', 'bin', 'bool', 'breakpoint', 'bytearray',
                     'bytes', 'callable', 'chr', 'classmethod', 'compile', 'complex',
                     'copyright', 'credits', 'delattr', 'dict', 'dir', 'divmod',
                     'enumerate', 'eval', 'exec', 'exit', 'filter', 'float',
                     'format', 'frozenset', 'getattr', 'globals', 'hasattr',
                     'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance',
                     'issubclass', 'iter', 'len', 'license', 'list', 'locals',
                     'map', 'max', 'memoryview', 'min', 'next', 'object', 'oct',
                     'open', 'ord', 'pow', 'print', 'property', 'qApp', 'quit',
                     'range', 'repr', 'reversed', 'round', 'set', 'setattr', 'slice',
                     'sorted', 'staticmethod', 'str', 'sum', 'super', 'tuple', 'type',
                     'vars', 'zip']


    numbers = ['None', 'True', 'False']

    # python operators
    operators = ['=', '==', '!=', '<', '<=', '>', '>=', '\+', '-', '\*', '/',
                 '//', '\%', '\*\*', '\+=', '-=', '\*=', '/=', '\%=', '\^',
                 '\|', '\&', '\~', '>>', '<<']

    # syntax styles
    styles = {'keyword': char_format((200, 116, 220)),
              'normal': char_format((170, 176, 190)),
              'operator': char_format((200, 116, 220)),
              'defclass': char_format((200, 116, 220)),
              'called': char_format((92, 166, 237)),
              'defName': char_format((92, 166, 237), 'bold'),
              'className': char_format((228, 187, 106), 'bold'),
              'classArg': char_format((228, 187, 106)),
              'string': char_format((147, 195, 121)),
              'comments': char_format((90, 99, 111), 'italic'),
              'interm': char_format((224, 109, 116)),
              'special': char_format((87, 180, 193)),
              'numbers': char_format((207, 154, 102))}

    #--------------------------------------------------------------------------
    def __init__(self, document):
        super(PythonHighlighter, self).__init__(document)

        self.rules = self.set_rules()

    #--------------------------------------------------------------------------
    def set_rules(self):
        """
        Set all syntax rules, except for comments, strings and triple-quotes,
        that will be handled differently.
        """

        # digits rule
        rules = [('\\b\d+\\b', 0, self.styles['numbers'])]

        # add def arguments rule
        rules += [('(\\bdef\\b\s+)(\w+\s*\()([^\)]+)', 3, self.styles['numbers'])]
        # add class arguments rule
        rules += [('(\\bclass\\b\s+)(\w+\s*\()([^\)]+)', 3, self.styles['classArg'])]

        # (moved downwards to override 'or ()' called-style, lets see if no other
        # issue will append...)
        """
        # add python keywords rules
        rules += [('\\b(%s)\\b' % w, 0, self.styles['keyword']) for w in self.keywords]
        """

        # add operators rules
        rules += [('%s' % o, 0, self.styles['operator']) for o in self.operators]

        rules += [
                     # intermediates rule
                     ('(\.)(\w+)', 2, self.styles['interm']),
                     # called functions rule
                     ('(\\b_*\w+_*\s*)(\()', 1, self.styles['called']),
                     # declared functions rule
                     ('(\\bdef\\b\s*)(_*\w+_*)', 2, self.styles['defName']),
                     # declared classes rule
                     ('(\\bclass\\b\s*)(_*\w+_*)', 2, self.styles['className'])
                 ]

        # add python keywords rules
        rules += [('\\b(%s)\\b' % w, 0, self.styles['keyword']) for w in self.keywords]

        # add python "special" keywords rules
        rules += [('\\b%s\\b' % x, 0, self.styles['special'])
                  for x in self.builtins_words]

        rules += [
                     # kwargs first part rule
                     ('(,\s*|\()(\w+)(\s*=\s*)', 2, self.styles['numbers'])
                 ]

        # add numbers rule (called after intermediates sur float would not
        # be considered as intermediates)
        rules += [('\\b(%s)\\b' % n, 0, self.styles['numbers']) for n in self.numbers]

        rules += [
                    # set '.' on float back to numbers style
                    ('\d+\.*\d+', 0, self.styles['numbers']),
                    # set ',' back to normal
                    (',', 0, self.styles['normal']),
                 ]

        # add decorators rule
        rules += [('\@.+', 0, self.styles['called'])]

        return [(QtCore.QRegExp(pat), index, fmt) for (pat, index, fmt) in rules]
    #--------------------------------------------------------------------------
    def highlightBlock(self, line):
        """
        Apply syntax highlighting to the given block of line (re-implementation,
        automatically called by Qt).
        """

        try:
            for pattern, nth, format in self.rules:
                expression = QtCore.QRegExp(pattern)
                index = expression.indexIn(line, 0)

                while index >= 0:
                    # we want the index of the nth match
                    index = expression.pos(nth)
                    length = len(expression.cap(nth))
                    # set segment format
                    self.setFormat(index, length, format)
                    index = expression.indexIn(line, index + length)

            self.apply_strings_and_comments_style(line)

        except Exception as e:
            return
            print (e)
    #--------------------------------------------------------------------------
    def apply_strings_and_comments_style(self, line):
        """
        Apply single or triple quotes, and comments highlight on line.
        """

        # propagate previous line's state
        self.setCurrentBlockState(self.previousBlockState())

        offset = 99999999999
        start = 0
        pos = 0

        delim_strings = TRIPLE_QUOTES +SINGLE_QUOTES +['#']

        while len(line) > pos > -1:
            # get current delimiter
            state = self.currentBlockState()
            delim_str = delim_strings[state] if state > -1 else None

            # if no current delimiter, get the next delimiter in line
            if not delim_str:
                positions = [QtCore.QRegExp(x).indexIn(line, pos) for x in delim_strings]

                # no more delimiter in line
                if not any(x != -1 for x in positions):
                    break

                positions = [x +offset if x == -1 else x for x in positions]
                pos = min(positions)

                # if found delimiter is escaped, search again
                if self.is_escaped(line, pos):
                    pos +=1
                    continue

                # "open" current state and delimiter
                state = positions.index(pos)
                self.setCurrentBlockState(state)
                delim_str = delim_strings[state]

                if state == 4:      # comments, paint until the end of the line
                    self.setFormat(pos, len(line) -pos, self.styles['comments'])
                    self.setCurrentBlockState(-1)
                    return          # there's no need for further analysis in this line

                else:
                    # "open" str (set painting start position)
                    start = pos
                    pos += len(delim_str)

            # else, search for the next occurence of the current delimiter in line
            else:
                next_pos = QtCore.QRegExp(delim_str).indexIn(line, pos)

                # not found
                if next_pos == -1:
                    # check for comments after a \-propagated string
                    comment_pos = QtCore.QRegExp('#').indexIn(line, pos)
                    # comments found
                    if comment_pos and self.currentBlockState() in [2, 3]:
                        # last character before was a non-escaped \
                        if self.last_util_char(line, comment_pos) == '\\':
                            self.paint_string(start, comment_pos-1 -start, line)
                            self.setFormat(comment_pos, len(line) -comment_pos, self.styles['comments'])
                            return
                    break

                # closing char is escaped
                if self.is_escaped(line, next_pos):
                    self.paint_string(start, next_pos -start, line)
                    pos = next_pos +1
                    continue

                # "close" and paint string
                self.paint_string(start, next_pos +len(delim_str) -start -1, line)
                self.setCurrentBlockState(-1)
                pos = next_pos +len(delim_str)

        # ------ after iterations (current state may still be "opened") -------

        if self.currentBlockState() == -1:
            return

        # comments (those after \ string-propagation are handled higher)
        elif self.currentBlockState() == 4:
            self.setFormat(start, len(line) -start, self.styles['comments'])
            self.setCurrentBlockState(-1)

        elif self.currentBlockState() in [2, 3]:
            # no string-propagation
            if line[-1] != '\\':
                self.setCurrentBlockState(-1)
            else:
                self.paint_string(start, len(line) -start, line)
                self.setFormat(len(line)-1, 1, self.styles['special'])
        # triple-quotes
        else:
            self.paint_string(start, len(line) -start, line)
    #--------------------------------------------------------------------------
    def last_util_char(self, line, pos):
        """
        Perform backward-lookup from <pos> in line for the first non-whitespace
        character.
        Return None if this character is escaped.
        """

        line = line[:pos]

        while line:
            if not re.match('\s', line[-1]):
                # return None if char is escaped
                if self.is_escaped(line, len(line)-1):
                    return

                return line[-1]

            line = line[:-1]
    #--------------------------------------------------------------------------
    def is_escaped(self, line, pos):
        """ Check the escaped state of the character at <pos> in <line>. """

        escaped = False

        while pos:
            if line[pos-1] == '\\':
                escaped = not escaped
                pos -= 1
            else:
                break

        return escaped
    #--------------------------------------------------------------------------
    def paint_string(self, start, count, line):
        """
        Inputs :
            <start>         int (string start pos in <line>)
            <count>         int (number of character to paint)
            <line>          str

        Return value:
            None

        Set each charcater's style from start to end, checking if it is escaped
        or not.
        """

        for i in range(start, start +count +1):
            # skip whitespaces, as they don't need to be painted, and must be
            # considered as escaped characters for "special" style painting.
            if re.match('\s', line[i]):
                continue

            if not self.is_escaped(line, i):
                self.setFormat(i, 1, self.styles['string'])
            else:
                self.setFormat(i-1, 2, self.styles['special'])

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

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class ScriptEditorDetector(QtCore.QObject):

    """
    Custom eventFilter installed on Maya's main window that will re-set highlight
    and connections on Script Editor (with evalDeferred).
    """

    def __init__(self, parent=None):
        super(ScriptEditorDetector, self).__init__(parent)

    #--------------------------------------------------------------------------
    def eventFilter(self, obj, event):
        # (no need to run set_customize_on_tab_change and customize_script_editor
        # if the Script Editor is already opened)
        if not script_editor_opened():
            if event.type() == QtCore.QEvent.ChildAdded:
                if event.child().isWidgetType():
                    # defer set_customize_on_tab_change and customize_script_editor to make sure
                    # Script Editor's window is fully created first
                    MC.evalDeferred(set_customize_on_tab_change, lowestPriority=True)
                    MC.evalDeferred(customize_script_editor, lowestPriority=True)

        return False

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class SnippetsHandler(QtCore.QObject):

    """
    Custom eventFilter installed on Maya's Script Editor to handle snippets.
    """

    customWords = ['sys.exit(app.exec_())', 'setContentsMargins']

    def __init__(self, textEdit, formLay):
        super(SnippetsHandler, self).__init__(textEdit)

        self.textEdit = textEdit
        self.snippetBox = self.getSnippetBox(formLay)
        self.triggerOnCursorChange = True
        self.textEdit.cursorPositionChanged.connect(self.onCursorChange)
        self.box = None

    #--------------------------------------------------------------------------
    def getSnippetBox(self, formLay):
        # get 'Snippets' menu's chechbox

        scriptEditorPopupMenus = mel.eval("$toto = $gCommandPopupMenus;")

        toto = [menu for menu in scriptEditorPopupMenus if formLay in menu]
        popupMenu = [menu for menu in scriptEditorPopupMenus if formLay in menu][0]
        return popupMenu +'|CustomMenu|SnippetBox'
    #--------------------------------------------------------------------------
    def snippetsEnabled(self):
        # MC.menuItem(self.snippetBox, q=True, checkBox=True) seems to fail
        # (when menuItem is not visible?), so we have to get menuItem as QAction
        # to get the right result!
        ptr = OMUI.MQtUtil.findMenuItem(self.snippetBox)
        qtBox = shiboken.wrapInstance(long(ptr), QtWidgets.QAction)
        return qtBox.isChecked()
    #--------------------------------------------------------------------------
    def eventFilter(self, obj, event):
        # close snippet box on RMB and MMB
        # (LMB seems to be handled directly into QTextCursor class)
        try:
            if event.button() and self.box:
                self.killBox()
        except:
            pass

        # handle snippet box on key press events
        if event.type() == event.KeyPress and self.snippetsEnabled():
            self.triggerOnCursorChange = False
            # get QtextEdit cursor
            cursor = self.textEdit.textCursor()

            if self.box:
                # validate snippet if "Return" is pressed
                if event.key() == QtCore.Qt.Key_Return:
                    self.validateSnippet(self.box.currentItem().text())
                    return True

                # step down into snippet box if possible on down key
                if event.key() == QtCore.Qt.Key_Down:
                    self.box.goDown()
                    return True
                # step up into snippet box if possible on up key
                if event.key() == QtCore.Qt.Key_Up:
                    self.box.goUp()
                    return True

                # close snippet box (will be reconstructed later if necessary)
                self.killBox()

            # get key
            toLower = True
            if event.modifiers():
                if event.modifiers() == QtCore.Qt.ShiftModifier:
                    toLower = False
                else:
                    return False

            keyAsStr = QtGui.QKeySequence(event.key()).toString()
            keyAsStr = keyAsStr.lower() if toLower else keyAsStr

            # skip if key as string is more than one character (ex: space)
            # except for Backspace, so the snippets would still be triggered
            if keyAsStr.lower() != 'backspace' and len(keyAsStr) > 1:
                return False

            cursor = self.textEdit.textCursor()
            line = cursor.block().text()

            try:
                if re.match('[a-zA-Z_]', keyAsStr) or keyAsStr.lower() in ['.', 'backspace']:      # on alphabetical characters
                    pos = cursor.positionInBlock()
                    if keyAsStr.lower() == 'backspace':
                        pos = min(0, pos -1)
                        keyAsStr = ''

                    snippets = self.getSnippets(line, pos, keyAsStr)

                    # if snippets have been found, show SnippetBox under current word
                    if snippets:
                        rect = self.textEdit.cursorRect()
                        pos = QtCore.QPoint(rect.x() +35, rect.y() +15)

                        self.box = SnippetBox(self.textEdit, snippets, pos)
                        self.box.itemPressed.connect(lambda x: self.validateSnippet(x.text()))
                        self.box.show()

            except Exception as e:
                print (e)
                pass

        return False
    #--------------------------------------------------------------------------
    def validateSnippet(self, text):
        # insert selected completion into QTextEdit and close snippets box

        cursor = self.textEdit.textCursor()
        pos = cursor.position()
        cursor.movePosition(cursor.StartOfWord, cursor.MoveAnchor)
        if cursor.position() == pos:
            cursor.movePosition(cursor.PreviousWord, cursor.MoveAnchor)
        cursor.movePosition(cursor.EndOfWord, cursor.KeepAnchor)
        cursor.insertText(text)
        MC.evalDeferred(self.killBox, lowestPriority=True)
    #--------------------------------------------------------------------------
    def killBox(self):
        if self.box:
            self.box.close()
        self.box = None
    #--------------------------------------------------------------------------
    def getCustomSnippets(self, lineToKey):
        customSnippets = []
        wordToKey = lineToKey.split(' ')[-1]

        # add "Exception" to snippets after except
        customSnippets.extend(self.getExceptionSnippets(lineToKey))
        # add double underscore snippets
        customSnippets.extend(self.getDoubleUnderscoreSnippets(wordToKey))

        if len(wordToKey) > 5:
            for word in self.customWords:
                if word.lower().startswith(wordToKey.lower()):
                    wordToKeyRoot = '.'.join(wordToKey.split('.')[:-1])
                    if '.' in word:
                        customSnippets.append(word[len(wordToKeyRoot) +1:])
                    else:
                        customSnippets.append(word[len(wordToKeyRoot):])

        return customSnippets
    #--------------------------------------------------------------------------
    def getDoubleUnderscoreSnippets(self, wordToKey):
        # propose "Exception" snippet after "except"
        if wordToKey.startswith('_'):
            return ['__main__', '__name__', '__class__', '__init__']

        return []
    #--------------------------------------------------------------------------
    def getExceptionSnippets(self, lineToKey):
        # propose "Exception" snippet after "except"

        wordsBeforeKey = re.findall('\w+\.*\w*', lineToKey)

        if len(wordsBeforeKey) != 2:
            return []

        errors = [x for x in __builtins__ if any(w in x.lower() for w in ['error', 'exception'])]

        return sorted([x +' as' for x in errors]) if wordsBeforeKey[0] == 'except' else []
    #--------------------------------------------------------------------------
    def getSnippets(self, line, i, key):
        wordBeforeKey = ''

        # retrieve current word begining to new character
        for x in reversed(line[:i]):
            if not re.match('[a-zA-Z\.]', x):
                break
            wordBeforeKey = x +wordBeforeKey

        wordToKey = wordBeforeKey.split('.')[-1] +key
        if not wordToKey:         # for instance, on backspace erasing the first
            return None         # character of a word, we don't want all snippets to rise

        try:
            snippets = self.getDirSnippets(wordBeforeKey)

        except:       # == if no dir() snippets
            snippets = self.getStoredSnippets()        # in case of snippets storage into a .json file (not implemented)
            snippets.extend(self.getGlobalSnippets())
            snippets.extend(self.getTextSnippets())

        snippets = sorted(snippets)                   # sort snippets
        snippets = list(set(snippets))                # filter duplicate snippets

        # get snippet words that start with wordToKey (no case match)
        matching = [s for s in snippets if s.lower().startswith(wordToKey.lower()) \
                    and wordToKey.lower() != s.lower()]

        matching.extend(self.getCustomSnippets(line[:i] +key))
        matching.extend(self.getSuperSnippets(line[:i] +key))

        return matching
    #--------------------------------------------------------------------------
    def getSuperSnippets(self, word):
        # get current class and function names on super

        if not word.strip() in 'super':
            return []

        cursor = self.textEdit.textCursor()

        className = self.getPreviousDeclarationName(cursor, 'class')
        defName = self.getPreviousDeclarationName(cursor, 'def')

        shortSuper = 'super({}, self)'.format(className)
        longSuper = 'super({}, self).{}('.format(className, defName)

        toReturn = [shortSuper, longSuper] if className and defName else \
                   [shortSuper] if className and not defName else []

        return toReturn
    #--------------------------------------------------------------------------
    def getPreviousDeclarationName(self, cursor, declStr):
        # get class or def name backwards from current position

        doc = cursor.document()
        searchCursor = doc.find(QtCore.QRegExp(declStr +'\s+(\w+)'),
                                cursor.position(), doc.FindBackward)

        line = searchCursor.block().text()

        return line.split(declStr)[1].split('(')[0].split(':')[0].strip()
    #--------------------------------------------------------------------------
    def getTextSnippets(self):
        # return words from current tab with length > 3
        text = self.textEdit.toPlainText()
        return [x for x in re.findall('[\w]+', text) if len(x) >3]
    #--------------------------------------------------------------------------
    def getStoredSnippets(self):
        # storage into a json file for most used words? (not implemented)
        return []
    #--------------------------------------------------------------------------
    def getGlobalSnippets(self):
        # get "root" modules into maya
        importedModules = [x.split('.')[0] for x in sys.modules]
        return list(set(importedModules))
    #--------------------------------------------------------------------------
    def getDirSnippets(self, word):
        # get dir(currentWord) as snippets ( removing the last '\.\w+' part )
        # if error return empty list so the other snippets methods will be called

        if not word or not '.' in word:
            raise

        cuts = [x for x in word.split('.')[:-1] if x]
        try:
            return dir(eval('.'.join(cuts)))
        except:
            raise
    #--------------------------------------------------------------------------
    def onCursorChange(self):
        # close the snippets box if users clicks into the QTextEdit
        if self.triggerOnCursorChange:
            if self.box:
                self.killBox()

        else:
            self.triggerOnCursorChange = True

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class SnippetBox(QtWidgets.QWidget):

    """
    Custom QWidget with QListWidget that will hold completion words, and arrow keys loop
    (up at row 0 will set selection at the end and reverse)
    """

    itemPressed = QtCore.Signal(QtWidgets.QListWidgetItem)

    def __init__(self, parent, list, pos):
        super(SnippetBox, self).__init__(parent)

        self.setStyleSheet('border : transparent;')

        self.setLayout(QtWidgets.QVBoxLayout())
        self.view = QtWidgets.QListWidget()
        self.layout().addWidget(self.view)

        for word in list:
            self.addItem(word)

        self.move(pos)

        textEditHeight = parent.frameRect().height()
        viewWidth = self.sizeHintForColumn(0) + 2 * self.frameWidth()
        viewHeight = self.sizeHintForRow(0) * self.count() + 2 * self.frameWidth()

        self.setCurrentItem(self.item(0))

        for w in [self, self.layout()]:
            w.setContentsMargins(0, 0, 0, 0)

        self.setMaximumSize(viewWidth +16, viewHeight +2)

        self.view.itemPressed.connect(self.itemPressed.emit)

        #self.wheelEvent = self.parent().wheelEvent

    #--------------------------------------------------------------------------
    def addItem(self, name):
        return self.view.addItem(name)
    #--------------------------------------------------------------------------
    def currentItem(self):
        return self.view.currentItem()
    #--------------------------------------------------------------------------
    def setCurrentItem(self, item):
        return self.view.setCurrentItem(item)
    #--------------------------------------------------------------------------
    def item(self, index):
        return self.view.item(index)
    #--------------------------------------------------------------------------
    def frameWidth(self):
        return self.view.frameWidth()
    #--------------------------------------------------------------------------
    def sizeHintForColumn(self, col):
        return self.view.sizeHintForColumn(col)
    #--------------------------------------------------------------------------
    def sizeHintForRow(self, row):
        return self.view.sizeHintForRow(row)
    #--------------------------------------------------------------------------
    def setCurrentRow(self, row):
        return self.view.setCurrentRow(row)
    #--------------------------------------------------------------------------
    def currentRow(self):
        return self.view.currentRow()
    #--------------------------------------------------------------------------
    def count(self):
        return self.view.count()
    #--------------------------------------------------------------------------
    def goDown(self):
        currRow = self.currentRow()
        if currRow +1 < self.count():
            self.setCurrentRow(currRow +1)
        else:
            self.setCurrentRow(0)
    #--------------------------------------------------------------------------
    def goUp(self):
        currRow = self.currentRow()
        if currRow -1 > 0:
            self.setCurrentRow(currRow -1)
        else:
            self.setCurrentRow(self.count() -1)

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def script_editor_opened():
    return True if getScriptEditor() else False
#------------------------------------------------------------------------------
def getScriptEditor():
    app = QtWidgets.QApplication.instance()
    for widget in app.topLevelWidgets():
        if widget.windowTitle() == 'Script Editor':
            return widget
#------------------------------------------------------------------------------
def set_customize_on_tab_change():
    # connect ScriptEditor > QTabWidget.currentChanged signal to customize_script_editor
    #  --> used to customize all new created tabs, because this signal is
    #      called after each tab creation when the Script Editor automatically
    #      focuses on the new tab

    tabsLay = getScriptsTabLay()
    if not tabsLay:
        return

    ptr = OMUI.MQtUtil.findControl(tabsLay)
    qtLay = shiboken.wrapInstance(long(ptr), QtWidgets.QWidget)

    for child in qtLay.children():
        if child.__class__.__name__ == 'QTabWidget':
            child.currentChanged.connect(customize_script_editor)
            break
#------------------------------------------------------------------------------
def getTextEdits(widget):
    # get all QTextEdit found into widget's children

    found = []
    for child in widget.children() or ():
        if isinstance(child, QtGui.QTextDocument):
            found.append(widget.parent())

        found.extend(getTextEdits(child))

    return found
#------------------------------------------------------------------------------
def getScriptsTabLay():
    # get Script Editor's tabLayout (detected by the presence of "MEL" and "Python" tabs)

    # get scriptEditor panel if exists
    try:
        panels = MC.lsUI(panels=True)
    except:
        return
    scriptEditor = [p for p in panels if 'scriptEditor' in p]
    if not scriptEditor:
        return

    # get all tablayouts that have scriptEditor as parent
    scriptEditorTabs = [lay for lay in MC.lsUI(type='tabLayout') \
                        if scriptEditor[0] in MC.layout(lay, q=True, p=True)]

    # get the tablayout that have only MEL and /or Python tabs
    # (there may be also the 'Quick Help' tablayout)
    for lay in scriptEditorTabs or ():
        tabs = MC.tabLayout(lay, q=True, tabLabel=True)
        if all(x in ['MEL', 'Python'] for x in tabs):
            return lay
#------------------------------------------------------------------------------
def child_class_needed(widget, className):
    # detect whether <className> exists in widget's children or not
    # (used to detect if eventFilters or SynthaxHighlighters or installed on widget)

    for w in widget.children():
        if w.__class__.__name__ == className:
            return False
    return True
#------------------------------------------------------------------------------
def scriptToolsMenu(menu):
    # (called on Custom Menu > Script Tools menu added into addCustomMenus func)

    try:
        pos = QtGui.QCursor().pos()
        from OM_scriptTools import menu
        reload(menu)
        menu.run(pos)
    except Exception as e:
        print (e)
        MC.warning('Could not import OM_scriptTools/menu.py')
#------------------------------------------------------------------------------
def removeMayaHighlight(widget):
    for syntaxHl in widget.findChildren(QtGui.QSyntaxHighlighter):
        syntaxHl.setDocument(None)
        # child.deleteLater()
        # del syntaxHl
#-----------------------------------------------------------------------------
def addCustomMenus():
    scriptEditorPopupMenus = mel.eval("$toto = $gCommandPopupMenus;")

    for menu in scriptEditorPopupMenus:
        if not MC.menu(menu, q=True, exists=True):
            continue

        mainMenu = MC.menuItem('CustomMenu', p=menu, subMenu=True,
                               radialPosition="S", label='Custom Menu')

        MC.menuItem('SnippetBox', p=mainMenu, radialPosition="S",
                                 label='Snippets', checkBox=True)
        MC.menuItem('ScriptTools', p=mainMenu, radialPosition="W",
                                 label='Script Tools', command=lambda *args: scriptToolsMenu(menu))
#------------------------------------------------------------------------------
def customize_script_editor(*args):
    # iterate every tab from ScriptEditor's TabWidget to check if the PythonHighlighter,
    # KeysHandler and SnippetsHandler are to be installed on it

    scriptTab = getScriptsTabLay()
    if not scriptTab:
        return

    # get all ScriptEditor tabs and tab-labels
    labels = MC.tabLayout(scriptTab, q=True, tabLabel=True)
    tabs = MC.tabLayout(scriptTab, q=True, childArray=True)

    for i, formLay in enumerate(tabs) or ():
        # do not apply PythonHighlighter on MEL tabs
        applyPythonHighlight = True if labels[i] == 'Python' else False

        ptr = OMUI.MQtUtil.findControl(formLay)
        widget = shiboken.wrapInstance(long(ptr), QtWidgets.QWidget)
        textEdits = getTextEdits(widget)

        # do not edit "MEL" tabs for now
        if not applyPythonHighlight:
            continue

        for t in textEdits or ():
            try:
                # add PythonHighlighter on QTextEdit if not already added
                if child_class_needed(t, 'PythonHighlighter') and applyPythonHighlight:
                    removeMayaHighlight(t)      # remove maya's default QSyntaxHighlighter
                    # set stylesheet with object name (will not be applied on children)
                    styleBody  = 'QTextEdit#' +t.objectName() +'{\n'
                    styleBody += '    color: rgb(170, 176, 190);\n'
                    styleBody += '    background : rgb(29, 34, 46);\n}'
                    styleBody += '    background : rgb(29, 34, 46);\n}'
                    t.setStyleSheet(styleBody)
                    highlight = PythonHighlighter(t)

                # install KeysHandler filterEvent on QTextEdit if not already installed
                if child_class_needed(t, 'KeysHandler'):
                    keyHandle = KeysHandler(parent=t)
                    t.installEventFilter(keyHandle)

                # install KeysHandler filterEvent on QTextEdit if not already installed
                if child_class_needed(t, 'SnippetsHandler'):
                    snippetsHandle = SnippetsHandler(t, formLay)
                    t.installEventFilter(snippetsHandle)

            except Exception as e:
                print (e)

    addCustomMenus()

#------------------------------------------------------------------------------

def run():
    """
    (called by maya's userSetup.mel/py)

    Install event filter on Maya's main window to automate Script Editor
    customization.
    """

    maya_ui = OMUI.MQtUtil.mainWindow()
    maya_ui_qt = shiboken.wrapInstance(long(maya_ui), QtWidgets.QWidget)

    # install ScriptEditorDetector event filter on Maya window if not already
    if child_class_needed(maya_ui_qt, 'ScriptEditorDetector'):
        ui_filter = ScriptEditorDetector(parent=maya_ui_qt)
        maya_ui_qt.installEventFilter(ui_filter)

    # customize Script Editor if already opened and connect ScriptEditor > QTabWidget.currentChanged
    # signal to customize_script_editor. This will allow to customize all new created tabs,
    # because this signal is called after each tab creation when the Script Editor
    # automatically focuses on the new tab
    if script_editor_opened():
        customize_script_editor()
        set_customize_on_tab_change()

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class TestWindow(QtWidgets.QMainWindow):
    def __init__(self, parent):
        super(TestWindow, self).__init__()

        self.setCentralWidget(QtWidgets.QWidget())
        lay = QtWidgets.QVBoxLayout(self.centralWidget())

        self.field = QtWidgets.QTextEdit()
        self.field.setObjectName('TESTFIELD')

        lay.addWidget(self.field)

        self.set_highlight()

        self.resize(500, 600)

    def set_highlight(self):
        import custom_script_editor
        import importlib

        importlib.reload(custom_script_editor)
        custom_script_editor.removeMayaHighlight(self.field)

        styleBody  = 'QTextEdit#' +self.field.objectName() +'{\n'
        styleBody += '    color: rgb(170, 176, 190);\n'
        styleBody += '    background : rgb(29, 34, 46);\n}'
        styleBody += '    background : rgb(29, 34, 46);\n}'
        self.field.setStyleSheet(styleBody)
        highlight = custom_script_editor.PythonHighlighter(self.field)

        keyHandle = KeysHandler(parent=self.field)
        self.field.installEventFilter(keyHandle)

#------------------------------------------------------------------------------

def test(parent=None):
    import sys

    try:
        app = QtWidgets.QApplication(sys.argv)

        window = TestWindow(parent)
        window.show()

        sys.exit(app.exec_())
    except:
        window = TestWindow(parent)
        window.show()

    return window

#------------------------------------------------------------------------------

if __name__ == '__main__':
    test()
