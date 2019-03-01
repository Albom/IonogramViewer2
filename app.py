import sys
from os import walk, path
from datetime import datetime, timedelta
from PyQt5 import uic
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QApplication, \
    QFileDialog, QMenu, QMessageBox

import matplotlib
matplotlib.use("agg")
from matplotlib.backends.backend_qt5agg \
    import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib import colors

from iono_tester import IonoTester
from karazin_iono import KarazinIono
from ips42_iono import Ips42Iono
from dps_amp_iono import DpsAmpIono


DATE_TIME_FORMAT = 'yyyy-MM-dd hh:mm'


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.program_name = 'IonogramViewer2 v1.3 pre'

        uic.loadUi('./ui/MainWnd.ui', self)

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
            self.actionClose: self.close_file}
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
        self.canvas.mpl_connect('button_press_event', self.onclick)
        self.canvas.mpl_connect('motion_notify_event', self.onmove)

        listWidgets = [self.listWidgetE, self.listWidgetF1, self.listWidgetF2]
        for w in listWidgets:
            w.setContextMenuPolicy(Qt.CustomContextMenu)
            w.customContextMenuRequested.connect(self.delete_menu)

        spinBoxes = [
            self.doubleSpinBoxF2, self.doubleSpinBoxF1, self.doubleSpinBoxE,
            self.doubleSpinBoxF2m, self.doubleSpinBoxF1m, self.doubleSpinBoxEm]
        for w in spinBoxes:
            w.valueChanged.connect(self.plot_lines)

        items = [str.format('{:>+3d}' if i != 0 else '{:>3d}', i) for i in range(-11, 13)]
        self.timeZoneComboBox.addItems(items)
        font = QFont("Monospace")
        font.setStyleHint(QFont.TypeWriter)
        self.timeZoneComboBox.setFont(font)

        self.properties_of_iono = [
            self.stationNameEdit, self.timeZoneComboBox,
            self.ursiCodeEdit, self.dateTimeEdit, self.latLineEdit,
            self.longLineEdit, self.sunspotNumberLineEdit,
            self.gyrofrequencyLineEdit, self.dipAngleLineEdit]

        self.dateTimeEdit.setDisplayFormat(DATE_TIME_FORMAT)

        self.clear_all()

        self.setWindowTitle(self.program_name)
        self.showMaximized()

    def png_state_changed(self, state):
        s = state == Qt.Checked
        elements = [
            self.pngDefaultButton, self.pngWidthSpinBox,
            self.pngHeightSpinBox, self.pngDpiSpinBox]
        for e in elements:
            e.setEnabled(s)

    def set_default_image_param(self):
        self.pngDpiSpinBox.setValue(100)
        self.pngWidthSpinBox.setValue(10)
        self.pngHeightSpinBox.setValue(6)

    def change_layer(self):
        mode = self.mode+1 if self.mode < 2 else 0
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
        self.doubleSpinBoxF2m.setValue(0)
        self.doubleSpinBoxF1m.setValue(0)
        self.doubleSpinBoxEm.setValue(0)

        self.listWidgetE.clear()
        self.listWidgetF1.clear()
        self.listWidgetF2.clear()

        self.radioButtonF2.setChecked(True)
        [e.setEnabled(False) for e in self.properties_of_iono]

    def delete_menu(self, point):
        if self.sender().count():
            listMenu = QMenu()
            delete_action = listMenu.addAction('Delete')
            delete_all_action = listMenu.addAction('Delete all')
            point_global = self.sender().mapToGlobal(point)
            r = listMenu.exec_(point_global)
            if r is delete_action:
                item = self.sender().row(self.sender().itemAt(point))
                self.sender().takeItem(item)
            elif r is delete_all_action:
                self.sender().clear()
            self.plot_scatter()

    def change_mode(self, mode):
        self.mode = mode

        widgets = [
            self.doubleSpinBoxE, self.doubleSpinBoxF1, self.doubleSpinBoxF2,
            self.doubleSpinBoxEm, self.doubleSpinBoxF1m, self.doubleSpinBoxF2m,
            self.listWidgetE, self.listWidgetF1, self.listWidgetF2]
        for w in widgets:
            w.setEnabled(False)

        if mode == 0:
            self.doubleSpinBoxF2.setEnabled(True)
            self.doubleSpinBoxF2m.setEnabled(True)
            self.listWidgetF2.setEnabled(True)
        elif mode == 1:
            self.doubleSpinBoxF1.setEnabled(True)
            self.doubleSpinBoxF1m.setEnabled(True)
            self.listWidgetF1.setEnabled(True)
        elif mode == 2:
            self.doubleSpinBoxE.setEnabled(True)
            self.doubleSpinBoxEm.setEnabled(True)
            self.listWidgetE.setEnabled(True)

    def onclick(self, event):
        if event.ydata and event.xdata:
            f = round(self.iono.coord_to_freq(event.xdata), 2)
            h = event.ydata
            s = '{:5.2f} {:5.1f}'.format(f, h)
            if event.button == 1:
                if self.mode == 0:  # F2
                    self.listWidgetF2.addItem(s)
                elif self.mode == 1:  # F1
                    self.listWidgetF1.addItem(s)
                elif self.mode == 2:  # E
                    self.listWidgetE.addItem(s)
            elif event.button == 3:
                if self.mode == 0:  # F2
                    self.doubleSpinBoxF2.setValue(f)
                elif self.mode == 1:  # F1
                    self.doubleSpinBoxF1.setValue(f)
                elif self.mode == 2:  # E
                    self.doubleSpinBoxE.setValue(f)
            elif event.button == 2:
                if self.mode == 0:  # F2
                    self.doubleSpinBoxF2m.setValue(f)
                elif self.mode == 1:  # F1
                    self.doubleSpinBoxF1m.setValue(f)
                elif self.mode == 2:  # E
                    self.doubleSpinBoxEm.setValue(f)
            self.plot_scatter()

    def plot_scatter(self):
        if self.e_scatter is not None:
            self.e_scatter.remove()

        x_e = []
        y_e = []
        for i in range(self.listWidgetE.count()):
            t = self.listWidgetE.item(i).text().split()
            x_e.append(self.iono.freq_to_coord(t[0]))
            y_e.append(float(t[1]))
        self.e_scatter = self.ax.scatter(x_e, y_e, c='g')

        if self.f1_scatter is not None:
            self.f1_scatter.remove()

        x_f1 = []
        y_f1 = []
        for i in range(self.listWidgetF1.count()):
            t = self.listWidgetF1.item(i).text().split()
            x_f1.append(self.iono.freq_to_coord(t[0]))
            y_f1.append(float(t[1]))
        self.f1_scatter = self.ax.scatter(x_f1, y_f1, c='c')

        if self.f2_scatter is not None:
            self.f2_scatter.remove()

        x_f2 = []
        y_f2 = []
        for i in range(self.listWidgetF2.count()):
            t = self.listWidgetF2.item(i).text().split()
            x_f2.append(self.iono.freq_to_coord(t[0]))
            y_f2.append(float(t[1]))
        self.f2_scatter = self.ax.scatter(x_f2, y_f2, c='r')

        self.canvas.draw()

    def plot_lines(self, text):

        if self.iono is None:
            return

        left = self.iono.get_extent()[0]
        right = self.iono.get_extent()[1]
        top = self.iono.get_extent()[3]
        bottom = self.iono.get_extent()[2]

        def plot_line(box, line, color, style='-'):
            if line is not None:
                line.remove()
                line = None
            freq = box.value()
            if (freq > left) and (freq < right):
                f = self.iono.freq_to_coord(freq)
                line, = self.ax.plot(
                    [f, f],
                    [bottom, top],
                    c=color,
                    linestyle=style)
            return line

        self.f2_critical = plot_line(
            self.doubleSpinBoxF2,
            self.f2_critical,
            'r')
        self.f1_critical = plot_line(
            self.doubleSpinBoxF1,
            self.f1_critical,
            'c')
        self.e_critical = plot_line(
            self.doubleSpinBoxE,
            self.e_critical,
            'g')
        self.f2_min = plot_line(
            self.doubleSpinBoxF2m,
            self.f2_min,
            'r',
            style='--')
        self.f1_min = plot_line(
            self.doubleSpinBoxF1m,
            self.f1_min,
            'c',
            style='--')
        self.e_min = plot_line(
            self.doubleSpinBoxEm,
            self.e_min,
            'g',
            style='--')

        self.canvas.draw()

    def onmove(self, event):
        if event.ydata and event.xdata:
            f = self.iono.coord_to_freq(event.xdata)
            h = event.ydata
            self.statusbar.showMessage('f={:5.2f}  h\'={:5.1f}'.format(f, h))
            if not self.is_cross:
                QApplication.setOverrideCursor(Qt.CrossCursor)
                self.is_cross = True
        else:
            self.statusbar.showMessage('')
            if self.is_cross:
                QApplication.restoreOverrideCursor()
                self.is_cross = False

    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self)
        self.open_file(file_name)

    def close_file(self):
        self.clear_all()
        self.iono = None
        self.file_name = ''
        self.figure.clear()
        self.ax = None
        self.canvas.draw()

    def open_file(self, file_name):

        self.close_file()

        self.setWindowTitle(self.program_name)
        if file_name:
            self.clear_all()

            tester = IonoTester()
            class_name = tester.examine(file_name)['class_name']
            if class_name != 'Unknown':
                class_ = globals()[class_name]
                self.iono = class_()
                self.iono.load(file_name)
                data = self.iono.get_data()
                if data:

                    self.file_name = file_name

                    self.ax = self.figure.add_subplot(111)

                    extent = self.iono.get_extent()
                    cmap = colors.ListedColormap(['black', 'white', 'purple'])
                    self.ax.imshow(data, cmap=cmap, interpolation='nearest',
                                   extent=extent, aspect='auto')

                    tics = self.iono.get_freq_tics()
                    labels = self.iono.get_freq_labels()
                    self.ax.set_xticks(tics)
                    self.ax.set_xticklabels(labels)

                    plt.tight_layout()
                    self.setWindowTitle(self.program_name + " - " + file_name)
                    self.canvas.draw()

                    self.stationNameEdit.setText(self.iono.get_station_name())
                    self.ursiCodeEdit.setText(self.iono.get_ursi_code() if 'ursi_code' in vars(self.iono) else '')
                    self.dateTimeEdit.setDateTime(self.iono.get_date())

                    timeZone = self.iono.get_timezone()
                    position = self.timeZoneComboBox.findText(str.format('{:>+3d}' if timeZone != 0 else '{:>3d}', timeZone))
                    self.timeZoneComboBox.setCurrentIndex(position)
                    [e.setEnabled(True) for e in self.properties_of_iono]

                    self.load_text_info()
            else:
                self.show_error('File format is not supported.')

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
        filenames = []
        for (dp, dn, fn) in walk(directory):
            filenames.extend(fn)
            break

        filenames.sort()
        tester = IonoTester()
        result = []
        for filename in filenames:
            class_name = tester.examine(directory+'/'+filename)['class_name']
            if class_name != 'Unknown':
                result.append(filename)

        return result

    def load_text_info(self):
        try:
            with open(self.file_name + '.STD', 'r') as file:
                (self.iono.station_name,
                    timezone) = file.readline().strip().split('//')
                (self.iono.lat, self.iono.long,
                    self.iono.gyro, self.iono.dip,
                    self.iono.sunspot) = file.readline().strip().split()
                date = file.readline().strip()

                self.stationNameEdit.setText(self.iono.station_name)
                self.latLineEdit.setText(self.iono.lat)
                self.longLineEdit.setText(self.iono.long)
                self.gyrofrequencyLineEdit.setText(self.iono.gyro)
                self.dipAngleLineEdit.setText(self.iono.dip)
                self.sunspotNumberLineEdit.setText(self.iono.sunspot)

                self.iono.set_timezone(timezone)
                timezone = self.iono.get_timezone()
                position = self.timeZoneComboBox.findText(str.format('{:>+3d}' if timezone != 0 else '{:>3d}', timezone))
                self.timeZoneComboBox.setCurrentIndex(position)

                date = datetime.strptime(date, '%Y %m %d %H %M 00')
                date += timedelta(hours=timezone)  # Convert from UT
                self.iono.set_date(date)
                self.dateTimeEdit.setDateTime(self.iono.get_date())

                foE = float(file.readline().strip())
                if abs(foE - 99.0) > 1:
                    self.doubleSpinBoxE.setValue(foE)
                while True:
                    line = file.readline().strip()
                    if line == 'END':
                        break
                    s = line.split()
                    line = '{:-5.2f} {:-5.1f}'.format(float(s[0]), float(s[1]))
                    self.listWidgetE.addItem(line)

                foF1 = float(file.readline().strip())
                if abs(foF1 - 99.0) > 1:
                    self.doubleSpinBoxF1.setValue(foF1)
                while True:
                    line = file.readline().strip()
                    if line == 'END':
                        break
                    s = line.split()
                    line = '{:-5.2f} {:-5.1f}'.format(float(s[0]), float(s[1]))
                    self.listWidgetF1.addItem(line)

                foF2 = float(file.readline().strip())
                if abs(foF2 - 99.0) > 1:
                    self.doubleSpinBoxF2.setValue(foF2)
                while True:
                    line = file.readline().strip()
                    if line == 'END':
                        break
                    s = line.split()
                    line = '{:-5.2f} {:-5.1f}'.format(float(s[0]), float(s[1]))
                    self.listWidgetF2.addItem(line)

            self.plot_scatter()

        except IOError:
            return

    def save_file(self):
        if self.file_name:
            if self.stdCheckBox.isChecked():
                self.save_std(self.file_name + '.STD')

            if self.pngCheckBox.isChecked():
                width = self.pngWidthSpinBox.value()
                height = self.pngHeightSpinBox.value()
                dpi = self.pngDpiSpinBox.value()
                self.save_image(
                    self.file_name + '.png',
                    width=width,
                    height=height,
                    dpi=dpi)
            self.statusbar.showMessage('File is saved.')

    def save_std(self, filename):

        foE = self.doubleSpinBoxE.value()
        if abs(foE - 99.0) < 1.0 or abs(foE) < 0.1:
            foE = '99.0'

        fohE = ''
        for i in range(self.listWidgetE.count()):
                fohE += self.listWidgetE.item(i).text() + '\n'

        foF1 = self.doubleSpinBoxF1.value()
        if abs(foF1 - 99.0) < 1.0 or abs(foF1) < 0.1:
            foF1 = '99.0'

        fohF1 = ''
        for i in range(self.listWidgetF1.count()):
            fohF1 += self.listWidgetF1.item(i).text() + '\n'

        foF2 = self.doubleSpinBoxF2.value()
        if abs(foF2 - 99.0) < 1.0 or abs(foF2) < 0.1:
            foF2 = '99.0'

        fohF2 = ''
        for i in range(self.listWidgetF2.count()):
            fohF2 += self.listWidgetF2.item(i).text() + '\n'

        lat = self.latLineEdit.text().strip()
        lon = self.longLineEdit.text().strip()
        gyro = self.gyrofrequencyLineEdit.text().strip()
        dip = self.dipAngleLineEdit.text().strip()
        sunspot = self.sunspotNumberLineEdit.text().strip()

        self.iono.lat = lat if len(lat) > 0 else 0
        self.iono.lon = lon if len(lon) > 0 else 0
        self.iono.gyro = gyro if len(gyro) > 0 else 0
        self.iono.dip = dip if len(dip) > 0 else 0
        self.iono.sunspot = sunspot if len(sunspot) > 0 else 0

        coordinates = str.format(
            '{} {} {} {} {}',
            str(self.iono.lat),
            str(self.iono.lon),
            str(self.iono.gyro),
            str(self.iono.dip),
            str(self.iono.sunspot))

        date = datetime.strptime(self.dateTimeEdit.text(), '%Y-%m-%d %H:%M')
        timezone = int(self.timeZoneComboBox.currentText().strip())
        date -= timedelta(hours=timezone)  # Convert to UT
        date = date.strftime('%Y %m %d %H %M 00')

        station = self.iono.station_name + '//' + str(timezone)

        with open(filename, 'w') as file:
            file.write(station + '\n')

            file.write(coordinates + '\n')

            file.write(date + '\n')

            file.write(str(foE) + '\n')
            file.write(str(fohE))
            file.write('END\n')

            file.write(str(foF1) + '\n')
            file.write(str(fohF1))
            file.write('END\n')

            file.write(str(foF2) + '\n')
            file.write(str(fohF2))
            file.write('END\n')

    def save_image(self, filename, **kwargs):
            width = 10 if 'width' not in kwargs else kwargs['width']
            height = 5.5 if 'height' not in kwargs else kwargs['height']
            dpi = 100 if 'dpi' not in kwargs else kwargs['dpi']
            old_size = self.figure.get_size_inches()
            self.figure.set_size_inches(width, height)
            ursiCode = self.ursiCodeEdit.text().strip()
            timeZone = self.timeZoneComboBox.currentText().strip()
            title = '{}{}, {} ({})'.format(
                self.stationNameEdit.text().strip(),
                ' (' + ursiCode + ')' if len(ursiCode) > 0 else '',
                self.dateTimeEdit.dateTime().toString(DATE_TIME_FORMAT),
                'UTC' if timeZone == '0' else 'UTC'+timeZone)
            plt.title(title)
            plt.tight_layout()
            self.figure.savefig(filename, dpi=dpi)
            plt.title('')
            self.figure.set_size_inches(old_size)
            plt.tight_layout()
            self.canvas.draw()

    def show_error(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(message)
        msg.setWindowTitle("Error")
        msg.show()
        msg.exec_()

    def show_about(self):
        about = '\n\n© 2018-2019 Oleksandr Bogomaz\no.v.bogomaz1985@gmail.com'

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(self.program_name + about)
        msg.setWindowTitle("About")
        msg.show()
        msg.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    main = MainWindow()
    main.show()

    sys.exit(app.exec_())
