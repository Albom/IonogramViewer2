import sys
from os import walk, path
from math import sqrt, log
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QApplication, \
    QFileDialog, QMenu, QMessageBox

import matplotlib
matplotlib.use("agg")
from matplotlib.backends.backend_qt5agg \
    import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

from karazin_iono import KarazinIono
from uac_iono import UacIono


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.program_name = 'IonogramViewer2 v1.1'

        uic.loadUi('./ui/MainWnd.ui', self)
        self.actionExit.triggered.connect(exit)
        self.actionOpen.triggered.connect(self.open_file_dialog)
        self.actionSave.triggered.connect(self.save_file)
        self.actionAbout.triggered.connect(self.show_about)
        self.actionNext.triggered.connect(self.open_next_file)
        self.actionPrevious.triggered.connect(self.open_prev_file)
        self.actionFirst.triggered.connect(self.open_first_file)
        self.actionLast.triggered.connect(self.open_last_file)
        self.actionReload.triggered.connect(self.reopen_file)

        self.mode = 0  # E
        self.radioButtonE.toggled.connect(lambda: self.change_mode(0))
        self.radioButtonF1.toggled.connect(lambda: self.change_mode(1))
        self.radioButtonF2.toggled.connect(lambda: self.change_mode(2))

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.horizontalLayout.addWidget(self.canvas)
        self.is_cross = False
        self.canvas.mpl_connect('button_press_event', self.onclick)
        self.canvas.mpl_connect('motion_notify_event', self.onmove)

        self.listWidgetE.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listWidgetE.customContextMenuRequested.connect(self.delete_menu)
        self.listWidgetF1.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listWidgetF1.customContextMenuRequested.connect(self.delete_menu)
        self.listWidgetF2.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listWidgetF2.customContextMenuRequested.connect(self.delete_menu)

        self.lineEditE.textChanged.connect(self.plot_lines)
        self.lineEditF1.textChanged.connect(self.plot_lines)
        self.lineEditF2.textChanged.connect(self.plot_lines)

        self.clear_all()

        self.setWindowTitle(self.program_name)
        self.showMaximized()

    def clear_all(self):
        self.e_scatter = None
        self.f1_scatter = None
        self.f2_scatter = None

        self.e_critical = None
        self.f1_critical = None
        self.f2_critical = None

        self.iono = None
        self.file_name = None

        self.change_mode(0)

        self.lineEditE.setText('')
        self.lineEditF1.setText('')
        self.lineEditF2.setText('')

        self.listWidgetE.clear()
        self.listWidgetF1.clear()
        self.listWidgetF2.clear()

        self.radioButtonE.setChecked(True)

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
        self.lineEditE.setEnabled(False)
        self.listWidgetE.setEnabled(False)
        self.lineEditF1.setEnabled(False)
        self.listWidgetF1.setEnabled(False)
        self.lineEditF2.setEnabled(False)
        self.listWidgetF2.setEnabled(False)
        if mode == 0:
            self.lineEditE.setEnabled(True)
            self.listWidgetE.setEnabled(True)
        elif mode == 1:
            self.lineEditF1.setEnabled(True)
            self.listWidgetF1.setEnabled(True)
        elif mode == 2:
            self.lineEditF2.setEnabled(True)
            self.listWidgetF2.setEnabled(True)

    def onclick(self, event):
        if event.ydata and event.xdata:
            f = sqrt(2) ** (event.xdata / 2.5)
            h = event.ydata
            s = '{:-5.2f} {:-5.1f}'.format(f, h)
            f = '{:-5.2f}'.format(f)
            if event.button == 1:
                if self.mode == 0:  # E
                    self.listWidgetE.addItem(s)
                elif self.mode == 1:  # F1
                    self.listWidgetF1.addItem(s)
                elif self.mode == 2:  # F2
                    self.listWidgetF2.addItem(s)
            else:
                if self.mode == 0:  # E
                    self.lineEditE.setText(f)
                elif self.mode == 1:  # F1
                    self.lineEditF1.setText(f)
                elif self.mode == 2:  # F2
                    self.lineEditF2.setText(f)
            self.plot_scatter()

    def plot_scatter(self):
        if self.e_scatter is not None:
            self.e_scatter.remove()

        x_e = []
        y_e = []
        for i in range(self.listWidgetE.count()):
            t = self.listWidgetE.item(i).text().split()
            x_e.append(log(float(t[0]), sqrt(2)) * 2.5)
            y_e.append(float(t[1]))
        self.e_scatter = self.ax.scatter(x_e, y_e, c='g')

        if self.f1_scatter is not None:
            self.f1_scatter.remove()

        x_f1 = []
        y_f1 = []
        for i in range(self.listWidgetF1.count()):
            t = self.listWidgetF1.item(i).text().split()
            x_f1.append(log(float(t[0]), sqrt(2)) * 2.5)
            y_f1.append(float(t[1]))
        self.f1_scatter = self.ax.scatter(x_f1, y_f1, c='c')

        if self.f2_scatter is not None:
            self.f2_scatter.remove()

        x_f2 = []
        y_f2 = []
        for i in range(self.listWidgetF2.count()):
            t = self.listWidgetF2.item(i).text().split()
            x_f2.append(log(float(t[0]), sqrt(2)) * 2.5)
            y_f2.append(float(t[1]))
        self.f2_scatter = self.ax.scatter(x_f2, y_f2, c='r')

        self.canvas.draw()

    def plot_lines(self, text):

        if self.iono is None:
            return

        foE = self.lineEditE.text().strip()

        try:
            foE = float(foE)
        except ValueError:
            foE = 99.0

        if (foE > 1) and (foE < 22.6):
            if self.e_critical is not None:
                self.e_critical.remove()
                self.e_critical = None

            f = log(float(foE), sqrt(2)) * 2.5
            self.e_critical, = self.ax.plot([f, f], [50, 750], c='g')
        else:
            if self.e_critical is not None:
                self.e_critical.remove()
                self.e_critical = None

        foF1 = self.lineEditF1.text().strip()

        try:
            foF1 = float(foF1)
        except ValueError:
            foF1 = 99.0

        if (foF1 > 1) and (foF1 < 22.6):
            if self.f1_critical is not None:
                self.f1_critical.remove()
                self.f1_critical = None

            f = log(float(foF1), sqrt(2)) * 2.5
            self.f1_critical, = self.ax.plot([f, f], [50, 750], c='c')
        else:
            if self.f1_critical is not None:
                self.f1_critical.remove()
                self.f1_critical = None

        foF2 = self.lineEditF2.text().strip()

        try:
            foF2 = float(foF2)
        except ValueError:
            foF2 = 99.0

        if (foF2 > 1) and (foF2 < 22.6):
            if self.f2_critical is not None:
                self.f2_critical.remove()
                self.f2_critical = None

            f = log(float(foF2), sqrt(2)) * 2.5
            self.f2_critical, = self.ax.plot([f, f], [50, 750], c='r')
        else:
            if self.f2_critical is not None:
                self.f2_critical.remove()
                self.f2_critical = None

        self.canvas.draw()

    def onmove(self, event):
        if event.ydata and event.xdata:
            f = sqrt(2) ** (event.xdata / 2.5)
            h = event.ydata
            self.statusbar.showMessage('f={:-5.2f}  h\'={:-5.1f}'.format(f, h))
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

    def open_file(self, file_name):
        if file_name:
            self.clear_all()
            self.iono = UacIono()
            self.iono.load(file_name)
            data = self.iono.get_data()
            if data:

                self.file_name = file_name

                self.figure.clear()
                self.ax = self.figure.add_subplot(111)

                left = 0
                right = 22.5
                bottom = -2
                top = 796
                extent = [left, right, bottom, top]
                self.ax.imshow(data, cmap='hot', interpolation='nearest',
                               extent=extent, aspect='auto')
                # [1, 1.4, 2, 2.8, 4, 5.6, 8, 11.4, 16, 22.4]
                x = ['{:.1f}'.format(sqrt(2) ** i) for i in range(22)]
                self.ax.set_xticklabels(x)

                self.setWindowTitle(self.program_name + " - " + file_name)
                self.canvas.draw()

                self.station_name = 'UAC'
                self.coordinates = '-65.25 -64.25 0.97 -59 0'
                self.date = '2017 3 17 0 0 0'

                self.load_text_info()

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
            filenames = list(filter(lambda s: s.endswith('.ion'), filenames))
            return filenames

    def load_text_info(self):
        try:
            with open(self.file_name + '.STD', 'r') as file:
                self.station_name = file.readline().strip()
                self.coordinates = file.readline().strip()
                self.date = file.readline().strip()
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
            with open(self.file_name + '.STD', 'w') as file:
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

                file.write(self.station_name + '\n')
                file.write(self.coordinates + '\n')
                file.write(self.date + '\n')

                file.write(str(foE) + '\n')
                file.write(str(fohE))
                file.write('END\n')

                file.write(str(foF1) + '\n')
                file.write(str(fohF1))
                file.write('END\n')

                file.write(str(foF2) + '\n')
                file.write(str(fohF2))
                file.write('END\n')

            self.statusbar.showMessage('File is saved.')
            self.figure.savefig(self.file_name + '.png')

    def show_error(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(message)
        msg.setWindowTitle("Error")
        msg.show()
        msg.exec_()

    def show_about(self):
        about = """
        IonogramViewer2 version 1.1
        © 2018 Oleksandr Bogomaz
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(about)
        msg.setWindowTitle("About")
        msg.show()
        msg.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    main = MainWindow()
    main.show()

    sys.exit(app.exec_())
