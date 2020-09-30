"""
Add CollapseButton on QTextEdits so user may collapse/expand text blocks.
"""

import re

from PySide2 import QtWidgets, QtCore, QtGui

from custom_script_editor import constants as kk
from custom_script_editor import utils
from custom_script_editor.multi_cursors import MultiCursorManager


class CollapseWidget(QtWidgets.QWidget):
    """
    Left-padding-area widget which will manage the CollapseButtons.
    """

    offsetX = 2

    def __init__(self, txt_edit):
        super(CollapseWidget, self).__init__(txt_edit)

        self.txt_edit = txt_edit

        self.buttons = []
        self.too_small_to_be_shown = False

        self.connect_signals()

        self.resize(kk.LEFT_PADDING, kk.INF_HEIGHT)

        self.update_all()

    def connect_signals(self):
        self.txt_edit.textChanged.connect(self.update_all)
        # update position on vertical scrollbar changes
        self.vertical_bar().valueChanged.connect(self.update_position)
        self.vertical_bar().rangeChanged.connect(self.update_all)
        self.vertical_bar().sliderMoved.connect(self.update_position)

        # update on QTextEdit zoom in/out
        text_lay = self.txt_edit.findChild(QtGui.QAbstractTextDocumentLayout)
        text_lay.documentSizeChanged.connect(self.on_zoom)

    def on_zoom(self, *args):
        """
        Hide buttons if text is too small, else update their positions.
        """

        if CollapseButton.radius >= self.line_height():
            self.too_small_to_be_shown = True
        else:
            self.too_small_to_be_shown = False

        self.update_buttons()

    def line_height(self):
        metrics = QtGui.QFontMetrics(self.txt_edit.font())
        return metrics.height() +metrics.lineSpacing()/2

    def vertical_bar(self):
        return self.txt_edit.verticalScrollBar()

    def update_all(self):
        self.update_position()      # update self.position
        self.update_buttons()       # update CollapseButtons

    def on_collapse(self):
        """
        Update all and clear multi-cursors.
        """

        self.update_all()

        button = self.sender()
        if not button.is_collapsed():
            return

        multi_manager = self.txt_edit.findChild(MultiCursorManager)
        if not multi_manager:
            return

        multi_manager.clear_cursors()

    def update_position(self, *args):
        """
        Match CollapseWidget's position with the scrolling area (using the
        vertical scrollbar value).
        """

        self.move(QtCore.QPoint(self.offsetX, -self.txt_edit.verticalScrollBar().value()))

    def update_buttons(self):
        """
        Add/remove necessary/un-necessary CollapseButtons and update all buttons
        position from corresponding block's positions.

        The commented lines where for an attempt to perform this update on the
        QTextEdit's visible area only. But it was not working well, so it must
        be re-examinated.
        """

        if self.too_small_to_be_shown:
            for button in self.buttons or ():
                button.setParent(None)
                button.deleteLater()

            self.buttons = []
            return

        # first_block = self.txt_edit.document().begin()
        # tmp_cursor = QtGui.QTextCursor(first_block)

        # txt_rect = self.txt_edit.geometry()
        block_count = self.txt_edit.document().blockCount()

        # proceeding = False

        # these two lists will be used to know which buttons are to be removed
        kept_buttons = []
        old_buttons = list(self.buttons)

        for i in range(0, block_count) or ():
            # block_rect = self.txt_edit.cursorRect(tmp_cursor)
            # block_rect = QtCore.QRect(
            #     txt_rect.x() +block_rect.x(),
            #     txt_rect.y() +block_rect.y(),
            #     block_rect.width(),
            #     block_rect.height()
            # )
            #
            # tmp_cursor.movePosition(tmp_cursor.Down, tmp_cursor.MoveAnchor)

            # if not txt_rect.contains(block_rect):
            #     # block is not into the visible QRect yet
            #     if not proceeding:
            #         continue
            #     # block is out of the visible QRect
            #     else:
            #         break
            #
            # else:
            #     proceeding = True

            block = self.txt_edit.document().findBlockByNumber(i)

            # do not show button on already collapsed lines
            if not block.isVisible():
                continue

            text = block.text().strip()
            # block matches a pattern
            if any(text.startswith(x) for x in kk.COLLAPSIBLE_PATTERNS):
                found = self.get_button(block)
                # if this block has already an associated button, just update
                # its position
                if found:
                    kept_buttons.append(found)
                    found.update_position()
                    continue

                # else, create a new button
                new_button = self.add_button(block)
                self.buttons.append(new_button)

        # remove all unused buttons
        for button in reversed(old_buttons) or ():
            if button not in kept_buttons:
                self.buttons.remove(button)
                button.setParent(None)
                button.deleteLater()

        # force CollapseWidget to update entirely
        self.update(self.geometry())

    def get_button(self, block):
        """
        Args:
            block (QtGui.QTextBlock)

        Returns:
            (CollapseButton or None)

        Get the existing CollapseButton that is associated to the <block>.
        """

        for button in self.buttons or ():
            if button.block == block:
                return button

    def add_button(self, block):
        """
        Args:
            block (QtGui.QTextBlock)

        Create new CollapseButton for <block>. Set its collapsed state from the
        next block's visibility state.
        """

        collapsed = True if not block.next().isVisible() else False

        button = CollapseButton(block, self, collapsed)
        # update CollapseWidget on block collapse/expand
        button.collapsed.connect(self.on_collapse)

        button.show()
        button.update_position()

        return button

    def paintEvent(self, event):
        """
        Qt re-implementation, paints the CollapseWidget itself.
        """

        painter = QtGui.QPainter(self)

        painter.setBrush(QtGui.QColor(207, 228, 255, 20))
        painter.setPen(QtCore.Qt.NoPen)

        painter.drawRect(0, 0, kk.LEFT_PADDING, kk.INF_HEIGHT)


