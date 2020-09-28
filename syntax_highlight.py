"""
Script for customizing Maya's script editor hightlights.
"""

import os
import re

import traceback
import datetime

try:
    from PySide2 import QtCore, QtGui
except ImportError:
    from PySide import QtGui, QtCore

from custom_script_editor import constants as kk
from custom_script_editor import palette


BASE_MESSAGES = ['warning', 'success', 'info', 'error']


class CustomHighlighter(QtGui.QSyntaxHighlighter):

    def __init__(self, text_edit):
        """
        Args:
            text_edit (QTextEdit)
        """

        self.text_edit = text_edit

        # Seems that setting CustomHighlighter's parent is not enough to avoid  
        # the garbage collector, so we will add it to its parent attributes
        text_edit.custom_highlighter = self

        QtGui.QSyntaxHighlighter.__init__(self, text_edit)

    def highlightBlock(self, line):
        """
        Args:
            line (str)

        Qt re-implementation. Apply syntax highlighting to the given line.
        """

        # For unknown reeason, the LogHighlighter may loose its attributes at one
        # time... In this case, just re-intitiate its rules and palettes.
        if not hasattr(self, 'rule'):
            self.init_rule()

        self.rule.apply(line)

    def set_theme(self, theme):
        self.palette.apply_theme(self.text_edit, theme)
        self.update_rule()

    def update_rule(self):
        self.rule.update()
        self.rehighlight()



class LogHighlighter(CustomHighlighter):
    """
    Syntax highlighter for the log panel (MEL/Python/log rules).
    """

    def __init__(self, text_edit):
        """
        Args:
            text_edit (QTextEdit)
        """

        self.init_rule(text_edit)
        CustomHighlighter.__init__(self, text_edit)

    def init_rule(self, text_edit=None):
        if text_edit is None:
            text_edit = self.parent()

        self.palette = palette.LogPalette(text_edit)
        self._python_palette = palette.PythonPalette(text_edit)
        self._mel_palette = palette.MelPalette(text_edit)

        self.rule = LogRule(
            self,
            self.palette,
            self._python_palette,
            self._mel_palette
        )


class MelHighlighter(CustomHighlighter):
    """
    Syntax highlighter for MEL tabs.
    """

    def __init__(self, text_edit):
        """
        Args:
            text_edit (QTextEdit)
        """

        self.init_rule(text_edit)
        CustomHighlighter.__init__(self, text_edit)

    def init_rule(self, text_edit=None):
        if text_edit is None:
            text_edit = self.parent()

        self.palette = palette.MelPalette(text_edit)
        self.rule = MelRule(self, self.palette)


class PythonHighlighter(CustomHighlighter):
    """
    Syntax highlighter for Python tabs.
    """

    def __init__(self, text_edit):
        """
        Args:
            text_edit (QTextEdit)
        """

        self.init_rule(text_edit)
        CustomHighlighter.__init__(self, text_edit)

    def init_rule(self, text_edit=None):
        if text_edit is None:
            text_edit = self.parent()

        self.palette = palette.PythonPalette(text_edit)
        self.rule = PythonRule(self, self.palette)


