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

        lineEdits = [
            self.lineEditE, self.lineEditF1, self.lineEditF2,
            self.lineEditEm, self.lineEditF1m, self.lineEditF2m]
        for e in lineEdits:
            e.textChanged.connect(self.plot_lines)

        self.timeZoneComboBox.addItems([str.format('{:>+3d}' if i != 0 else '{:>3d}', i) for i in range(-11, 13)])
        font = QFont("Monospace");
        font.setStyleHint(QFont.TypeWriter);
        self.timeZoneComboBox.setFont(font)

        self.properties_of_iono = [self.stationNameEdit,
            self.timeZoneComboBox, self.ursiCodeEdit, self.dateTimeEdit,
            self.latLineEdit, self.longLineEdit, self.sunspotNumberLineEdit,
            self.gyrofrequencyLineEdit, self.dipAngleLineEdit]

        self.dateTimeEdit.setDisplayFormat(DATE_TIME_FORMAT)

        self.clear_all()

        self.setWindowTitle(self.program_name)
        self.showMaximized()

    def png_state_changed(self, state):
        s = state == Qt.Checked
        elements = [self.pngDefaultButton, self.pngWidthSpinBox,
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

        self.lineEditE.setText('')
        self.lineEditF1.setText('')
        self.lineEditF2.setText('')

        self.lineEditEm.setText('')
        self.lineEditF1m.setText('')
        self.lineEditF2m.setText('')

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
            self.lineEditE, self.lineEditEm, self.listWidgetE,
            self.lineEditF1, self.lineEditF1m, self.listWidgetF1,
            self.lineEditF2, self.lineEditF2m, self.listWidgetF2]
        for w in widgets:
            w.setEnabled(False)

        if mode == 0:
            self.lineEditF2.setEnabled(True)
            self.lineEditF2m.setEnabled(True)
            self.listWidgetF2.setEnabled(True)
        elif mode == 1:
            self.lineEditF1.setEnabled(True)
            self.lineEditF1m.setEnabled(True)
            self.listWidgetF1.setEnabled(True)
        elif mode == 2:
            self.lineEditE.setEnabled(True)
            self.lineEditEm.setEnabled(True)
            self.listWidgetE.setEnabled(True)

    def onclick(self, event):
        if event.ydata and event.xdata:
            f = self.iono.coord_to_freq(event.xdata)
            h = event.ydata
            s = '{:5.2f} {:5.1f}'.format(f, h)
            f = '{:<5.2f}'.format(f).strip()
            if event.button == 1:
                if self.mode == 0:  # F2
                    self.listWidgetF2.addItem(s)
                elif self.mode == 1:  # F1
                    self.listWidgetF1.addItem(s)
                elif self.mode == 2:  # E
                    self.listWidgetE.addItem(s)
            elif event.button == 3:
                if self.mode == 0:  # F2
                    self.lineEditF2.setText(f)
                elif self.mode == 1:  # F1
                    self.lineEditF1.setText(f)
                elif self.mode == 2:  # E
                    self.lineEditE.setText(f)
            elif event.button == 2:
                if self.mode == 0:  # F2
                    self.lineEditF2m.setText(f)
                elif self.mode == 1:  # F1
                    self.lineEditF1m.setText(f)
                elif self.mode == 2:  # E
                    self.lineEditEm.setText(f)
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

        foE = self.lineEditE.text().strip()

        try:
            foE = float(foE)
        except ValueError:
            foE = 99.0

        if (foE > left) and (foE < right):
            if self.e_critical is not None:
                self.e_critical.remove()
                self.e_critical = None

            f = self.iono.freq_to_coord(foE)

            self.e_critical, = self.ax.plot([f, f], [bottom, top], c='g')
        else:
            if self.e_critical is not None:
                self.e_critical.remove()
                self.e_critical = None

        foF1 = self.lineEditF1.text().strip()

        try:
            foF1 = float(foF1)
        except ValueError:
            foF1 = 99.0

        if (foF1 > left) and (foF1 < right):
            if self.f1_critical is not None:
                self.f1_critical.remove()
                self.f1_critical = None

            f = self.iono.freq_to_coord(foF1)
            self.f1_critical, = self.ax.plot([f, f], [bottom, top], c='c')
        else:
            if self.f1_critical is not None:
                self.f1_critical.remove()
                self.f1_critical = None

        foF2 = self.lineEditF2.text().strip()

        try:
            foF2 = float(foF2)
        except ValueError:
            foF2 = 99.0

        if (foF2 > left) and (foF2 < right):
            if self.f2_critical is not None:
                self.f2_critical.remove()
                self.f2_critical = None

            f = self.iono.freq_to_coord(foF2)
            self.f2_critical, = self.ax.plot([f, f], [bottom, top], c='r')
        else:
            if self.f2_critical is not None:
                self.f2_critical.remove()
                self.f2_critical = None

        f_min_F2 = self.lineEditF2m.text().strip()
        try:
            f_min_F2 = float(f_min_F2)
        except ValueError:
            f_min_F2 = 99.0

        if (f_min_F2 > left) and (f_min_F2 < right):
            if self.f2_min is not None:
                self.f2_min.remove()
                self.f2_min = None

            f = self.iono.freq_to_coord(f_min_F2)
            self.f2_min, = self.ax.plot(
                [f, f],
                [bottom, top],
                c='r',
                linestyle='--')
        else:
            if self.f2_min is not None:
                self.f2_min.remove()
                self.f2_min = None

        f_min_F1 = self.lineEditF1m.text().strip()
        try:
            f_min_F1 = float(f_min_F1)
        except ValueError:
            f_min_F1 = 99.0

        if (f_min_F1 > left) and (f_min_F1 < right):
            if self.f1_min is not None:
                self.f1_min.remove()
                self.f1_min = None

            f = self.iono.freq_to_coord(f_min_F1)
            self.f1_min, = self.ax.plot(
                [f, f],
                [bottom, top],
                c='c',
                linestyle='--')
        else:
            if self.f1_min is not None:
                self.f1_min.remove()
                self.f1_min = None

        f_min_E = self.lineEditEm.text().strip()
        try:
            f_min_E = float(f_min_E)
        except ValueError:
            f_min_E = 99.0

        if (f_min_E > left) and (f_min_E < right):
            if self.e_min is not None:
                self.e_min.remove()
                self.e_min = None

            f = self.iono.freq_to_coord(f_min_E)
            self.e_min, = self.ax.plot(
                [f, f],
                [bottom, top],
                c='g',
                linestyle='--')
        else:
            if self.e_min is not None:
                self.e_min.remove()
                self.e_min = None

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
                date += timedelta(hours=timezone) # Convert from UT
                self.iono.set_date(date)
                self.dateTimeEdit.setDateTime(self.iono.get_date())

                foE = file.readline().strip()
                if abs(float(foE) - 99.0) > 1:
                    self.lineEditE.setText(foE)
                while True:
                    line = file.readline().strip()
                    if line == 'END':
                        break
                    s = line.split()
                    line = '{:-5.2f} {:-5.1f}'.format(float(s[0]), float(s[1]))
                    self.listWidgetE.addItem(line)

                foF1 = file.readline().strip()
                if abs(float(foF1) - 99.0) > 1:
                    self.lineEditF1.setText(foF1)
                while True:
                    line = file.readline().strip()
                    if line == 'END':
                        break
                    s = line.split()
                    line = '{:-5.2f} {:-5.1f}'.format(float(s[0]), float(s[1]))
                    self.listWidgetF1.addItem(line)

                foF2 = file.readline().strip()
                if abs(float(foF2) - 99.0) > 1:
                    self.lineEditF2.setText(foF2)
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

        foE = self.lineEditE.text().strip()
        try:
            foE = float(foE)
            if abs(foE - 99.0) < 1.0 or abs(foE) < 0.1:
                foE = '99.0'
        except ValueError:
            foE = '99.0'

        fohE = ''
        for i in range(self.listWidgetE.count()):
                fohE += self.listWidgetE.item(i).text() + '\n'

        foF1 = self.lineEditF1.text().strip()
        try:
            foF1 = float(foF1)
            if abs(foF1 - 99.0) < 1.0 or abs(foF1) < 0.1:
                foF1 = '99.0'
        except ValueError:
            foF1 = '99.0'

        fohF1 = ''
        for i in range(self.listWidgetF1.count()):
            fohF1 += self.listWidgetF1.item(i).text() + '\n'

        foF2 = self.lineEditF2.text().strip()
        try:
            foF2 = float(foF2)
            if abs(foF2 - 99.0) < 1.0 or abs(foF2) < 0.1:
                foF2 = '99.0'
        except ValueError:
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
        date -= timedelta(hours=timezone) # Convert to UT
        date = date.strftime('%Y %m %d %H %M 00')

        station = self.iono.station_name  + '//' + str(timezone)

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
