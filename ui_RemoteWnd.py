# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'RemoteWndheTEKb.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QDateTimeEdit, QDialog,
    QGroupBox, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QWidget)

class Ui_Remote(object):
    def setupUi(self, Remote):
        if not Remote.objectName():
            Remote.setObjectName(u"Remote")
        Remote.resize(350, 270)
        Remote.setMinimumSize(QSize(350, 270))
        Remote.setMaximumSize(QSize(350, 270))
        self.endDateTimeEdit = QDateTimeEdit(Remote)
        self.endDateTimeEdit.setObjectName(u"endDateTimeEdit")
        self.endDateTimeEdit.setGeometry(QRect(100, 200, 221, 22))
        self.endDateTimeEdit.setDateTime(QDateTime(QDate(2015, 1, 1), QTime(0, 0, 0)))
        self.startDateTimeEdit = QDateTimeEdit(Remote)
        self.startDateTimeEdit.setObjectName(u"startDateTimeEdit")
        self.startDateTimeEdit.setGeometry(QRect(100, 170, 221, 22))
        self.startDateTimeEdit.setDateTime(QDateTime(QDate(2015, 1, 1), QTime(0, 0, 0)))
        self.sourceComboBox = QComboBox(Remote)
        self.sourceComboBox.setObjectName(u"sourceComboBox")
        self.sourceComboBox.setGeometry(QRect(100, 20, 221, 22))
        self.proxyGroupBox = QGroupBox(Remote)
        self.proxyGroupBox.setObjectName(u"proxyGroupBox")
        self.proxyGroupBox.setEnabled(True)
        self.proxyGroupBox.setGeometry(QRect(10, 80, 321, 80))
        self.proxyGroupBox.setCheckable(True)
        self.proxyGroupBox.setChecked(False)
        self.label = QLabel(self.proxyGroupBox)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 20, 47, 13))
        self.proxyHostLineEdit = QLineEdit(self.proxyGroupBox)
        self.proxyHostLineEdit.setObjectName(u"proxyHostLineEdit")
        self.proxyHostLineEdit.setGeometry(QRect(80, 20, 221, 20))
        self.proxyPortLineEdit = QLineEdit(self.proxyGroupBox)
        self.proxyPortLineEdit.setObjectName(u"proxyPortLineEdit")
        self.proxyPortLineEdit.setGeometry(QRect(80, 50, 221, 20))
        self.label_2 = QLabel(self.proxyGroupBox)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(10, 50, 47, 13))
        self.label_3 = QLabel(Remote)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(20, 20, 47, 13))
        self.label_4 = QLabel(Remote)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(20, 170, 71, 16))
        self.label_5 = QLabel(Remote)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(20, 200, 61, 16))
        self.importButton = QPushButton(Remote)
        self.importButton.setObjectName(u"importButton")
        self.importButton.setGeometry(QRect(250, 240, 75, 23))
        self.ionosondeComboBox = QComboBox(Remote)
        self.ionosondeComboBox.setObjectName(u"ionosondeComboBox")
        self.ionosondeComboBox.setGeometry(QRect(100, 50, 221, 22))
        self.label_6 = QLabel(Remote)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(20, 40, 71, 16))

        self.retranslateUi(Remote)

        QMetaObject.connectSlotsByName(Remote)
    # setupUi

    def retranslateUi(self, Remote):
        Remote.setWindowTitle(QCoreApplication.translate("Remote", u"Remote", None))
        self.proxyGroupBox.setTitle(QCoreApplication.translate("Remote", u"Proxy", None))
        self.label.setText(QCoreApplication.translate("Remote", u"Host", None))
        self.label_2.setText(QCoreApplication.translate("Remote", u"Port", None))
        self.label_3.setText(QCoreApplication.translate("Remote", u"Source", None))
        self.label_4.setText(QCoreApplication.translate("Remote", u"Start (UTC)", None))
        self.label_5.setText(QCoreApplication.translate("Remote", u"End (UTC)", None))
        self.importButton.setText(QCoreApplication.translate("Remote", u"Import...", None))
        self.label_6.setText(QCoreApplication.translate("Remote", u"Ionosonde", None))
    # retranslateUi

