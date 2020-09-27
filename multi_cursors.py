from PySide2 import QtWidgets, QtCore, QtGui

class MultiCursor(QtCore.QObject):

    """
    Custom eventFilter installed on Maya's main window that will set highlight,
    custom menu and hotkeys on Script Editor QTextEdits (with evalDeferred).
    """

    events_trigger = [
        QtCore.QEvent.MouseButtonPress
    ]
    cursor_colors = [
        (94, 132, 255),
        (117, 229, 92)
    ]

    def __init__(self, script_editor):
        super(MultiCursor, self).__init__(script_editor)

        self.txt_edits_list = []
        self.cursors_list = []
        self.multi_cursors_list = []
        self.overlays_list = []
        self.repaint_region = None
        self.idx = -1

        # set cursor blinking timer
        self.timer = QtCore.QTimer(interval = 500)
        self.timer.timeout.connect(self.blink_cursors)

        self.cursor_state = True    # used to switch cursor's colors

    def eventFilter(self, obj, event):
        # (no need to run set_customize_on_tab_change and customize_script_editor
        # if the Script Editor is already opened)

        if not event.type() in self.events_trigger:
            return False

        txt_edit = obj.parent()

        if False:
            key = event.key()

            if event.key() == QtCore.Qt.Key_Backspace:
                self.multi_exec(self.multi_cursor().deletePreviousChar)
                return

            elif event.key() == QtCore.Qt.Key_Delete:
                self.multi_exec(self.multi_cursor().deleteChar)
                return


            else:
                if event.modifiers() & QtCore.Qt.ControlModifier:
                    if key == QtCore.Qt.Key_V:
                        text = QtGui.QClipboard().text()
                        self.multi_exec(self.multi_cursor().insertText, text)
                        return

                else:
                    text = event.text()
                    self.multi_exec(self.multi_cursor().insertText, text)
                    return

            QtWidgets.QTextEdit.keyPressEvent(self.txt_edit(()), event)

        elif event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() & QtCore.Qt.LeftButton:
                pos = event.pos()
                # get new QTextCursor at mouse position
                new_cursor = txt_edit.cursorForPosition(pos)

                if event.modifiers() & QtCore.Qt.ControlModifier:
                    self.cursors_list[self.idx].append(new_cursor)

                    self.idx = self.txt_edits_list.index(txt_edit)

                    if not self.timer.isActive():
                        self.timer.start()

                    return True

                else:
                    self.set_cursors([new_cursor])
                    self.update_cursors()
                    self.timer.stop()

        return False

    def txt_edit(self):
        return self.txt_edits_list[self.idx]
    def cursors(self):
        return self.cursors_list[self.idx]
    def set_cursors(self, cursors):
        self.cursors_list[self.idx] = cursors
    def multi_cursor(self):
        return self.multi_cursors_list[self.idx]
    def overlay(self):
        return self.overlays_list[self.idx]

    def install_if_not_already(self, txt_edit):
        if txt_edit in self.txt_edits_list:
            return

        txt_edit.viewport().installEventFilter(self)
        self.txt_edits_list.append(txt_edit)

        cursor = txt_edit.textCursor()
        self.cursors_list.append([cursor])
        self.multi_cursors_list.append(QtGui.QTextCursor(cursor))   # creates a copy

        viewport = txt_edit.viewport()
        overlay = QtWidgets.QWidget(txt_edit)
        overlay.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        overlay.move(viewport.pos().x(), viewport.pos().y())
        self.overlays_list.append(overlay)
        overlay.show()

        #txt_edit.keyPressEvent = self.key_press_event
        #txt_edit.mousePressEvent = self.mouse_press_event
        txt_edit.paintEvent = self.paint_event
        txt_edit.resizeEvent = self.resize_event

    def resize_event(self, event):
        overlay = self.overlay()
        txt_edit = self.txt_edit()

        new_size = event.size()
        overlay.resize(new_size.width(), new_size.height())
        QtWidgets.QTextEdit.resizeEvent(txt_edit, event)
        overlay.move(txt_edit.viewport().pos().x(), txt_edit.viewport().pos().y())

    def relative_to_viewport(self, rect):
        txt_edit = self.txt_edit()
        offset_x = txt_edit.viewport().pos().x()
        offset_y = txt_edit.viewport().pos().y()
        rect.moveTo(rect.x() +offset_x, rect.y() +offset_y)
        return rect


    def paint_event(self, event):
        """
        (overwrites QTextEdit's paintEvent)
        Paint multi-cursors (switch between two colors to paint over the actual
        cursor).
        """

        txt_edit = self.txt_edit()
        overlay = self.overlay()

        QtWidgets.QWidget.paintEvent(txt_edit, event)

        # paint multi-cursors
        if len(self.cursors()) > 1:
            painter = QtGui.QPainter(overlay)
            painter.setPen(QtGui.QColor(*self.cursor_colors[self.cursor_state]))

            for cursor in self.cursors():
                rect = txt_edit.cursorRect(cursor)
                painter.drawRect(rect)

    def multi_exec(self, func, *args, **kwargs):

        txt_edit = self.txt_edit()
        multi_cursor = self.multi_cursor()
        cursors = self.cursors()

        multi_cursor.beginEditBlock()

        for cursor in cursors:
            if cursor.hasSelection():
                # set the same selection
                multi_cursor.setPosition(cursor.selectionStart(), cursor.MoveAnchor)
                multi_cursor.movePosition(cursor.selectionEnd(), cursor.KeepAnchor)
            else:
                # move cursor at the same position
                multi_cursor.setPosition(cursor.position(), cursor.MoveAnchor)

            # run
            func(*args, **kwargs)

        multi_cursor.endEditBlock()

    def update_cursors(self):
        """
        Args:
            cursors (list[QtGui.QTextCursor])

        Repaint all <cursors> regions.
        """

        cursors = self.cursors()
        txt_edit = self.txt_edit()
        overlay = self.overlay()

        for cursor in cursors or ():
            rect = txt_edit.cursorRect(cursor)
            top_left = rect.topLeft()
            top_left = txt_edit.mapTo(overlay, top_left)
            rect.setTopLeft(top_left)
            # self.repaint_region = rect
            # overlay.repaint(
            #     rect.x() -5,
            #     rect.y() -5,
            #     rect.width() +10,
            #     rect.height() +10
            # )
            txt_edit.repaint(
                rect.x() -5,
                rect.y() -5,
                rect.width() +10,
                rect.height() +10
            )

    def blink_cursors(self):
        """
        Toggle self.cursor_state and repaint all cursors.
        """

        self.cursor_state = not self.cursor_state
        self.update_cursors()