class Rule(object):
    """
    Base class for highlighting rules. Must be re-implemented.
    """

    docstr_chars = []
    docstr_close_chars = []
    cmnt_chars = []
    str_chars = []

    def __init__(self, highlighter, rule_palette):

        self.highlighter = highlighter
        self.palette = rule_palette
        self.styles = self.palette.char_formatted()
        self.rules = self.get_rules()

        self.delim_strings = self.docstr_chars +self.str_chars +self.cmnt_chars
        self.docstr_states = [i for i, _ in enumerate(self.docstr_chars)]
        self.str_states = [i +len(self.docstr_chars) for i, _ in enumerate(self.str_chars)]
        self.comment_states = [
            i +len(self.docstr_chars) +len(self.str_chars) for i, _ in enumerate(self.cmnt_chars)
        ]

        self.map_methods()

    def update(self):
        self.styles = self.palette.char_formatted()
        self.rules = self.get_rules()

        if hasattr(self, 'blocking_rules'):
            self.blocking_rules = self.get_blocking_rules()
        if hasattr(self, 'message_rules'):
            self.message_rules = self.get_message_rules()

    def apply_rule(self, line, expression, nth, txt_format):
        """
        Args:
            line (str)
            expression (QtCore.QRegExp or str)
            nth (int) : the nth matching group that is to be highlighted
            txt_format (QtGui.QTextCharFormat)

        Apply <txt_format> on segments that matches <expression> in <line>.

        """

        expression = QtCore.QRegExp(expression)
        index = expression.indexIn(line, 0)

        while index >= 0:
            # we want the index of the nth match
            index = expression.pos(nth)
            length = len(expression.cap(nth))
            # set segment format
            self.setFormat(index, length, txt_format)
            index = expression.indexIn(line, index + length)

    def apply(self, line):
        """
        Args:
            line (str)

        Apply all defined rules on line.
        """

        # straight-forward regex rules, no block state used
        for pattern, nth, txt_format in self.rules:
            self.apply_rule(line, pattern, nth, txt_format)

        # strings, docstrings and comments rules, using block states to propagate
        # un-closed rules from one line to another
        self.apply_multiline_style(line)

    def get_rules(self):
        """ Returns empty list by default. """
        return []

    def apply_multiline_style(self, line):
        """
        Args:
            line (str)

        Apply strings, docstrings and comments highlight on line.
        """

        # propagate previous line's state
        self.setCurrentBlockState(self.previousBlockState())

        offset = 99999999999
        start = 0
        pos = 0

        while len(line) > pos > -1:
            # get current delimiter
            state = self.currentBlockState()
            delim_str = self.delim_strings[state] if state > -1 else None

            # switch to docstring closing char
            if self.currentBlockState() in self.docstr_states:
                delim_idx = self.docstr_chars.index(delim_str)
                delim_str = self.docstr_close_chars[delim_idx]

                        ############################
                        #   No state is going on   #
                        ############################

            # if no current delimiter, get the next delimiter in line
            if delim_str is None:
                positions = [QtCore.QRegExp(x).indexIn(line, pos) for x in self.delim_strings]

                # no more delimiter in line
                if all(x == -1 for x in positions):
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
                delim_str = self.delim_strings[state]

                if state in self.comment_states:      # comments, paint until the end of the line
                    self.setFormat(pos, len(line) -pos, self.styles['comments'])
                    self.setCurrentBlockState(-1)
                    return          # there's no need for further analysis in this line

                # "open" str (set painting start position)
                start = pos
                pos += len(delim_str.replace('\\', ''))


                    ######################################
                    #   Some state is already going on   #
                    ######################################

            # else, search for the next occurence of the current delimiter in line
            else:
                next_pos = QtCore.QRegExp(delim_str).indexIn(line, pos)

                # not found
                if next_pos == -1:
                    # check for comments after a \-propagated string
                    comment_pos = QtCore.QRegExp('#').indexIn(line, pos)
                    # comments found
                    if comment_pos and self.currentBlockState() in self.str_states:
                        # last character before was a non-escaped \
                        if self.last_util_char(line, comment_pos) == '\\':
                            self.paint_string(start, comment_pos-1 -start, line)
                            self.setFormat(
                                comment_pos,
                                len(line) -comment_pos,
                                self.styles['comments']
                            )
                            return
                    break

                # closing char is escaped
                if self.is_escaped(line, next_pos):
                    self.paint_string(start, next_pos -start, line)
                    pos = next_pos +1
                    continue

                # "close" and paint string
                self.paint_string(start, next_pos +len(delim_str.replace('\\', '')) -start -1, line)
                self.setCurrentBlockState(-1)
                pos = next_pos +len(delim_str.replace('\\', ''))

        ##############################################################
        #   after iterations (current state may still be "opened")   #
        ##############################################################

        if self.currentBlockState() == -1:
            return

        # comments (those after \ string-propagation are handled higher)
        if self.currentBlockState() in self.comment_states:
            self.setFormat(start, len(line) -start -1, self.styles['comments'])
            self.setCurrentBlockState(-1)

        elif self.currentBlockState() in self.str_states:
            # no string-propagation
            if line[-1] != '\\':
                self.setCurrentBlockState(-1)
            else:
                self.paint_string(start, len(line) -start -1, line)
                self.setFormat(len(line)-1, 1, self.styles['special'])
        # triple-quotes
        else:
            self.paint_string(start, len(line) -start -1, line)

    def last_util_char(self, line, pos):
        """
        Args:
            line (str)
            pos (int)

        Returns:
            (str or None)

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

    def is_escaped(self, line, pos):
        """
        Args:
            line (str)
            pos (int)

        Returns:
            (bool)

        Check the escaped state of the character at <pos> in <line>.
        """

        escaped = False

        while pos:
            if line[pos-1] == '\\':
                escaped = not escaped
                pos -= 1
            else:
                break

        return escaped

    def paint_string(self, start, count, line):
        """
        Args:
            start (int) : string start pos in <line>
            count (int) : number of character to paint
            line (str)

        Returns:
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

    def map_methods(self):
        self.setFormat = self.highlighter.setFormat
        self.setCurrentBlockState = self.highlighter.setCurrentBlockState
        self.currentBlockState = self.highlighter.currentBlockState
        self.previousBlockState = self.highlighter.previousBlockState



