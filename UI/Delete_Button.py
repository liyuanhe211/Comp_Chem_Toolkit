# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI/Delete_Button.ui'
#
# Created by: PyQt5 UI code generator 5.5
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Delete_pushButton(object):
    def setupUi(self, Delete_pushButton):
        Delete_pushButton.setObjectName("Delete_pushButton")
        Delete_pushButton.resize(96, 28)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Delete_pushButton.sizePolicy().hasHeightForWidth())
        Delete_pushButton.setSizePolicy(sizePolicy)
        Delete_pushButton.setMinimumSize(QtCore.QSize(75, 0))
        self.horizontalLayout = QtWidgets.QHBoxLayout(Delete_pushButton)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.load_file_pushButton = QtWidgets.QPushButton(Delete_pushButton)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.load_file_pushButton.sizePolicy().hasHeightForWidth())
        self.load_file_pushButton.setSizePolicy(sizePolicy)
        self.load_file_pushButton.setMinimumSize(QtCore.QSize(0, 28))
        font = QtGui.QFont()
        font.setFamily("Consolas")
        font.setPointSize(11)
        self.load_file_pushButton.setFont(font)
        self.load_file_pushButton.setObjectName("load_file_pushButton")
        self.horizontalLayout.addWidget(self.load_file_pushButton)

        self.retranslateUi(Delete_pushButton)
        QtCore.QMetaObject.connectSlotsByName(Delete_pushButton)

    def retranslateUi(self, Delete_pushButton):
        _translate = QtCore.QCoreApplication.translate
        Delete_pushButton.setWindowTitle(_translate("Delete_pushButton", "Form"))
        self.load_file_pushButton.setText(_translate("Delete_pushButton", "Delete"))

