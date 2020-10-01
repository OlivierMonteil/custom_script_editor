"""
GUI for palette editing, saving and applying.
"""

import os
import json

from maya.OpenMayaUI import MQtUtil
from PySide2 import QtWidgets, QtCore, QtGui
import shiboken2 as shiboken


from custom_script_editor import syntax_highlight
from custom_script_editor import palette
from custom_script_editor import constants as kk


STYLE_PATTERN = """
QTextEdit#%(object_name)s {
    color: rgb%(color)s;
    background : rgb%(background)s;
}
"""

PALETTES_ROOT = os.path.join(os.path.dirname(__file__), 'palettes')
WINDOW_OBJECT_NAME = 'CSE_paletteEditor'



class PaletteEditor(QtWidgets.QMainWindow):
    """
    Main "Edit palettes" GUi.
    """

    rule_types = ('log', 'mel', 'python')

    def __init__(self, parent=None):
        super(PaletteEditor, self).__init__(parent=parent)

        self.highlighter = None
        self.sample_text = None

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle('Edit palettes')
        self.setObjectName(WINDOW_OBJECT_NAME)

        central_widget = QtWidgets.QWidget(self)
        central_lay = QtWidgets.QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        rule_widget = QtWidgets.QWidget(self)
        self.lay = QtWidgets.QGridLayout(rule_widget)

        central_lay.addWidget(rule_widget)

        buttons_widget = QtWidgets.QWidget(self)
        buttons_lay = QtWidgets.QHBoxLayout(buttons_widget)
        central_lay.addWidget(buttons_widget)

        apply_button = QtWidgets.QPushButton('Apply', self)
        save_button = QtWidgets.QPushButton('Save as...', self)
        set_default_button = QtWidgets.QPushButton('Set as default', self)

        for button in (apply_button, save_button, set_default_button):
            buttons_lay.addWidget(button)

        # prevent keys propagation to Maya Window
        self.keyPressEvent = lambda *args: None
        self.keyReleaseEvent = lambda *args: None

        for widget in (
            central_widget,
            central_lay,
            rule_widget,
            buttons_widget,
            buttons_lay
        ):
            widget.setContentsMargins(0, 0, 0, 0)
        self.setContentsMargins(4, 4, 4, 4)
        self.lay.setContentsMargins(4, 4, 4, 4)


        self.setStyleSheet(
        """
        QMainWindow {
            background : rgb(43, 43, 43);
            color: rgb(180, 180, 190);
        }""")

        self.set_toolbar()
        self.display_palette('default')

        save_button.clicked.connect(self.save_preset)
        apply_button.clicked.connect(self.apply_preset)
        set_default_button.clicked.connect(self.set_as_default)

    def set_toolbar(self):
        # create bar and menus
        toolbar = QtWidgets.QToolBar(self, floatable=False, movable=False)

        self.rules_box = QtWidgets.QComboBox(self)
        for rule in self.rule_types:
            self.rules_box.addItem(rule)

        toolbar.addWidget(self.rules_box)

        menu_button = QtWidgets.QToolButton(self)
        menu_button.setText('Presets')
        menu_button.setPopupMode(menu_button.InstantPopup)
        menu = QtWidgets.QMenu(menu_button, self)
        menu_button.setMenu(menu)
        load_preset = menu.addAction('Load...')
        delete_preset = menu.addAction('Delete')

        toolbar.addWidget(menu_button)

        toolbar.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.addToolBar(QtCore.Qt.TopToolBarArea, toolbar)

        self.rules_box.currentTextChanged.connect(lambda x: self.display_palette('default'))
        load_preset.triggered.connect(self.load_preset)
        delete_preset.triggered.connect(self.delete_preset)

        toolbar.setStyleSheet("""
            QToolBar, QMenuBar {
                background-color : rgb(70, 70, 70);
                border : 1px solid rgb(58, 58, 58);
            }

            QToolBar QToolButton {
                width : 50;
            }

            QLabel {
                padding-left: 3px;
            }"""
        )

    def load_preset(self):
        """
        Load preset and apply it on text sample.
        """

        rule_type = self.rules_box.currentText()

        dialog = PresetsDialog(
            os.path.join(PALETTES_ROOT, rule_type),
            title='Load preset file',
            parent=self
        )

        accepted = dialog.exec_()

        if accepted:
            path = dialog.get_selected_path()

            with open(path, 'r') as opened_file:
                content = json.load(opened_file)
                theme = path.split('/')[-1]
                theme = ('.').join(theme.split('.')[:-1])

                self.display_palette(None, force_palette=(theme, content))

    def set_as_default(self):
        print (kk.WARNING_MESSAGE.format('not implemented yet.'))

    def apply_preset(self):
        print (kk.WARNING_MESSAGE.format('not implemented yet.'))

    def save_preset(self):
        txt_type = self.rules_box.currentText()

        dialog = PresetsDialog(
            os.path.join(PALETTES_ROOT, txt_type),
            title='Save As...',
            parent=self,
            create=True
        )

        accepted = dialog.exec_()

        if accepted:
            template_dict = palette.get_palette('{}/template'.format(txt_type))

            attributes = template_dict['attributes']
            save_dict = {}

            for attr in attributes:
                save_dict[attr] = self.buttons[attr].rgb

            path = dialog.get_selected_path()

            print (kk.WARNING_MESSAGE.format('save action is not implemented yet.'))

    def delete_preset(self):
        print (kk.WARNING_MESSAGE.format('not implemented yet.'))

    def clear_layout(self):
        count = self.lay.count()

        for i in range(count):
            self.lay.itemAt(i).widget().deleteLater()

    def display_palette(self, theme, force_palette=None):
        """
        Args:
            theme (str)
            force_palette (dict, optional)

        Show all parameters and colors into layout.
        Run add_text_sample() at the end to add also the QTextEdit with text sample.
        """

        # remove all current layout's widgets
        self.clear_layout()

        txt_type = self.rules_box.currentText()

        # get theme palette and template dict
        if force_palette:
            theme, theme_palette = force_palette
        else:
            theme_palette = palette.get_palette('{}/{}'.format(txt_type, theme))

        template_dict = palette.get_palette('{}/template'.format(txt_type))
        attr_dict = template_dict['attributes']
        attributes = sorted(attr_dict.keys(), key=lambda x: attr_dict[x][0])

        self.buttons = {}
        i = 0

        # add every parameter with its QColorButton set
        for attr in attributes or ():
            label, tooltip = attr_dict[attr]

            label_widget = QtWidgets.QLabel(label, self, toolTip=tooltip)
            color_button = ColorButton(
                tuple(theme_palette[attr]),
                attr,
                label,
                self
            )

            self.lay.addWidget(label_widget, i, 0)
            self.lay.addWidget(color_button, i, 1)

            self.buttons[attr] = color_button
            self.lay.setRowStretch(i, 0)

            color_button.color_changed.connect(self.on_color_changed)

            i += 1

        self.lay.setRowStretch(i, 10)

        # add QTextEdit
        self.add_text_sample(i, txt_type, theme)

    def add_text_sample(self, row, txt_type, theme):
        """
        Args:
            row (int)
            txt_type (str)
            theme (str)

        Create and add sample text field (QTextEdit).
        """

        self.sample_text = QtWidgets.QTextEdit(self, readOnly=True)
        self.sample_text.setObjectName(WINDOW_OBJECT_NAME +'_sampleTextEdit')

        #self.sample_text.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.sample_text.viewport().setCursor(QtCore.Qt.ArrowCursor)

        # apply highlight
        if txt_type == 'mel':
            self.highlighter = syntax_highlight.MelHighlighter(self.sample_text)
        elif txt_type == 'python':
            self.highlighter = syntax_highlight.PythonHighlighter(self.sample_text)
        elif txt_type == 'log':
            self.highlighter = syntax_highlight.LogHighlighter(self.sample_text)

        # set theme
        self.highlighter.set_theme(theme)

        # set font
        font = QtGui.QFont("DejaVu Sans Mono", 8)
        self.sample_text.setFont(font)

        self.lay.addWidget(self.sample_text, 0, 2, row+1, 1)

        # add sample.txt content into the QTextEdit
        sample_file = os.path.join(PALETTES_ROOT, '{}/sample.txt'.format(txt_type))
        text = ''

        with open(sample_file, 'r') as opened_file:
            try:
                text = opened_file.read()
            except:
                pass

        self.sample_text.setText(text)


    def on_color_changed(self):
        """
        Args:
        rgb (tuple[float])

        Update palette with new color.
        """

        attr = self.sender().attr
        rgb = self.sender().rgb

        self.highlighter.palette.set_color(attr, rgb)
        self.highlighter.update_rule()