class LogRule(Rule):
    """
    Syntax highlighter for Maya Script Editor's log panel. This class has its
    own specific rules, and also uses MEL and Python ones.
    """

    def __init__(self, highlighter, log_palette, python_palette, mel_palette):
        """
        Args:
            highlighter (LogHighlighter)
            palette (palette.Palette)
        """

        Rule.__init__(self, highlighter, log_palette)

        self.current_rule = 'log'

        self.rules = self.get_rules()
        self.blocking_rules = self.get_blocking_rules()
        self.message_rules = self.get_message_rules()

        self.mel_rules = MelRule(highlighter, mel_palette)
        self.python_rules = PythonRule(highlighter, python_palette)

    def get_blocking_rules(self):
        """
        Returns:
            (list[tuple(QtCore.QRegExp, int, QtGui.QTextCharFormat)])

        These rules are applied prior to MEL and Python rules. If any rule was
        used, all MEL, Python and self rules will be ignored.
        """

        # printed Python modules or methods (like <module 'maya' from '...'>)
        # rule, if not in string.
        rules = [
            (
                '(?<![\"\'])(<\s*\w+\s+\'.+\'\s+from\s+\'.+\'>)(?![\"\'])',
                1,
                self.styles['special']
            )
        ]

        # printed Python objects (like <PySide2.QtWidgets.QWidget) rule if
        # not in string.
        rules = [
            (
                '(?<![\"\'])(<\s*.+\s+object at\s+.+>\s*)(?![\"\'])',
                1,
                self.styles['special']
            )
        ]

        return rules

    def get_message_rules(self):
        """
        Returns:
            (list[tuple(QtCore.QRegExp, QtGui.QTextCharFormat)])

        Get all message rules. These are applied on the whole line, analysing the
        line with no case match.
        """

        # set info, warning, error and success messages rules
        rules = [
            (
                '^\s*%(char)s(.)+(%(type)s\s*:)' % {'char': c, 'type': x},
                self.styles[x]
            ) for c in ('//', '#') for x in BASE_MESSAGES
        ]

        # info lines with '//' or '#' at the start of the line
        rules += [('^\s*%s.*' % c, self.styles['info']) for c in ('//', '#')]
        # info lines with '//' or '#' at the end of the line
        rules += [('.*%s\s*$' % c, self.styles['info']) for c in ('//', '#')]

        # info lines with '[] msg:' at the start of the line
        rules += [
            (
                '^\s*\[\w+\]\s*(%s\s*:)' % x,
                self.styles[x]
            ) for x in BASE_MESSAGES
        ]

        return rules

    def apply(self, line):
        """
        Args:
            line (str)

        Apply syntax highlighting rules to the given line.
        """

        try:
            if self.traceback_applied(line):
                return

            # apply message rules, and skip next if some rule matches (as applied
            # on the whole line)
            for pattern, txt_format in self.message_rules:
                if re.match(pattern, line.lower()):
                    self.setFormat(0, len(line), txt_format)
                    self.current_rule = 'log'
                    return

            block_next = False
            # apply blocking rules
            for pattern, nth, txt_format in self.blocking_rules:
                match = re.search(pattern, line)

                if match:
                    start = match.start(nth)
                    end = match.end(nth)
                    self.setFormat(start, end -start, txt_format)
                    block_next = True

            if block_next:
                return

            if is_mel_line(line):
                if not self.current_rule in ('log', 'MEL'):
                    # interrupt potential opened docstrings
                    self.setCurrentBlockState(-1)
                self.current_rule = 'MEL'

            elif is_python_line(line):
                if not self.current_rule in ('log', 'Python'):
                    # interrupt potential opened docstrings
                    self.setCurrentBlockState(-1)
                self.current_rule = 'Python'

            if self.current_rule == 'MEL':
                self.mel_rules.apply(line)
            elif self.current_rule == 'Python':
                self.python_rules.apply(line)

            # apply overall rules
            for pattern, nth, txt_format in self.rules or ():
                self.apply_rule(line, pattern, nth, txt_format)

        # silent errors so we don't fall into a print loop...
        except:
            pass

    def apply_multiline_style(self, line):
        return

    def traceback_applied(self, line):
        """
        Args:
            line (str)

        Handle Tracebacks.
        """

        # propagate previous line's state
        self.setCurrentBlockState(self.previousBlockState())

        if re.match('^(#\s)*Traceback', line):
            self.setCurrentBlockState(5)
            self.setFormat(0, len(line), self.styles['traceback'])
            return True

        if self.currentBlockState() == 5:
            if re.match('^(#\s)*\s+', line):
                self.setFormat(0, len(line), self.styles['traceback'])
                return True
            else:
                self.setCurrentBlockState(-1)

        return False


