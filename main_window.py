import sys
import os
from datetime import datetime, timedelta
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt, QFile, QIODevice, QSize
from PySide6.QtWidgets import (
    QMainWindow,
    QApplication,
    QFileDialog,
    QMenu,
    QMessageBox,
    QSpinBox,
)
from matplotlib import use as matplotlib_backend_use
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
from ionogram_tester import IonogramTester
from ui_MainWnd import Ui_mainWindow
from remote_window import RemoteWindow
from file_navigator import FileNavigator
from std_file_format import STDFileIO
from json_file_format import JsonFileIO
from ionospheric_layer_trace import IonosphericLayerTrace, IonosphericLayers
from program_version import PROGRAM_VERSION

DATE_TIME_FORMAT = "yyyy-MM-dd hh:mm"


class MainWindow(QMainWindow, Ui_mainWindow):

    def __init__(self, program_configuration):

        super().__init__()

        matplotlib_backend_use("agg")

        self.program_name = f"IonogramViewer2 v{PROGRAM_VERSION}"
        self.file_name = ""
        self.iono = None
        self.ax = None
        self.f2_scatter = None
        self.f1_scatter = None
        self.e_scatter = None
        self.es_scatter = None
        self.f2_critical = None
        self.f1_critical = None
        self.e_critical = None
        self.es_critical = None
        self.f2_min = None
        self.f1_min = None
        self.e_min = None

        self.im_iono = None

        self.F2_COLOR = "#F51020"
        self.F1_COLOR = "#10E0E0"
        self.E_COLOR = "#10C010"
        self.ES_COLOR = "#F0B000"

        self.setupUi(self)

        self.repair_icons()

        self.level_spin_box = QSpinBox()
        self.level_spin_box.setSuffix("%")
        self.level_spin_box.setRange(10, 100)
        self.level_spin_box.setValue(100)
        self.level_spin_box.setToolTip("Level (from 10 to 100%)")
        self.toolBar.addWidget(self.level_spin_box)

        self.connect_actions()

        self.change_mode(0)  # F2

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.horizontalLayout.addWidget(self.canvas)
        self.is_cross = False
        self.canvas.mpl_connect("button_press_event", self.onclick)
        self.canvas.mpl_connect("motion_notify_event", self.onmove)

        traces_list_widgets = [
            self.listWidgetE,
            self.listWidgetF1,
            self.listWidgetF2,
            self.listWidgetEs,
        ]
        for w in traces_list_widgets:
            w.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            w.customContextMenuRequested.connect(self.delete_menu)

        items = [f"{i:>+3d}" if i != 0 else f"{i:>3d}" for i in range(-11, 13)]
        self.timeZoneComboBox.addItems(items)
        font = QFont("Monospace")
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        self.timeZoneComboBox.setFont(font)

        self.properties_of_iono = [
            self.stationNameEdit,
            self.timeZoneComboBox,
            self.dateTimeEdit,
            self.latLineEdit,
            self.longLineEdit,
            self.sunspotNumberLineEdit,
            self.gyrofrequencyLineEdit,
            self.dipAngleLineEdit,
        ]

        self.dateTimeEdit.setDisplayFormat(DATE_TIME_FORMAT)

        self.clear_all()

        self.setWindowTitle(self.program_name)

        self.showMaximized()

        self.setAcceptDrops(True)

        self.toolBar.removeAction(self.action_ANN)

        if len(sys.argv) == 2:
            self.open_file(sys.argv[1])

    def connect_actions(self):
        actions = {
            self.actionExit: self.close_window,
            self.actionOpen: self.open_file_dialog,
            self.actionSave: self.save_file,
            self.actionAbout: self.show_about,
            self.actionNext: self.open_next_file,
            self.actionPrevious: self.open_prev_file,
            self.actionFirst: self.open_first_file,
            self.actionLast: self.open_last_file,
            self.actionReload: self.reopen_file,
            self.actionChangeLayer: self.change_layer,
            self.actionClose: self.close_file,
            self.actionClean: self.clean_ionogram,
            self.actionMoveLeft: self.move_left,
            self.actionMoveRight: self.move_right,
            self.actionO_trace: self.action_ox_traces,
            self.actionX_trace: self.action_ox_traces,
            self.action_ANN: self.auto_scale,
        }
        for key, action in actions.items():
            key.triggered.connect(action)

        spin_boxes = (
            self.doubleSpinBoxF2,
            self.doubleSpinBoxF1,
            self.doubleSpinBoxE,
            self.doubleSpinBoxEs,
        )
        for w in spin_boxes:
            w.valueChanged.connect(self.critical_frequency_spin_box_change)

        clear_buttons = (
            self.buttonClearF2,
            self.buttonClearF1,
            self.buttonClearE,
            self.buttonClearEs,
        )
        for b in clear_buttons:
            b.clicked.connect(self.clear_frequency)

        self.radioButtonF2.toggled.connect(lambda: self.change_mode(0))
        self.radioButtonF1.toggled.connect(lambda: self.change_mode(1))
        self.radioButtonE.toggled.connect(lambda: self.change_mode(2))
        self.radioButtonEs.toggled.connect(lambda: self.change_mode(3))

        self.pngDefaultButton.clicked.connect(self.set_default_image_param)
        self.pngCheckBox.stateChanged.connect(self.png_state_changed)

        self.actionRemote.triggered.connect(self.remote)

        self.level_spin_box.valueChanged.connect(self.scale_change)

    def close_window(self):
        sys.exit()

    def repair_icons(self):

        def get_resource_path(filename):
            return os.path.join(os.path.dirname(__file__), filename)

        actions = {
            self.actionExit: "images/application-exit.png",
            self.actionOpen: "images/document-open.png",
            self.actionHelp: "images/help-contents.png",
            self.actionSave: "images/document-save-as.png",
            self.actionAbout: "images/help-about.png",
            self.actionNext: "images/go-next.png",
            self.actionPrevious: "images/go-next-rtl.png",
            self.actionFirst: "images/go-first.png",
            self.actionLast: "images/go-last.png",
            self.actionReload: "images/view-refresh.png",
            self.actionRemote: "images/folder-remote.png",
            self.actionClean: "images/Gartoon-Team-Gartoon-Action-Edit-clear-broom.24.png",
            self.actionMoveLeft: "images/icons8-open-pane-24.png",
            self.actionMoveRight: "images/icons8-close-pane-24.png",
            self.actionO_trace: "images/o-trace.png",
            self.actionX_trace: "images/x-trace.png",
            self.actionIgnore_errors: "images/Martz90-Circle-Addon2-Warning.24.png",
            self.buttonClearF1: "images/icons8-close-16.png",
            self.buttonClearF2: "images/icons8-close-16.png",
            self.buttonClearE: "images/icons8-close-16.png",
            self.buttonClearEs: "images/icons8-close-16.png",
        }

        for key, value in actions.items():
            icon = QIcon()
            icon.addFile(
                get_resource_path(value),
                QSize(),
                QIcon.Mode.Normal,
                QIcon.State.Off,
            )
            key.setIcon(icon)

    def _check_spin_box(self, spin_box, value):
        if not self.iono:
            return

        f_start = self.iono.coord_to_freq(self.iono.get_extent()[0])
        if value < f_start:
            spin_box.setValue(0)
        self.plot_lines(0)

    def critical_frequency_spin_box_change(self, value):
        if self.mode == 0:  # F2
            self._check_spin_box(self.doubleSpinBoxF2, value)
        elif self.mode == 1:  # F1
            self._check_spin_box(self.doubleSpinBoxF1, value)
        elif self.mode == 2:  # E
            self._check_spin_box(self.doubleSpinBoxE, value)
        elif self.mode == 3:  # Es
            self._check_spin_box(self.doubleSpinBoxEs, value)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        first_file = files[0]
        if not os.path.isdir(first_file):
            self.open_file(first_file)

    def clear_frequency(self):
        if self.mode == 0:  # F2
            self.doubleSpinBoxF2.setValue(0)

        elif self.mode == 1:  # F1
            self.doubleSpinBoxF1.setValue(0)

        elif self.mode == 2:  # E
            self.doubleSpinBoxE.setValue(0)

        elif self.mode == 3:  # Es
            self.doubleSpinBoxEs.setValue(0)

    def move_left(self):

        if self.iono:
            gyro_2 = self.get_value(self.gyrofrequencyLineEdit) / 2

            if self.mode == 0:  # F2
                f = self.doubleSpinBoxF2.value() - gyro_2
                if f >= self.iono.coord_to_freq(self.iono.get_extent()[0]):
                    self.doubleSpinBoxF2.setValue(f)

            elif self.mode == 1:  # F1
                f = self.doubleSpinBoxF1.value() - gyro_2
                if f >= self.iono.coord_to_freq(self.iono.get_extent()[0]):
                    self.doubleSpinBoxF1.setValue(f)

            elif self.mode == 2:  # E
                f = self.doubleSpinBoxE.value() - gyro_2
                if f >= self.iono.coord_to_freq(self.iono.get_extent()[0]):
                    self.doubleSpinBoxE.setValue(f)

            elif self.mode == 3:  # Es
                f = self.doubleSpinBoxEs.value() - gyro_2
                if f >= self.iono.coord_to_freq(self.iono.get_extent()[0]):
                    self.doubleSpinBoxEs.setValue(f)

    def move_right(self):

        if self.iono:
            gyro_2 = self.get_value(self.gyrofrequencyLineEdit) / 2

            if self.mode == 0 and self.doubleSpinBoxF2.value():  # F2
                f = self.doubleSpinBoxF2.value() + gyro_2
                if f <= self.iono.coord_to_freq(self.iono.get_extent()[1] - 1):
                    self.doubleSpinBoxF2.setValue(f)

            elif self.mode == 1 and self.doubleSpinBoxF1.value():  # F1
                f = self.doubleSpinBoxF1.value() + gyro_2
                if f <= self.iono.coord_to_freq(self.iono.get_extent()[1] - 1):
                    self.doubleSpinBoxF1.setValue(f)

            elif self.mode == 2 and self.doubleSpinBoxE.value():  # E
                f = self.doubleSpinBoxE.value() + gyro_2
                if f <= self.iono.coord_to_freq(self.iono.get_extent()[1] - 1):
                    self.doubleSpinBoxE.setValue(f)

            elif self.mode == 3 and self.doubleSpinBoxEs.value():  # Es
                f = self.doubleSpinBoxEs.value() + gyro_2
                if f <= self.iono.coord_to_freq(self.iono.get_extent()[1] - 1):
                    self.doubleSpinBoxEs.setValue(f)

    def scale_change(self):
        if self.iono:
            self.im_iono.set_clim(
                vmax=np.max(self.iono.get_data()) * self.level_spin_box.value() / 100,
                vmin=np.min(self.iono.get_data()) * self.level_spin_box.value() / 100,
            )
            self.figure.canvas.draw()

    def clean_ionogram(self):

        if self.iono:
            self.iono.clean_ionogram()

            self.im_iono.set_data(self.iono.get_data())

            self.im_iono.set_clim(
                vmin=np.min(self.iono.get_data()), vmax=np.max(self.iono.get_data())
            )
            self.figure.canvas.draw()

    def remote(self):
        wnd = RemoteWindow()
        wnd.exec()

    def png_state_changed(self, state):
        s = state == Qt.CheckState.Checked
        elements = [
            self.pngDefaultButton,
            self.pngWidthSpinBox,
            self.pngHeightSpinBox,
            self.pngDpiSpinBox,
        ]
        for e in elements:
            e.setEnabled(s)

    def set_default_image_param(self):
        self.pngDpiSpinBox.setValue(100)
        self.pngWidthSpinBox.setValue(10)
        self.pngHeightSpinBox.setValue(6)

    def change_layer(self):
        mode = self.mode + 1 if self.mode < 3 else 0
        if mode == 0:
            self.radioButtonF2.setChecked(True)
        elif mode == 1:
            self.radioButtonF1.setChecked(True)
        elif mode == 2:
            self.radioButtonE.setChecked(True)
        elif mode == 3:
            self.radioButtonEs.setChecked(True)

    def clear_all(self):
        self.e_scatter = None
        self.f1_scatter = None
        self.f2_scatter = None
        self.es_scatter = None

        self.e_critical = None
        self.f1_critical = None
        self.f2_critical = None
        self.es_critical = None

        self.e_min = None
        self.f1_min = None
        self.f2_min = None

        self.iono = None
        self.file_name = None

        self.change_mode(0)

        self.doubleSpinBoxF2.setValue(0)
        self.doubleSpinBoxF1.setValue(0)
        self.doubleSpinBoxE.setValue(0)
        self.doubleSpinBoxEs.setValue(0)

        self.listWidgetE.clear()
        self.listWidgetF1.clear()
        self.listWidgetF2.clear()
        self.listWidgetEs.clear()

        self.radioButtonF2.setChecked(True)
        _ = [e.setEnabled(False) for e in self.properties_of_iono]

    def delete_menu(self, point):
        if self.sender().count():
            list_menu = QMenu()
            delete_action = list_menu.addAction("Delete")
            delete_all_action = list_menu.addAction("Delete all")
            point_global = self.sender().mapToGlobal(point)
            r = list_menu.exec(point_global)
            if r is delete_action:
                item = self.sender().row(self.sender().itemAt(point))
                self.sender().takeItem(item)
            elif r is delete_all_action:
                self.sender().clear()
            self.plot_scatters()

    def change_mode(self, mode):
        self.mode = mode

        widgets = [
            self.doubleSpinBoxE,
            self.doubleSpinBoxF1,
            self.doubleSpinBoxF2,
            self.doubleSpinBoxEs,
            self.listWidgetE,
            self.listWidgetF1,
            self.listWidgetF2,
            self.listWidgetEs,
            self.buttonClearF2,
            self.buttonClearF1,
            self.buttonClearE,
            self.buttonClearEs,
        ]
        for w in widgets:
            w.setEnabled(False)

        if mode == 0:
            self.doubleSpinBoxF2.setEnabled(True)
            self.listWidgetF2.setEnabled(True)
            self.buttonClearF2.setEnabled(True)
        elif mode == 1:
            self.doubleSpinBoxF1.setEnabled(True)
            self.listWidgetF1.setEnabled(True)
            self.buttonClearF1.setEnabled(True)
        elif mode == 2:
            self.doubleSpinBoxE.setEnabled(True)
            self.listWidgetE.setEnabled(True)
            self.buttonClearE.setEnabled(True)
        elif mode == 3:
            self.doubleSpinBoxEs.setEnabled(True)
            self.listWidgetEs.setEnabled(True)
            self.buttonClearEs.setEnabled(True)

    def onclick(self, event):
        if event.ydata and event.xdata:
            f = round(self.iono.coord_to_freq(event.xdata), 2)
            h = event.ydata
            s = f"{f:5.2f} {h:5.1f}"

            modifiers = QApplication.keyboardModifiers()

            if event.button == 1:

                widgets = {
                    0: self.listWidgetF2,
                    1: self.listWidgetF1,
                    2: self.listWidgetE,
                    3: self.listWidgetEs,
                }
                widget = widgets[self.mode]

                if modifiers == Qt.KeyboardModifier.ControlModifier:

                    def find_closest_point_index(new_point, points):
                        points = np.array(points)
                        distances = np.linalg.norm(points - new_point, axis=1)
                        index = np.argmin(distances)
                        return index

                    layer_lines = [widget.item(i).text() for i in range(widget.count())]
                    if layer_lines:
                        points = [[float(v) for v in x.split()] for x in layer_lines]
                        point_index = find_closest_point_index([f, h], points)
                        if (
                            abs(f - points[point_index][0]) < 0.05
                            and abs(h - points[point_index][1]) < 5
                        ):
                            widget.takeItem(point_index)

                else:
                    widget.addItem(s)

            elif event.button == 3:

                # subract half of hyrofrequency if Shift key is pressed
                if modifiers == Qt.KeyboardModifier.ShiftModifier:
                    f = round(
                        self.iono.coord_to_freq(event.xdata)
                        - self.get_value(self.gyrofrequencyLineEdit) / 2,
                        2,
                    )

                widgets = {
                    0: self.doubleSpinBoxF2,
                    1: self.doubleSpinBoxF1,
                    2: self.doubleSpinBoxE,
                    3: self.doubleSpinBoxEs,
                }
                widget = widgets[self.mode]
                widget.setValue(f)

            self.plot_scatters()

    def plot_scatters(self):
        if self.e_scatter is not None:
            self.e_scatter.remove()

        x_e = []
        y_e = []
        for i in range(self.listWidgetE.count()):
            t = self.listWidgetE.item(i).text().split()
            x_e.append(self.iono.freq_to_coord(t[0]))
            y_e.append(float(t[1]))
        self.e_scatter = self.ax.scatter(x_e, y_e, c=self.E_COLOR)

        if self.f1_scatter is not None:
            self.f1_scatter.remove()

        x_f1 = []
        y_f1 = []
        for i in range(self.listWidgetF1.count()):
            t = self.listWidgetF1.item(i).text().split()
            x_f1.append(self.iono.freq_to_coord(t[0]))
            y_f1.append(float(t[1]))
        self.f1_scatter = self.ax.scatter(x_f1, y_f1, c=self.F1_COLOR)

        if self.f2_scatter is not None:
            self.f2_scatter.remove()

        x_f2 = []
        y_f2 = []
        for i in range(self.listWidgetF2.count()):
            t = self.listWidgetF2.item(i).text().split()
            x_f2.append(self.iono.freq_to_coord(t[0]))
            y_f2.append(float(t[1]))
        self.f2_scatter = self.ax.scatter(x_f2, y_f2, c=self.F2_COLOR)

        if self.es_scatter is not None:
            self.es_scatter.remove()

        x_es = []
        y_es = []
        for i in range(self.listWidgetEs.count()):
            t = self.listWidgetEs.item(i).text().split()
            x_es.append(self.iono.freq_to_coord(t[0]))
            y_es.append(float(t[1]))
        self.es_scatter = self.ax.scatter(x_es, y_es, c=self.ES_COLOR)

        self.canvas.draw()

    def plot_lines(self, value):

        if self.iono is None:
            return

        left = self.iono.get_extent()[0]
        right = self.iono.get_extent()[1]
        top = self.iono.get_extent()[3]
        bottom = self.iono.get_extent()[2]

        def plot_line(box, line, color, style="-"):
            if line is not None:
                line.remove()
                line = None
            freq = box.value()
            if freq > 0:
                f = self.iono.freq_to_coord(freq)
                if left < f < right:
                    (line,) = self.ax.plot(
                        [f, f], [bottom, top], c=color, linestyle=style
                    )
                return line

        self.f2_critical = plot_line(
            self.doubleSpinBoxF2, self.f2_critical, self.F2_COLOR
        )
        self.f1_critical = plot_line(
            self.doubleSpinBoxF1, self.f1_critical, self.F1_COLOR
        )
        self.e_critical = plot_line(self.doubleSpinBoxE, self.e_critical, self.E_COLOR)

        self.es_critical = plot_line(
            self.doubleSpinBoxEs, self.es_critical, self.ES_COLOR
        )

        self.canvas.draw()

    def onmove(self, event):
        if event.ydata and event.xdata:
            f = self.iono.coord_to_freq(event.xdata)
            h = event.ydata
            self.statusbar.showMessage(f"f={f:5.2f}  h'={h:5.1f}")
            if not self.is_cross:
                QApplication.setOverrideCursor(Qt.CursorShape.CrossCursor)
                self.is_cross = True
        else:
            self.statusbar.showMessage("")
            if self.is_cross:
                QApplication.restoreOverrideCursor()
                self.is_cross = False

    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self)
        if file_name:
            self.open_file(file_name)

    def close_file(self):
        self.clear_all()
        self.iono = None
        self.file_name = ""
        self.figure.clear()
        self.ax = None
        self.canvas.draw()
        self.actionO_trace.setEnabled(False)
        self.actionX_trace.setEnabled(False)

    def open_file(self, file_name):
        tester = IonogramTester()
        is_iono = tester.examine(file_name)
        if is_iono:
            self.close_file()
            self.file_navigator = FileNavigator(file_name)
            self.iono = tester.get_iono()
            self.iono.load(file_name)
            data = self.iono.get_data()
            if data is not None:

                self.file_name = file_name

                self.ax = self.figure.add_subplot(111)

                extent = self.iono.get_extent()

                self.im_iono = self.ax.imshow(
                    data,
                    cmap=self.iono.cmap,
                    interpolation="nearest",
                    extent=extent,
                    aspect="auto",
                    vmax=np.max(self.iono.get_data())
                    * self.level_spin_box.value()
                    / 100,
                    vmin=np.min(self.iono.get_data())
                    * self.level_spin_box.value()
                    / 100,
                )

                tics = self.iono.get_freq_tics()
                labels = self.iono.get_freq_labels()
                self.ax.set_xticks(tics)
                self.ax.set_xticklabels(labels)

                plt.tight_layout()
                self.setWindowTitle(f"{self.program_name} - {file_name}")
                self.canvas.draw()

                self.stationNameEdit.setText(self.iono.get_station_name())
                self.dateTimeEdit.setDateTime(self.iono.get_date())
                self.latLineEdit.setText(str(self.iono.get_lat()))
                self.longLineEdit.setText(str(self.iono.get_lon()))
                self.gyrofrequencyLineEdit.setText(str(self.iono.get_gyro()))
                self.dipAngleLineEdit.setText(str(self.iono.get_dip()))

                sunspot = self.iono.get_sunspot()
                if sunspot != -1:
                    self.sunspotNumberLineEdit.setText(str(sunspot))
                else:
                    self.sunspotNumberLineEdit.setText("")
                    if not self.actionIgnore_errors.isChecked():
                        error_message = """
                        Sunspot number is not found.<br><br>
                        File <b>SN_d_tot_V2.0.txt</b> is probably outdated.<br>
                        Please update it from<br>
                        <a href='http://www.sidc.be/silso/DATA/SN_d_tot_V2.0.txt'>http://www.sidc.be/silso/DATA/SN_d_tot_V2.0.txt</a>
                        """
                        self.show_error(error_message)

                time_zone = self.iono.get_timezone()
                position = self.timeZoneComboBox.findText(
                    f"{time_zone:>+3d}" if time_zone != 0 else f"{time_zone:>3d}"
                )
                self.timeZoneComboBox.setCurrentIndex(position)
                _ = [e.setEnabled(True) for e in self.properties_of_iono]

                self.load_text_info()

                self.plot_scatters()

                self.actionO_trace.setChecked(True)
                self.actionX_trace.setChecked(True)

                if self.iono.ox_mode:
                    self.actionO_trace.setEnabled(True)
                    self.actionX_trace.setEnabled(True)
                else:
                    self.actionO_trace.setEnabled(False)
                    self.actionX_trace.setEnabled(False)
        else:
            self.show_error("File format is not supported.")

    def open_next_file(self):
        if self.file_name:
            self.open_file(self.file_navigator.next())

    def open_prev_file(self):
        if self.file_name:
            self.open_file(self.file_navigator.previous())

    def open_last_file(self):
        if self.file_name:
            self.open_file(self.file_navigator.last())

    def open_first_file(self):
        if self.file_name:
            self.open_file(self.file_navigator.first())

    def reopen_file(self):
        if self.file_name:
            self.open_file(self.file_name)

    def load_text_info(self):
        if not self.load_json():
            self.load_std()

    def load_json(self):
        json_data = JsonFileIO.load(f"{self.file_name}.json")

        if not json_data:
            return False

        date = self.iono.date - timedelta(hours=self.iono.timezone)

        current_data = json_data[date.isoformat()]

        self.iono.station_name = current_data["station_name"]
        self.iono.lat = current_data["latitude"]
        self.iono.lon = current_data["longitude"]
        self.iono.gyro = current_data["gyro"]
        self.iono.dip = current_data["dip"]
        self.iono.sunspot = current_data["sunspot"]
        self.iono.date = datetime.fromisoformat(current_data["date"])
        self.iono.timezone = current_data["timezone"]

        self._update_parameters()

        traces = current_data["traces"]
        foe, e_layer_points = JsonFileIO.get_trace_points(
            IonosphericLayers.E_LAYER, traces
        )

        foes, es_layer_points = JsonFileIO.get_trace_points(
            IonosphericLayers.ES_LAYER, traces
        )

        fof1, f1_layer_points = JsonFileIO.get_trace_points(
            IonosphericLayers.F1_LAYER, traces
        )
        fof2, f2_layer_points = JsonFileIO.get_trace_points(
            IonosphericLayers.F2_LAYER, traces
        )

        if foe:
            self.doubleSpinBoxE.setValue(foe)
            for point in e_layer_points:
                f = float(point.split()[0])
                h = float(point.split()[1])
                line = f"{f:-5.2f} {h:-5.1f}"
                self.listWidgetE.addItem(line)

        if foes:
            self.doubleSpinBoxEs.setValue(foes)
            for point in es_layer_points:
                f = float(point.split()[0])
                h = float(point.split()[1])
                line = f"{f:-5.2f} {h:-5.1f}"
                self.listWidgetEs.addItem(line)

        if fof1:
            self.doubleSpinBoxF1.setValue(fof1)
            for point in f1_layer_points:
                f = float(point.split()[0])
                h = float(point.split()[1])
                line = f"{f:-5.2f} {h:-5.1f}"
                self.listWidgetF1.addItem(line)

        if fof2:
            self.doubleSpinBoxF2.setValue(fof2)
            for point in f2_layer_points:
                f = float(point.split()[0])
                h = float(point.split()[1])
                line = f"{f:-5.2f} {h:-5.1f}"
                self.listWidgetF2.addItem(line)

        return True

    def _update_parameters(self):
        self.stationNameEdit.setText(self.iono.get_station_name())
        self.latLineEdit.setText(str(self.iono.lat))
        self.longLineEdit.setText(str(self.iono.lon))
        self.gyrofrequencyLineEdit.setText(str(self.iono.gyro))
        self.dipAngleLineEdit.setText(str(self.iono.dip))
        self.sunspotNumberLineEdit.setText(str(self.iono.sunspot))
        self.dateTimeEdit.setDateTime(self.iono.get_date())

    def load_std(self):
        std_info = STDFileIO.load(f"{self.file_name}.STD")

        if not std_info:
            return False

        self.iono.station_name = std_info["station_name"]
        self.iono.lat = std_info["latitude"]
        self.iono.lon = std_info["longitude"]
        self.iono.gyro = std_info["gyro"]
        self.iono.dip = std_info["dip"]
        self.iono.sunspot = std_info["sunspot"]
        self.iono.date = std_info["date"]
        self.iono.timezone = std_info["timezone"]

        self._update_parameters()

        timezone = self.iono.get_timezone()
        position = self.timeZoneComboBox.findText(
            f"{timezone:>+3d}" if timezone != 0 else f"{timezone:>3d}"
        )
        self.timeZoneComboBox.setCurrentIndex(position)

        traces = std_info["traces"]

        foe, e_layer_points = STDFileIO.get_trace_points(
            IonosphericLayers.E_LAYER, traces
        )
        fof1, f1_layer_points = STDFileIO.get_trace_points(
            IonosphericLayers.F1_LAYER, traces
        )
        fof2, f2_layer_points = STDFileIO.get_trace_points(
            IonosphericLayers.F2_LAYER, traces
        )

        if foe:
            self.doubleSpinBoxE.setValue(foe)
            for point in e_layer_points:
                f = float(point.split()[0])
                h = float(point.split()[1])
                line = f"{f:-5.2f} {h:-5.1f}"
                self.listWidgetE.addItem(line)

        if fof1:
            self.doubleSpinBoxF1.setValue(fof1)
            for point in f1_layer_points:
                f = float(point.split()[0])
                h = float(point.split()[1])
                line = f"{f:-5.2f} {h:-5.1f}"
                self.listWidgetF1.addItem(line)

        if fof2:
            self.doubleSpinBoxF2.setValue(fof2)
            for point in f2_layer_points:
                f = float(point.split()[0])
                h = float(point.split()[1])
                line = f"{f:-5.2f} {h:-5.1f}"
                self.listWidgetF2.addItem(line)

        return True

    def save_json(self):

        self._prepare_ionogram_parameters()

        e_layer = self._prepare_trace_data(
            IonosphericLayers.E_LAYER, self.doubleSpinBoxE, self.listWidgetE
        )
        es_layer = self._prepare_trace_data(
            IonosphericLayers.ES_LAYER, self.doubleSpinBoxEs, self.listWidgetEs
        )
        f1_layer = self._prepare_trace_data(
            IonosphericLayers.F1_LAYER, self.doubleSpinBoxF1, self.listWidgetF1
        )
        f2_layer = self._prepare_trace_data(
            IonosphericLayers.F2_LAYER, self.doubleSpinBoxF2, self.listWidgetF2
        )

        JsonFileIO.save(
            f"{self.file_name}.json", self.iono, [e_layer, es_layer, f1_layer, f2_layer]
        )

    def save_file(self):
        if self.file_name:

            if self.jsonCheckBox.isChecked():
                self.save_json()

            if self.stdCheckBox.isChecked():
                self.save_std()

            if self.pngCheckBox.isChecked():
                width = self.pngWidthSpinBox.value()
                height = self.pngHeightSpinBox.value()
                dpi = self.pngDpiSpinBox.value()
                self.save_image(
                    f"{self.file_name}.png", width=width, height=height, dpi=dpi
                )
            self.statusbar.showMessage("File is saved.")

    def get_value(self, widget):
        value = 0
        try:
            value = float(widget.text().strip())
        except ValueError:
            pass
        return value

    def _prepare_trace_data(
        self, trace_name, critical_frequency_spin_box, trace_list_widget
    ):
        critical_frequency = critical_frequency_spin_box.value()
        layer_lines = [
            trace_list_widget.item(i).text() for i in range(trace_list_widget.count())
        ]
        freqs = [float(x.split()[0]) for x in layer_lines]
        heights = [float(x.split()[1]) for x in layer_lines]
        layer = IonosphericLayerTrace(trace_name, freqs, heights, critical_frequency)
        return layer

    def _prepare_ionogram_parameters(self):
        self.iono.station_name = self.stationNameEdit.text()
        self.iono.lat = self.get_value(self.latLineEdit)
        self.iono.lon = self.get_value(self.longLineEdit)
        self.iono.gyro = self.get_value(self.gyrofrequencyLineEdit)
        self.iono.dip = self.get_value(self.dipAngleLineEdit)
        self.iono.sunspot = self.get_value(self.sunspotNumberLineEdit)
        self.iono.date = datetime.strptime(self.dateTimeEdit.text(), "%Y-%m-%d %H:%M")
        self.iono.timezone = int(self.timeZoneComboBox.currentText().strip())

    def save_std(self):
        self._prepare_ionogram_parameters()

        e_layer = self._prepare_trace_data(
            IonosphericLayers.E_LAYER, self.doubleSpinBoxE, self.listWidgetE
        )
        f1_layer = self._prepare_trace_data(
            IonosphericLayers.F1_LAYER, self.doubleSpinBoxF1, self.listWidgetF1
        )
        f2_layer = self._prepare_trace_data(
            IonosphericLayers.F2_LAYER, self.doubleSpinBoxF2, self.listWidgetF2
        )

        STDFileIO.save(
            f"{self.file_name}.STD", self.iono, [e_layer, f1_layer, f2_layer]
        )

    def save_image(self, filename, **kwargs):
        width = 10 if "width" not in kwargs else kwargs["width"]
        height = 6 if "height" not in kwargs else kwargs["height"]
        dpi = 100 if "dpi" not in kwargs else kwargs["dpi"]
        old_size = self.figure.get_size_inches()
        self.figure.set_size_inches(width, height)
        plt.title(self.get_description())
        plt.tight_layout()
        self.figure.savefig(filename, dpi=dpi)
        plt.title("")
        self.figure.set_size_inches(old_size)
        plt.tight_layout()
        self.canvas.draw()

    def get_description(self):
        time_zone = self.timeZoneComboBox.currentText().strip()
        date_str = self.dateTimeEdit.dateTime().toString(DATE_TIME_FORMAT)
        utc_str = "UTC" if time_zone == "0" else "UTC" + time_zone
        station_name = self.stationNameEdit.text().strip()

        description = f"{station_name}, {date_str} ({utc_str})"

        fof2 = self.doubleSpinBoxF2.value()
        fof1 = self.doubleSpinBoxF1.value()
        foe = self.doubleSpinBoxE.value()
        foes = self.doubleSpinBoxEs.value()

        fof2 = f"foF2 = {fof2:.2f} MHz   " if fof2 else ""
        fof1 = f"foF1 = {fof1:.2f} MHz   " if fof1 else ""
        foe = f"foE = {foe:.2f} MHz   " if foe else ""
        foes = f"foEs = {foes:.2f} MHz" if foes else ""

        if fof2 or fof1 or foe or foes:
            description += f"\n{fof2}{fof1}{foe}{foes}"

        return description

    def action_ox_traces(self):
        data = np.copy(self.iono.get_data())

        if not self.actionO_trace.isChecked():
            data[data > 0] = 0

        if not self.actionX_trace.isChecked():
            data[data < 0] = 0

        self.im_iono.set_data(data)

        self.figure.canvas.draw()

    def show_error(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(message)
        msg.setWindowTitle("Error")
        msg.show()
        msg.exec()

    def show_about(self):
        about = f"""<b>{self.program_name}</b>
                     <br><br>
                     Source code on GitHub:<br>
                     <a href="https://github.com/Albom/IonogramViewer2">https://github.com/Albom/IonogramViewer2</a><br>
                     <br>
                     <br>
                     © 2018-2025 Oleksandr Bogomaz<br>
                     o.v.bogomaz1985@gmail.com<br>
                 """

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(about)
        msg.setWindowTitle("About")
        msg.show()
        msg.exec()

    def auto_scale(self):
        print("ANN")