class ColorButton(QtWidgets.QPushButton):
    """
    Custom QPushButton for color picking.
    """

    counter = 0
    color_changed = QtCore.Signal()

    def __init__(self, rgb, attr, label, *args, **kwargs):
        super(ColorButton, self).__init__(*args, **kwargs)

        self.rgb = None
        self.attr = attr
        self.label = label
        self.setMaximumSize(16, 16)
        self.setObjectName('ColorButton' +str(self.counter))

        self.clicked.connect(self.open_color_picker)

        ColorButton.counter += 1
        if rgb:
            self.set_rgb(rgb)

    def open_color_picker(self):
        """
        Open a QColorDialog and edit ColorButton's color if user picjed a new color.
        (emits color_changed signal in set_rgb() so the QTextEdit palette will be
        updated)
        """

        dialog = QtWidgets.QColorDialog(self)
        dialog.setOption(dialog.DontUseNativeDialog)
        dialog.setWindowTitle('Select {} color'.format(self.label))

        # set ColorButton's color as dialog's current one
        qcolor = QtGui.QColor(*self.rgb)
        dialog.setCurrentColor(qcolor)
        # add ColorButton's color to dialog's custom colors if not already in
        if not any(dialog.customColor(i) == qcolor for i in range(dialog.customCount())):
            for i in reversed(range(dialog.customCount())):
                dialog.setCustomColor(i+1, dialog.customColor(i))
            dialog.setCustomColor(0, qcolor)

        # run dialog
        if dialog.exec_():
            new_rgb = dialog.currentColor()
            new_rgb = [new_rgb.red(), new_rgb.green(), new_rgb.blue()]
            self.set_rgb(new_rgb)

    def set_rgb(self, rgb):
        """
        Args:
            rgb (list[float])

            Set QColorButton's color and emit color_changed signal.
        """

        if rgb != self.rgb:
            self.rgb = rgb
            self.color_changed.emit()

        if self.rgb:
            self.setStyleSheet(
                'QPushButton#%s {background-color: rgb(%s, %s, %s)}' % (
                    self.objectName(), rgb[0], rgb[1], rgb[2]
                )
            )
        else:
            self.setStyleSheet('')