class MelRule(Rule):
    """
    Syntax highlighter for the MEL language.
    """

    docstr_chars = ['/\\*']
    docstr_close_chars = ['\\*/']
    cmnt_chars = ['//']
    str_chars = ['"']

    def get_rules(self):
        """
        Returns:
            (list[tuple(QtCore.QRegExp, int, QtGui.QTextCharFormat)])

        Get all MEL rules, except for comments, strings and triple-quotes,
        that will be handled differently.
        """

        # digits rule
        rules = [('\\b\d+\\b', 0, self.styles['numbers'])]

        rules += [('^\s*\w+', 0, self.styles['called'])]
        rules += [('-(\w+)', 1, self.styles['flags'])]
        rules += [('(\"\w*\")', 1, self.styles['string'])]

        # $variables rules
        rules += [('\$\w+', 0, self.styles['variables'])]

        # add MEL keywords rules
        rules += [('\\b(%s)\\b' % w, 0, self.styles['keyword']) for w in kk.MEL_KEYWORDS]
        # add MEL numbers rules
        rules += [('\\b(%s)\\b' % n, 0, self.styles['numbers']) for n in kk.MEL_NUMBERS]
        # add MEL builtins rules
        rules += [('\\b(%s)\\b' % n, 0, self.styles['special']) for n in kk.MEL_BUILTINS]
        # add operators rules
        rules += [('%s' % o, 0, self.styles['operator']) for o in kk.OPERATORS]

        # declared procedures rule
        rules += [ ('(\\bproc\\b\s+)(.+\s+)*(\w+)\s*\(', 3, self.styles['proc_name']),]

        # expressions between ``
        rules += [('(`.*`)', 1, self.styles['called_expr'])]

        rules += [
                    # set '.' on float back to numbers style
                    ('\d+\.*\d+', 0, self.styles['numbers']),
                    # set ',' back to normal
                    (',', 0, self.styles['normal']),
                 ]

        return rules


class PythonRule(Rule):
    """
    Syntax highlighter for the Python language.
    """

    docstr_chars = ["'''", '"""']
    docstr_close_chars = ["'''", '"""']
    cmnt_chars = ['#']
    str_chars = ["'", '"']

    def get_rules(self):
        """
        Returns:
            (list[tuple(QtCore.QRegExp, int, QtGui.QTextCharFormat)])

        Get all Python rules, except for comments, strings and triple-quotes,
        that will be handled differently.
        """

        # digits rule
        rules = [('\\b\d+\\b', 0, self.styles['numbers'])]

        # add python "self" rule
        rules += [('\\b(self)\\b', 0, self.styles['self'])]
        # add python "builtins" words rules
        rules += [('\\b%s\\b' % x, 0, self.styles['special']) for x in kk.PYTHON_BUILTINS]

        rules += [
                     # inherited classes rule
                     ('(\\bclass\\b\s*_*\w+_*\s*\()(.+)(\))', 2, self.styles['class_arg']),
                     # declared classes rule
                     ('(\\bclass\\b\s*)(_*\w+_*)', 2, self.styles['class_name']),
                     # intermediates rule
                     ('(\.)(\w+)', 2, self.styles['interm']),
                     # declared functions rule
                     ('(\\bdef\\b\s*)(_*\w+_*)', 2, self.styles['def_name']),
                     # called functions rule
                     ('(\\b_*\w+_*\s*)(\()', 1, self.styles['called'])
                     # add python "builtins" words rules
                 ]

        # add python keywords rules
        rules += [('\\b(%s)\\b' % w, 0, self.styles['keyword']) for w in kk.PYTHON_KEYWORDS]

        # add operators rules
        rules += [('%s' % o, 0, self.styles['operator']) for o in kk.OPERATORS]

        rules += [
                     # kwargs first part rule
                     ('(,\s*|\()(\w+)(\s*=\s*)', 2, self.styles['numbers'])
                 ]

        # add numbers rule (called after intermediates sur float would not
        # be considered as intermediates)
        rules += [('\\b(%s)\\b' % n, 0, self.styles['numbers']) for n in kk.PYTHON_NUMBERS]

        rules += [
                    # set '.' on float back to numbers style
                    ('\d+\.*\d+', 0, self.styles['numbers']),
                    # set ',' back to normal
                    (',', 0, self.styles['normal']),
                 ]

        # add decorators rule
        rules += [('\s*\@\w+', 0, self.styles['decorators'])]

        return [(QtCore.QRegExp(pat), index, fmt) for (pat, index, fmt) in rules]



                        ###########################
                        #   detecting MEL lines   #
                        ###########################