class CollapseButton(QtWidgets.QPushButton):
    """
    QtGui.QTextBlock expand/collapse button.
    """

    collapsed = QtCore.Signal()

    colors = [
        QtGui.QColor(207, 228, 255, 100),
        QtGui.QColor(207, 228, 255, 160)
    ]

    radius = 10

    def __init__(self, block, collapse_widget, collapsed=False):
        """
        Args:
            block (QtGui.QTextBlock)
            collapse_widget (CollapseWidget)
            collapsed (bool, optional)
        """

        super(CollapseButton, self).__init__(collapse_widget)

        self.block = block
        self.collapse_widget = collapse_widget
        self.txt_edit = collapse_widget.txt_edit
        self._is_collapsed = collapsed

        self.pending_block = None
        self.start = None
        self.length = 0

        self.clicked.connect(self.toggle_visibility)

        self.setFixedSize(self.radius+2, self.radius+2)

    def update_position(self):
        """
        Maintain CollapseButton aligned with its associated QtGui.QTextBlock.
        """

        block_position = self.block.layout().position().toPoint()
        metrics = QtGui.QFontMetrics(self.txt_edit.font())
        self.move(4, block_position.y() +2 +(metrics.height() -self.radius)/2)

    def is_collapsed(self):
        return self._is_collapsed

    def toggle_visibility(self):
        """
        Toggle text block visibility (show/hide all  QtGui.QTextBlocks under
        self.block that matches grater indentation-level).

        For line breaks, a pending-block system will be used to manage their
        state without taking their indentation-level in account.
        """

        # get scrollbar's position so it will be restored at the end of this function
        v_scroolbar = self.collapse_widget.vertical_bar()
        v_pos = v_scroolbar.sliderPosition()

        block = self.block
        start_indent_level = self.get_indent_level(block)

        self.pending_block = None       # used for line breaks
        self.start = None
        self.length = 0
        self.block_count = 0
        state = None

        while True:
            block = block.next()
            # catch the visibility state that must be applied on the first block
            if state is None:
                state = not block.isVisible()

            # the end of the document is reached
            if block.blockNumber() == -1:
                break

            indent_level = self.get_indent_level(block)
            # line break
            if indent_level is None:
                self.set_pending_visibility(state)
                self.pending_block = block
                continue

            # indentation-level is strictly higher
            elif indent_level > start_indent_level:
                self.set_pending_visibility(state)
                self.set_block_visibility(block, state)

            else:
                # the last pending block is not edited here, so we keep the line
                # break that preceeds the next block of text
                break

        # toggle button's aspect
        self._is_collapsed = not self._is_collapsed

        # force the QTextEdit tobe properly updated
        self.update_block_area(self.start, self.length)
        self.repaint()

        if self.is_collapsed():
            self.collapsed.emit()

        # restore scrollbar's position
        v_scroolbar.setSliderPosition(v_pos)

    def set_pending_visibility(self, state):
        """
        Args:
            state (bool) : the visibility state that is to be applied

        Set <state> on previous block if it was pending (line breaks) and reset
        self.pending_block to None.
        """

        if not self.pending_block:
            return

        self.set_block_visibility(self.pending_block, state)
        self.pending_block = None

    def increment_counters(self, block):
        """
        Args:
            block (QtGui.QTextBlock)

        Update self.start and self.length values from <block>. These values will
        be used to trigger the QTextEdit update.
        """

        if self.start is None:
            self.start = block.position()
        self.length += block.length()

    def set_block_visibility(self, block, state):
        """
        Args:
            block (QtGui.QTextBlock)
            state (bool) : the visibility state that is to be applied

        Set <block>'s visibility <state> and update start/length counters.
        """

        if not block:
            return

        block.setVisible(state)
        self.increment_counters(block)

    def get_indent_level(self, block):
        """
        Args:
            block (QtGui.QTextBlock)

        Returns:
            (int or None)

        Get <block>'s indentation-level or None if the line is empty or
        whitespaces-only (will set this block as pending).
        """

        text = block.text()
        if not text:
            return None

        non_whitespace_chars = re.search('\S', text)

        if not non_whitespace_chars:
            return None

        return non_whitespace_chars.start(0)

    def update_block_area(self, start, length):
        """
        Args:
            start (int)
            length (int)

        Trigger QTextEdit's update through QTextDocument.markContentsDirty slot.
        It seems to be the only way to update properly the QTextEdit after editing
        some QTextBlocks visibility.
        """

        start = 0 if start is None else start
        self.txt_edit.document().markContentsDirty(start, length)

    def paintEvent(self, event):
        """
        Qt re-implementation, paints the CollapseButton itself, with a simple
        |-| / |+| paint, depending on collapsed state.
        """

        painter = QtGui.QPainter(self)
        painter.setBrush(QtCore.Qt.transparent)
        painter.setPen(self.colors[self._is_collapsed])

        painter.drawRect(QtCore.QRect(0, 0, self.radius, self.radius))
        # draw horizontal line
        painter.drawLine(3, self.radius/2, self.radius -3, self.radius/2)

        if self._is_collapsed:
            # draw vertical line
            painter.drawLine(self.radius/2, 3, self.radius/2, self.radius -3)


def set_collapse_widget(txt_edit):
    collapse_widget = CollapseWidget(txt_edit)
    collapse_widget.show()
