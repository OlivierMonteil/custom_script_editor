###############################################################################
#           Script for customizing Maya's script editor hightlights.
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

        # add class arguments rule
        rules += [('(\\bclass\\b\s+)(\w+\s*\()([^\)]+)', 3, self.styles['classArg'])]

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