def is_mel_line(line):
    # lines that ends with ";"
    if re.match('.+;$', line):
        return True
    if re.match('^\s*/\\*', line):                      # /* docstrings
        return True
    if re.search('(global\s+)*proc', line):             # proc declarations
        return True
    if re.match('\$.+\s*\=', line):                     # $variable declaration
        return True
    if re.match('for\s*\(.+\)\s*{', line):              # for (...) { declaration
        return True
    if re.match("^\s*//", line):                        # comment lines
        return True
    if re.search('\\btrue\\b', line):                    # true
        return True
    if re.search('\\bfalse\\b', line):                   # false
        return True
    if re.search('\\bnone\\b', line):                    # none
        return True

    loops_regex = '%s\s*\(.+\)\s*\{'
    if re.search(loops_regex % 'while', line):           # while (...) { declaration
        return True
    if re.search(loops_regex % 'for', line):             # for (...) { declaration
        return True
    if re.search(loops_regex % 'if', line):              # if (...) { declaration
        return True
    if re.search(loops_regex % 'else', line):            # else (...) { declaration
        return True
    if re.search(loops_regex % 'else if', line):         # else if (...) { declaration
        return True

    functions_regex = '%s\s*\(.+\)'
    if re.search(functions_regex % 'catch', line):           # catch (...) declaration
        return True
    if re.search(functions_regex % 'catchQuiet', line):      # catchQuiet (...) declaration
        return True

    return False


                      ##############################
                      #   detecting Python lines   #
                      ##############################


def is_python_line(line):
    if re.match('from(.)+import(.)+', line):            # "from" imports
        return True
    if re.match('import(.)+', line):                    # imports
        return True
    if re.search('(\\bdef\\b\s*)(_*\w+_*)', line):      # function declarations
        return True
    if re.search('(\\bclass\\b\s*)(_*\w+_*)', line):    # class declarations
        return True
    if re.match('^\s*"""', line):                       # """ docstrings
        return True
    if re.match("^\s*'''", line):                       # ''' docstrings
        return True
    if re.match("\s*\@\w+\s*", line):                   # decorators
        return True
    if re.match("^\s*#", line):                         # comment lines
        return True
    if re.search('\\bTrue\\b', line):                   # True
        return True
    if re.search('\\bFalse\\b', line):                  # False
        return True
    if re.search('\\bNone\\b', line):                   # None
        return True

    loops_regex = '%s\s*.*\s*:'
    if re.search(loops_regex % 'while', line):           # while (...) : declaration
        return True
    if re.search(loops_regex % 'for', line):             # for (...) : declaration
        return True
    if re.search(loops_regex % 'if', line):              # if (...) : declaration
        return True
    if re.search(loops_regex % 'else', line):            # else (...) : declaration
        return True
    if re.search(loops_regex % 'elif', line):            # else if (...) : declaration
        return True
    if re.search(loops_regex % 'try', line):             # try (...) : declaration
        return True
    if re.search(loops_regex % 'except', line):          # except (...) : declaration
        return True
    if re.search(loops_regex % 'finally', line):         # finally (...) : declaration
        return True

    if re.search('\s*print\s*(?!\()', line):            # print call without ()
        return True

    return False
