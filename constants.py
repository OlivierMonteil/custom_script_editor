"""
Scripts constant values.
"""

import string

from PySide2 import QtCore

            #######################################################
            #                        General                      #
            #######################################################

VALID_TABS_REGEX = ['MEL', 'Python', '[\w\-_]+(.py)$']
CUSTOM_MENU_NAME = 'CustomMenu'
SNIPPETS_BOX_NAME = 'SnippetBox'
WORD_WRAP_BOX_NAME = 'WordWrapBox'

INF_HEIGHT = 5000
INF_WIDTH = 10000

LEFT_PADDING = 20

            #######################################################
            #                         Keys                        #
            #######################################################

MOVE_KEYS = [
    QtCore.Qt.Key_Down,
    QtCore.Qt.Key_Up,
    QtCore.Qt.Key_Left,
    QtCore.Qt.Key_Right,
    QtCore.Qt.Key_End,
    QtCore.Qt.Key_Home
]

CHARACTERS = string.printable.split(' ')[0] +' '
# special chars, with accents, etc
SPECIAL_CHARS = u'\x83\x9a\x9c\x9e\xaa\xb5\xba\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6'
SPECIAL_CHARS += u'\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5'
SPECIAL_CHARS += u'\xf6\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff\x8a\x8c\x8e\x9f\xc0\xc1'
SPECIAL_CHARS += u'\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0'
SPECIAL_CHARS += u'\xd1\xd2\xd3\xd4\xd5\xd6\xd8\xd9\xda\xdb\xdc\xdd\xde'

            #######################################################
            #                   Blocks Collapse                   #
            #######################################################

COLLAPSIBLE_PATTERNS = [
    'def ',
    'class '
]

            #######################################################
            #                   Syntax Highlight                  #
            #######################################################

PYTHON_NUMBERS = [
    'None',
    'True',
    'False'
]

MEL_NUMBERS = [
    'none',
    'true',
    'false'
]

# python keywords
PYTHON_KEYWORDS = [
    'and',
    'as',
    'assert',
    'async',
    'await',
    'break',
    'class',
    'continue',
    'def',
    'del',
    'elif',
    'else',
    'except',
    'finally',
    'for',
    'from',
    'global',
    'if',
    'import',
    'in',
    'is',
    'lambda',
    'nonlocal',
    'not',
    'or',
    'pass',
    'raise',
    'return',
    'try',
    'while',
    'with',
    'yield'
]

# MEL keywords
MEL_KEYWORDS = [
    'break',
    'catch',
    'continue',
    'else if',
    'else',
    'for',
    'global',
    'if',
    'in',
    'proc',
    'return',
    'try',
    'while'
]

# operators
OPERATORS = [
    '=',
    '==',
    '!=',
    '<',
    '<=',
    '>',
    '>=',
    '\+',
    '-',
    '\*',
    '/',
    '//',
    '\%',
    '\*\*',
    '\+=',
    '-=',
    '\*=',
    '/=',
    '\%=',
    '\^',
    '\|',
    '\&',
    '\~',
    '>>',
    '<<'
]

# python builtins
PYTHON_BUILTINS = [
    'ArithmeticError',
    'AssertionError',
    'AttributeError',
    'BaseException',
    'BlockingIOError',
    'BrokenPipeError',
    'BufferError',
    'BytesWarning',
    'ChildProcessError',
    'ConnectionAbortedError',
    'ConnectionError',
    'ConnectionRefusedError',
    'ConnectionResetError',
    'DeprecationWarning',
    'EOFError',
    'Ellipsis',
    'EnvironmentError',
    'Exception',
    'FileExistsError',
    'FileNotFoundError',
    'FloatingPointError',
    'FutureWarning',
    'GeneratorExit',
    'IOError',
    'ImportError',
    'ImportWarning',
    'IndentationError',
    'IndexError',
    'InterruptedError',
    'IsADirectoryError',
    'KeyError',
    'KeyboardInterrupt',
    'LookupError',
    'MemoryError',
    'ModuleNotFoundError',
    'NameError',
    'NotADirectoryError',
    'NotImplemented',
    'NotImplementedError',
    'OSError',
    'OverflowError',
    'PendingDeprecationWarning',
    'PermissionError',
    'ProcessLookupError',
    'RecursionError',
    'ReferenceError',
    'ResourceWarning',
    'RuntimeError',
    'RuntimeWarning',
    'StopAsyncIteration',
    'StopIteration',
    'SyntaxError',
    'SyntaxWarning',
    'SystemError',
    'SystemExit',
    'TabError',
    'TimeoutError',
    'TypeError',
    'UnboundLocalError',
    'UnicodeDecodeError',
    'UnicodeEncodeError',
    'UnicodeError',
    'UnicodeTranslateError',
    'UnicodeWarning',
    'UserWarning',
    'ValueError',
    'Warning',
    'WindowsError',
    'ZeroDivisionError',
    '__build_class__',
    '__debug__',
    '__doc__',
    '__import__',
    '__loader__',
    '__name__',
    '__package__',
    '__spec__',
    'abs',
    'all',
    'any',
    'ascii',
    'bin',
    'bool',
    'breakpoint',
    'bytearray',
    'bytes',
    'callable',
    'chr',
    'classmethod',
    'compile',
    'complex',
    'copyright',
    'credits',
    'delattr',
    'dict',
    'dir',
    'divmod',
    'enumerate',
    'eval',
    'exec',
    'exit',
    'filter',
    'float',
    'format',
    'frozenset',
    'getattr',
    'globals',
    'hasattr',
    'hash',
    'help',
    'hex',
    'id',
    'input',
    'int',
    'isinstance',
    'issubclass',
    'iter',
    'len',
    'license',
    'list',
    'locals',
    'map',
    'max',
    'memoryview',
    'min',
    'next',
    'object',
    'oct',
    'open',
    'ord',
    'pow',
    'print',
    'property',
    'qApp',
    'quit',
    'range',
    'repr',
    'reversed',
    'round',
    'set',
    'setattr',
    'slice',
    'sorted',
    'staticmethod',
    'str',
    'sum',
    'super',
    'tuple',
    'type',
    'vars',
    'zip'
]
# MEL builtins
MEL_BUILTINS = [
    'abs',
    'bool',
    'eval',
    'float',
    'int',
    'max',
    'min',
    'pow',
    'print',
    'round',
    'string',
]