class PresetsDialog(QtWidgets.QDialog):
    """
    """

    def __init__(self, root_dir, title=None, parent=None, create=False):
        super(PresetsDialog, self).__init__(parent)

        self.setWindowTitle(title)

        layout = QtWidgets.QVBoxLayout(self)

        self.name_field = None
        self.label = QtWidgets.QLabel(self)

        self.list_view = QtWidgets.QListView(self)
        self.list_view.setAlternatingRowColors(True)

        self.file_model = QtWidgets.QFileSystemModel(self.list_view)
        self.file_model.setFilter(QtCore.QDir.Files | QtCore.QDir.Dirs | QtCore.QDir.NoDot)
        self.proxy_model = ProxyModel(self.list_view, root_dir)
        self.list_view.setModel(self.proxy_model)
        self.proxy_model.setSourceModel(self.file_model)

        layout.addWidget(self.label)
        layout.addWidget(self.list_view)

        buttons_widget = QtWidgets.QWidget(self)
        buttons_lay = QtWidgets.QHBoxLayout(buttons_widget)

        self.open_button = QtWidgets.QPushButton('Open', self, enabled=False)
        cancel_button = QtWidgets.QPushButton('Cancel', self)

        buttons_lay.addWidget(self.open_button)
        buttons_lay.addWidget(cancel_button)

        layout.addWidget(self.list_view)
        if create:
            self.name_field = QtWidgets.QLineEdit(self)
            layout.addWidget(self.name_field)
        layout.addWidget(buttons_widget)

        self.list_view.doubleClicked.connect(self.handle_double_click)
        self.list_view.clicked.connect(self.handle_click)
        self.list_view.mouseReleaseEvent = self.on_mouse_release
        self.open_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        for widget in (self, buttons_widget, buttons_lay):
            widget.setContentsMargins(0, 0, 0, 0)

        self.set_root(root_dir)
        self.update_path_label()

    def update_path_label(self):
        index = self.list_view.rootIndex()
        path = self.file_model.filePath(self.proxy_model.mapToSource(index))
        self.label.setText(path)

    def on_mouse_release(self, event):
        pos = event.pos()
        proxy_index = self.list_view.indexAt(pos)
        model_index = self.proxy_model.mapToSource(proxy_index)
        path = self.file_model.filePath(model_index)

        if not path:
            self.open_button.setEnabled(False)
            self.list_view.clearSelection()

        QtWidgets.QListView.mouseReleaseEvent(self.list_view, event)

    def handle_click(self, proxy_index):
        model_index = self.proxy_model.mapToSource(proxy_index)
        path = self.file_model.filePath(model_index)

        if not path or not os.path.isfile(path):
            self.open_button.setEnabled(False)

        else:
            self.open_button.setEnabled(True)

    def handle_double_click(self, proxy_index):
        model_index = self.proxy_model.mapToSource(proxy_index)
        path = self.file_model.filePath(model_index)

        if not path:
            return

        if os.path.isfile(path):
            self.accept()

        elif os.path.isdir(path):
            self.set_root(path)

    def get_path(self):
        pass

    def proxy_index(self, path):
        """
        Args:
            path (str) : absolute path

        Returns:
            (QtCore.QModelIndex) : index from ProxyModel

        Get ProxyModel's index for <path>.
        """

        index = self.file_model.setRootPath(path)
        return self.proxy_model.mapFromSource(index)

    def set_root(self, path):
        """
        Args:
            path (str) : absolute path

        Returns:
            None

        Set view's root <path>.

        """
        index = self.file_model.setRootPath(path)
        self.list_view.setRootIndex(self.proxy_index(path))

    def get_selected_path(self):
        """
        Returns:
            (str) : absolute path

        Get current view's path. If no item is selected get view's root path.
        """

        index = self.list_view.currentIndex()

        if not self.list_view.selectionModel().isSelected(index):
            return self.file_model.rootPath()

        return self.file_model.filePath(self.proxy_model.mapToSource(index))


class ProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, view, root_dir, *args, **kwargs):
        super(ProxyModel, self).__init__(view, *args, **kwargs)

        self.root_dir = root_dir

    def filterAcceptsRow(self, row, parent_index):
        """
        Args:
            row (int)
            parent_index (QtCore.QModelIndex) : from FileModel !!

        Returns:
            (bool)

        Qt re-implementation. Exclude template.json fies from dialog.
        """

        source_model = self.sourceModel()
        model_index = parent_index.child(row, 0)
        file_path = source_model.filePath(model_index).replace('\\', '/')

        if file_path.split('/')[-1] == '..':
            if file_path == os.path.join(self.root_dir, '..').replace('\\', '/'):
                return False

        if os.path.isfile(file_path) and not file_path.endswith('.json'):
            return False

        if file_path.split('/')[-1] == 'template.json':
            # prevent from adding this row
            return False

        return True


def closeExisting(maya_ui_qt):
    """
    Args:
        maya_ui_qt (QtWidgets.QMainWindow) : wrapped instance of Maya's main window

    Close existing MainWindow instance in Maya.
    """

    for widget in maya_ui_qt.children():
        if widget.objectName() == WINDOW_OBJECT_NAME:
            widget.setParent(None)
            widget.close()
            widget.deleteLater()
            del widget
            break


def run(pos=None):
    maya_ui = MQtUtil.mainWindow()
    maya_ui_qt = shiboken.wrapInstance(long(maya_ui), QtWidgets.QMainWindow)

    closeExisting(maya_ui_qt)

    window = PaletteEditor(maya_ui_qt)
    window.show()

    # center window on mouse position
    if pos:
        window_size = window.size()
        centered_pos = (
            pos.x() -window_size.width()/2,
            pos.y() -window_size.height()/2,
        )

        window.move(*centered_pos)
