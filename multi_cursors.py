from PySide2 import QtWidgets, QtCore, QtGui

class MultiCursor(QtCore.QObject):

    """
    Custom eventFilter installed on Maya's main window that will set highlight,
    custom menu and hotkeys on Script Editor QTextEdits (with evalDeferred).
    """

    events_trigger = [
        QtCore.QEvent.MouseButtonPress
    ]

    def __init__(self, script_editor):
        super(MultiCursor, self).__init__(script_editor)

        self.text_edits = []

    def eventFilter(self, obj, event):
        # (no need to run set_customize_on_tab_change and customize_script_editor
        # if the Script Editor is already opened)

        if not event.type() in self.events_trigger:
            return False

        if event.button() & QtCore.Qt.LeftButton:
            if not event.modifiers() & QtCore.Qt.ControlModifier:
                return False

            textEdit = obj.parentWidget()
            print (textEdit)
            print (self.text_edits)

        return False

    def install_if_not_already(self, txt_edit):
        if txt_edit not in self.text_edits:
            print ('install on', txt_edit)

            txt_edit.viewport().installEventFilter(self)
            self.text_edits.append(txt_edit)

            print ('// installed')

class MultiCursorHandler_bckp(object):
    """
    Multi-cursors manager for QTextEdits.
    """

    cursor_colors = [
        (94, 132, 255),
        (117, 229, 92)
    ]

    def __init__(self, text_edit):
        self.text_edit = text_edit

        cursor = text_edit.textCursor()
        self.cursors = [cursor]
        self.multi_cursor = QtGui.QTextCursor(cursor)   # creates a copy
        # set cursor blinking timer
        self.timer = QtCore.QTimer(interval = 500)
        self.timer.timeout.connect(self.blink_cursors)

        self.overlay = QtWidgets.QWidget(text_edit.viewport().parent())
        self.overlay.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        self.overlay.move(text_edit.pos().x(), text_edit.pos().y())

        self.cursor_state = True    # used to switch cursor's colors

        self.overwrite_methods()

    def overwrite_methods(self):
        self.text_edit.keyPressEvent = self.key_press_event
        self.text_edit.mousePressEvent = self.mouse_press_event
        self.overlay.paintEvent = self.paint_event
        self.text_edit.resizeEvent = self.resize_event

    def resize_event(self, event):
        new_size = event.size()
        self.overlay.resize(new_size.width(), new_size.height())
        QtWidgets.QTextEdit.resizeEvent(self.text_edit, event)

    def key_press_event(self, event):
        key = event.key()

        if event.key() == QtCore.Qt.Key_Backspace:
            self.multi_exec(self.multi_cursor.deletePreviousChar)
            return

        elif event.key() == QtCore.Qt.Key_Delete:
            self.multi_exec(self.multi_cursor.deleteChar)
            return


        else:
            if event.modifiers() & QtCore.Qt.ControlModifier:
                if key == QtCore.Qt.Key_V:
                    text = QtGui.QClipboard().text()
                    self.multi_exec(self.multi_cursor.insertText, text)
                    return

            else:
                text = event.text()
                self.multi_exec(self.multi_cursor.insertText, text)
                return

        QtWidgets.QTextEdit.keyPressEvent(self.text_edit, event)

    def multi_exec(self, func, *args, **kwargs):
        """
        Args:
            func (method)
            args : all method arguments
            kwargs : all method keyword arguments

        Use self.multi_cursor to perform <func(*args, **kwargs)> at every cursor
        position under a single edit block (for undo/redo).
        """

        self.multi_cursor.beginEditBlock()

        for cursor in self.cursors:
            if cursor.hasSelection():
                # set the same selection
                self.multi_cursor.setPosition(cursor.selectionStart(), cursor.MoveAnchor)
                self.multi_cursor.movePosition(cursor.selectionEnd(), cursor.KeepAnchor)
            else:
                # move cursor at the same position
                self.multi_cursor.setPosition(cursor.position(), cursor.MoveAnchor)

            # run
            func(*args, **kwargs)

        self.multi_cursor.endEditBlock()

    def mouse_press_event(self, event):
        """
        (overwrites QTextEdit's mousePressEvent)
        Add multi-cursors on Ctrl +LMB click.
        """

        if event.button() == QtCore.Qt.LeftButton:
            pos = event.pos()
            # get new QTextCursor at mouse position
            new_cursor = self.text_edit.cursorForPosition(pos)

            if event.modifiers() == QtCore.Qt.ControlModifier:
                self.cursors.append(new_cursor)
                self.update_cursors(self.cursors)

                print ('new cursor added')

                if not self.timer.isActive():
                    self.timer.start()

            else:
                old_cursors = self.cursors
                self.cursors = [new_cursor]
                self.update_cursors(old_cursors)
                self.timer.stop()

        QtWidgets.QTextEdit.mousePressEvent(self.text_edit, event)

    def update_cursors(self, cursors):
        """
        Args:
            cursors (list[QtGui.QTextCursor])

        Repaint all <cursors> regions.
        """

        for cursor in cursors or ():
            rect = self.text_edit.cursorRect(cursor)
            self.overlay.repaint(
                rect.x() -5,
                rect.y() -5,
                rect.width() +10,
                rect.height() +10,
            )

    def blink_cursors(self):
        """
        Toggle self.cursor_state and repaint all cursors.
        """

        self.cursor_state = not self.cursor_state
        self.update_cursors(self.cursors)

    def paint_event(self, event):
        """
        (overwrites QTextEdit's paintEvent)
        Paint multi-cursors (switch between two colors to paint over the actual
        cursor).
        """

        # paint multi-cursors
        if len(self.cursors) > 1:
            painter = QtGui.QPainter(self.overlay)
            painter.setPen(QtGui.QColor(*self.cursor_colors[self.cursor_state]))

            for cursor in self.cursors:
                rect = self.text_edit.cursorRect(cursor)
                painter.drawRect(rect)
