import sys
from os import path
from datetime import datetime, timedelta
import re
from PyQt6 import uic
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QFileDialog,
    QMenu,
    QMessageBox,
    QDialog,
)
from matplotlib import use as matplotlib_backend_use
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import numpy as np


import_error = None

try:
    from visrc2t_iono import Visrc2tIono
    from shigaraki_loader import ShigarakiLoader
    from filelist import FileList
    from shigaraki_iono import ShigarakiIono
    from dps_amp_iono import DpsAmpIono
    from ips42_iono import Ips42Iono
    from bazis_iono import BazisIono
    from rinan_iono import RinanIono
    from karazin_iono import KarazinIono
    from iono_tester import IonoTester
except ModuleNotFoundError as err:
    quoted = re.compile('"[^"]*"')
    search_result = quoted.findall(str(err).replace("'", '"'))
    if search_result:
        if search_result[0].replace('"', "") == "cv2":
            import_error = """
            OpenCV is not installed.<br><br>
            You can install it by:<br>
            <b>pip install opencv-python</b>
            """
        else:
            import_error = str(err)


DATE_TIME_FORMAT = "yyyy-MM-dd hh:mm"


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.program_name = "IonogramViewer2 v1.6.4"
        self.file_name = ""
        self.iono = None
        self.ax = None
        self.f2_scatter = None
        self.f1_scatter = None
        self.e_scatter = None
        self.f2_critical = None
        self.f1_critical = None
        self.e_critical = None
        self.f2_min = None
        self.f1_min = None
        self.e_min = None

        self.im_iono = None

        self.F2_COLOR = "#f51020"
        self.F1_COLOR = "#10f0f0"
        self.E_COLOR = "#10c020"

        uic.loadUi("./ui/MainWnd.ui", self)

        actions = {
            self.actionExit: sys.exit,
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
        }
        for key, action in actions.items():
            key.triggered.connect(action)

        self.change_mode(0)  # F2
        self.radioButtonF2.toggled.connect(lambda: self.change_mode(0))
        self.radioButtonF1.toggled.connect(lambda: self.change_mode(1))
        self.radioButtonE.toggled.connect(lambda: self.change_mode(2))

        self.pngDefaultButton.clicked.connect(self.set_default_image_param)
        self.pngCheckBox.stateChanged.connect(self.png_state_changed)

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.horizontalLayout.addWidget(self.canvas)
        self.is_cross = False
        self.canvas.mpl_connect("button_press_event", self.onclick)
        self.canvas.mpl_connect("motion_notify_event", self.onmove)

        listWidgets = [self.listWidgetE, self.listWidgetF1, self.listWidgetF2]
        for w in listWidgets:
            w.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            w.customContextMenuRequested.connect(self.delete_menu)

        spinBoxes = [self.doubleSpinBoxF2, self.doubleSpinBoxF1, self.doubleSpinBoxE]
        for w in spinBoxes:
            w.valueChanged.connect(self.plot_lines)

        clear_buttons = [self.buttonClearF2, self.buttonClearF1, self.buttonClearE]
        for b in clear_buttons:
            b.clicked.connect(self.clear_frequency)

        items = [
            str.format("{:>+3d}" if i != 0 else "{:>3d}", i) for i in range(-11, 13)
        ]
        self.timeZoneComboBox.addItems(items)
        font = QFont("Monospace")
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        self.timeZoneComboBox.setFont(font)

        self.properties_of_iono = [
            self.stationNameEdit,
            self.timeZoneComboBox,
            self.ursiCodeEdit,
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

        self.actionRemote.triggered.connect(self.remote)

        self.showMaximized()

        self.setAcceptDrops(True)

        if import_error is not None:
            self.show_error(import_error)
            sys.exit(0)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        first_file = files[0]
        if not path.isdir(first_file):
            self.open_file(first_file)

    def clear_frequency(self):
        if self.mode == 0:  # F2
            self.doubleSpinBoxF2.setValue(0)

        elif self.mode == 1:  # F1
            self.doubleSpinBoxF1.setValue(0)

        elif self.mode == 2:  # E
            self.doubleSpinBoxE.setValue(0)

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

    def clean_ionogram(self):

        if self.iono:
            self.iono.clean_ionogram()

            self.im_iono.set_data(self.iono.get_data())

            self.im_iono.set_clim(
                vmin=np.min(self.iono.get_data()), vmax=np.max(self.iono.get_data())
            )
            self.figure.canvas.draw()

    def remote(self):
        wnd = RemoteWnd()
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
        mode = self.mode + 1 if self.mode < 2 else 0
        if mode == 0:
            self.radioButtonF2.setChecked(True)
        elif mode == 1:
            self.radioButtonF1.setChecked(True)
        elif mode == 2:
            self.radioButtonE.setChecked(True)

    def clear_all(self):
        self.e_scatter = None
        self.f1_scatter = None
        self.f2_scatter = None

        self.e_critical = None
        self.f1_critical = None
        self.f2_critical = None

        self.e_min = None
        self.f1_min = None
        self.f2_min = None

        self.iono = None
        self.file_name = None

        self.change_mode(0)

        self.doubleSpinBoxF2.setValue(0)
        self.doubleSpinBoxF1.setValue(0)
        self.doubleSpinBoxE.setValue(0)

        self.listWidgetE.clear()
        self.listWidgetF1.clear()
        self.listWidgetF2.clear()

        self.radioButtonF2.setChecked(True)
        _ = [e.setEnabled(False) for e in self.properties_of_iono]

    def delete_menu(self, point):
        if self.sender().count():
            listMenu = QMenu()
            delete_action = listMenu.addAction("Delete")
            delete_all_action = listMenu.addAction("Delete all")
            point_global = self.sender().mapToGlobal(point)
            r = listMenu.exec(point_global)
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
            self.listWidgetE,
            self.listWidgetF1,
            self.listWidgetF2,
            self.buttonClearF2,
            self.buttonClearF1,
            self.buttonClearE,
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

    def onclick(self, event):
        if event.ydata and event.xdata:
            f = round(self.iono.coord_to_freq(event.xdata), 2)
            h = event.ydata
            s = "{:5.2f} {:5.1f}".format(f, h)

            if event.button == 1:

                if self.mode == 0:  # F2
                    self.listWidgetF2.addItem(s)
                elif self.mode == 1:  # F1
                    self.listWidgetF1.addItem(s)
                elif self.mode == 2:  # E
                    self.listWidgetE.addItem(s)

            elif event.button == 3:

                if self.mode == 0:  # F2

                    modifiers = QApplication.keyboardModifiers()
                    # subract half of hyrofrequency if Shift key is pressed
                    if modifiers == Qt.KeyboardModifier.ShiftModifier:
                        f = round(
                            self.iono.coord_to_freq(event.xdata)
                            - self.get_value(self.gyrofrequencyLineEdit) / 2,
                            2,
                        )

                    self.doubleSpinBoxF2.setValue(f)

                elif self.mode == 1:  # F1
                    self.doubleSpinBoxF1.setValue(f)

                elif self.mode == 2:  # E
                    self.doubleSpinBoxE.setValue(f)
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

        self.canvas.draw()

    def plot_lines(self, text):

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
                if (f > left) and (f < right):
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

        self.canvas.draw()

    def onmove(self, event):
        if event.ydata and event.xdata:
            f = self.iono.coord_to_freq(event.xdata)
            h = event.ydata
            self.statusbar.showMessage("f={:5.2f}  h'={:5.1f}".format(f, h))
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
        tester = IonoTester()
        class_name = tester.examine(file_name)["class_name"]
        if class_name != "Unknown":
            self.close_file()
            class_ = globals()[class_name]
            self.iono = class_()
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
                )

                tics = self.iono.get_freq_tics()
                labels = self.iono.get_freq_labels()
                self.ax.set_xticks(tics)
                self.ax.set_xticklabels(labels)

                plt.tight_layout()
                self.setWindowTitle(self.program_name + " - " + file_name)
                self.canvas.draw()

                self.stationNameEdit.setText(self.iono.get_station_name())
                self.ursiCodeEdit.setText(
                    self.iono.get_ursi_code() if "ursi_code" in vars(self.iono) else ""
                )
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
                    str.format("{:>+3d}" if time_zone != 0 else "{:>3d}", time_zone)
                )
                self.timeZoneComboBox.setCurrentIndex(position)
                _ = [e.setEnabled(True) for e in self.properties_of_iono]

                self.load_text_info()

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
            directory = path.dirname(self.file_name)
            filenames = self.get_filelist(directory)
            index = filenames.index(path.basename(self.file_name))
            if index + 1 < len(filenames):
                new_file_name = path.join(directory, filenames[index + 1])
                self.open_file(new_file_name)

    def open_prev_file(self):
        if self.file_name:
            directory = path.dirname(self.file_name)
            filenames = self.get_filelist(directory)
            index = filenames.index(path.basename(self.file_name))
            if index - 1 >= 0:
                new_file_name = path.join(directory, filenames[index - 1])
                self.open_file(new_file_name)

    def open_last_file(self):
        if self.file_name:
            directory = path.dirname(self.file_name)
            filenames = self.get_filelist(directory)
            new_file_name = path.join(directory, filenames[-1])
            self.open_file(new_file_name)

    def open_first_file(self):
        if self.file_name:
            directory = path.dirname(self.file_name)
            filenames = self.get_filelist(directory)
            new_file_name = path.join(directory, filenames[0])
            self.open_file(new_file_name)

    def reopen_file(self):
        if self.file_name:
            self.open_file(self.file_name)

    def get_filelist(self, directory):
        tester = IonoTester()
        result = []
        for filename in FileList.get(directory):
            class_name = tester.examine(directory + "/" + filename)["class_name"]
            if class_name != "Unknown":
                result.append(filename)
        return result

    def load_text_info(self):
        try:
            with open(self.file_name + ".STD", "r", encoding="ascii") as file:
                first_line = file.readline().strip()
                if "//" in first_line:
                    (self.iono.station_name, timezone) = first_line.strip().split("//")
                else:
                    self.iono.station_name = first_line
                    timezone = 0
                (
                    self.iono.lat,
                    self.iono.long,
                    self.iono.gyro,
                    self.iono.dip,
                    self.iono.sunspot,
                ) = (
                    file.readline().strip().split()
                )
                date = file.readline().strip()

                self.stationNameEdit.setText(self.iono.station_name)
                self.latLineEdit.setText(self.iono.lat)
                self.longLineEdit.setText(self.iono.long)
                self.gyrofrequencyLineEdit.setText(self.iono.gyro)
                self.dipAngleLineEdit.setText(self.iono.dip)
                self.sunspotNumberLineEdit.setText(self.iono.sunspot)

                self.iono.set_timezone(timezone)
                timezone = self.iono.get_timezone()
                position = self.timeZoneComboBox.findText(
                    str.format("{:>+3d}" if timezone != 0 else "{:>3d}", timezone)
                )
                self.timeZoneComboBox.setCurrentIndex(position)

                date = datetime.strptime(date, "%Y %m %d %H %M 00")
                date += timedelta(hours=timezone)  # Convert from UT
                self.iono.set_date(date)
                self.dateTimeEdit.setDateTime(self.iono.get_date())

                foE = float(file.readline().strip())
                if abs(foE - 99.0) > 1:
                    self.doubleSpinBoxE.setValue(foE)
                while True:
                    line = file.readline().strip()
                    if line == "END":
                        break
                    s = line.split()
                    line = "{:-5.2f} {:-5.1f}".format(float(s[0]), float(s[1]))
                    self.listWidgetE.addItem(line)

                foF1 = float(file.readline().strip())
                if abs(foF1 - 99.0) > 1:
                    self.doubleSpinBoxF1.setValue(foF1)
                while True:
                    line = file.readline().strip()
                    if line == "END":
                        break
                    s = line.split()
                    line = "{:-5.2f} {:-5.1f}".format(float(s[0]), float(s[1]))
                    self.listWidgetF1.addItem(line)

                foF2 = float(file.readline().strip())
                if abs(foF2 - 99.0) > 1:
                    self.doubleSpinBoxF2.setValue(foF2)
                while True:
                    line = file.readline().strip()
                    if line == "END":
                        break
                    s = line.split()
                    line = "{:-5.2f} {:-5.1f}".format(float(s[0]), float(s[1]))
                    self.listWidgetF2.addItem(line)

            self.plot_scatters()

        except IOError:
            return

    def save_file(self):
        if self.file_name:

            if self.stdCheckBox.isChecked():
                self.save_std(self.file_name + ".STD")

            if self.pngCheckBox.isChecked():
                width = self.pngWidthSpinBox.value()
                height = self.pngHeightSpinBox.value()
                dpi = self.pngDpiSpinBox.value()
                self.save_image(
                    self.file_name + ".png", width=width, height=height, dpi=dpi
                )
            self.statusbar.showMessage("File is saved.")

    def get_value(self, widget):
        value = 0
        try:
            value = float(widget.text().strip())
        except ValueError:
            pass
        return value

    def save_std(self, filename):

        foE = self.doubleSpinBoxE.value()
        if abs(foE - 99.0) < 1.0 or abs(foE) < 0.1:
            foE = "99.0"

        fohE = ""
        for i in range(self.listWidgetE.count()):
            fohE += self.listWidgetE.item(i).text() + "\n"

        foF1 = self.doubleSpinBoxF1.value()
        if abs(foF1 - 99.0) < 1.0 or abs(foF1) < 0.1:
            foF1 = "99.0"

        fohF1 = ""
        for i in range(self.listWidgetF1.count()):
            fohF1 += self.listWidgetF1.item(i).text() + "\n"

        foF2 = self.doubleSpinBoxF2.value()
        if abs(foF2 - 99.0) < 1.0 or abs(foF2) < 0.1:
            foF2 = "99.0"

        fohF2 = ""
        for i in range(self.listWidgetF2.count()):
            fohF2 += self.listWidgetF2.item(i).text() + "\n"

        self.iono.lat = self.get_value(self.latLineEdit)
        self.iono.lon = self.get_value(self.longLineEdit)
        self.iono.gyro = self.get_value(self.gyrofrequencyLineEdit)
        self.iono.dip = self.get_value(self.dipAngleLineEdit)
        self.iono.sunspot = self.get_value(self.sunspotNumberLineEdit)

        coordinates = str.format(
            "{} {} {} {} {}",
            str(self.iono.lat),
            str(self.iono.lon),
            str(self.iono.gyro),
            str(self.iono.dip),
            str(self.iono.sunspot),
        )

        date = datetime.strptime(self.dateTimeEdit.text(), "%Y-%m-%d %H:%M")
        timezone = int(self.timeZoneComboBox.currentText().strip())
        date -= timedelta(hours=timezone)  # Convert to UT
        date = date.strftime("%Y %m %d %H %M 00")

        station = self.iono.station_name + "//" + str(timezone)

        with open(filename, "w") as file:
            file.write(station + "\n")

            file.write(coordinates + "\n")

            file.write(date + "\n")

            file.write(str(foE) + "\n")
            file.write(str(fohE))
            file.write("END\n")

            file.write(str(foF1) + "\n")
            file.write(str(fohF1))
            file.write("END\n")

            file.write(str(foF2) + "\n")
            file.write(str(fohF2))
            file.write("END\n")

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
        ursi_code = self.ursiCodeEdit.text().strip()
        time_zone = self.timeZoneComboBox.currentText().strip()
        description = "{}{}, {} ({})".format(
            self.stationNameEdit.text().strip(),
            " (" + ursi_code + ")" if ursi_code else "",
            self.dateTimeEdit.dateTime().toString(DATE_TIME_FORMAT),
            "UTC" if time_zone == "0" else "UTC" + time_zone,
        )

        foF2 = self.doubleSpinBoxF2.value()
        foF1 = self.doubleSpinBoxF1.value()
        foE = self.doubleSpinBoxE.value()
        foF2 = f"foF2 = {foF2:.2f} MHz   " if foF2 else ""
        foF1 = f"foF1 = {foF1:.2f} MHz   " if foF1 else ""
        foE = f"foE = {foE:.2f} MHz" if foE else ""

        if foF2 or foF1 or foE:
            description += f"\n{foF2}{foF1}{foE}"

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
                     © 2018-2024 Oleksandr Bogomaz<br>
                     o.v.bogomaz1985@gmail.com<br>
                 """

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(about)
        msg.setWindowTitle("About")
        msg.show()
        msg.exec()


class RemoteWnd(QDialog):

    def __init__(self):
        super().__init__()
        uic.loadUi("./ui/RemoteWnd.ui", self)
        self.setModal(True)
        self.importButton.clicked.connect(self.import_button_clicked)
        self.sourceComboBox.addItem("database.rish.kyoto-u.ac.jp")
        self.ionosondeComboBox.addItem("Shigaraki")
        self.startDateTimeEdit.setDisplayFormat(DATE_TIME_FORMAT)
        self.endDateTimeEdit.setDisplayFormat(DATE_TIME_FORMAT)
        self.show()

    def import_button_clicked(self):
        directory_name = str(QFileDialog.getExistingDirectory(self))
        if directory_name:
            index = self.sourceComboBox.currentIndex()
            ionosonde = self.ionosondeComboBox.currentIndex()
            proxy_host = self.proxyHostLineEdit.text()
            proxy_port = self.proxyPortLineEdit.text()
            start = self.startDateTimeEdit.dateTime().toString(DATE_TIME_FORMAT)
            end = self.endDateTimeEdit.dateTime().toString(DATE_TIME_FORMAT)
            start = datetime.strptime(start, "%Y-%m-%d %H:%M")
            end = datetime.strptime(end, "%Y-%m-%d %H:%M")
            if index == 0 and ionosonde == 0:
                loader = ShigarakiLoader(proxy_host, proxy_port)
                n_files = loader.saveTo(directory_name, start, end)

                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setText(str(n_files) + " file(s) loaded.")
                msg.setWindowTitle("Remote")
                msg.show()
                msg.exec()


if __name__ == "__main__":
    matplotlib_backend_use("agg")
    app = QApplication(sys.argv)

    main = MainWindow()
    main.show()

    sys.exit(app.exec())
