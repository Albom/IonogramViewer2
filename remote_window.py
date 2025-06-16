from datetime import datetime
from PySide6.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QDialog,
)
from ui_RemoteWnd import Ui_Remote
from shigaraki_loader import ShigarakiLoader

DATE_TIME_FORMAT = "yyyy-MM-dd hh:mm"

class RemoteWindow(QDialog, Ui_Remote):

    def __init__(self):
        super().__init__()

        self.setupUi(self)

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
                msg.setText(f"{n_files} file(s) loaded.")
                msg.setWindowTitle("Remote")
                msg.show()
                msg.exec()
