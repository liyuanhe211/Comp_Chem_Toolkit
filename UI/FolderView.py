# -*- coding: utf-8 -*-
__author__ = 'LiYuanhe'

import sys
import os
import math
import copy
import shutil
import re
import time
import random
from datetime import datetime

from My_Lib import *
from PyQt5 import Qt
from PyQt5 import uic
from PIL import Image
from PIL import ImageDraw
from PIL import ImageEnhance

from PyQt5 import Qt

class FolderView(Qt.QWidget):
    double_click = Qt.pyqtSignal()
    def __init__(self,root_path,index=""):
        super(self.__class__, self).__init__()

        self.model = Qt.QFileSystemModel(self)

        self.model.setRootPath(root_path)
        self.model.setFilter(Qt.QDir.AllDirs|Qt.QDir.NoDotAndDotDot)
        self.model.setReadOnly(True)

        self.indexRoot = self.model.index(self.model.rootPath())

        self.treeView = Qt.QTreeView(self)
        self.treeView.setModel(self.model)
        self.treeView.setRootIndex(self.indexRoot)
        connect_once(self.treeView.doubleClicked,self.double_clicked)
        # self.treeView.clicked.connect(self.on_treeView_clicked)

        self.header =self.treeView.header()
        self.header.hideSection(1)
        self.header.hideSection(2)
        self.header.hideSection(3)

        self.treeView.resizeColumnToContents(0)

        self.layout = Qt.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0,0, 0)
        self.layout.addWidget(self.treeView)

        self.chosen_filename = ""

        # self.resize(300,500)

        font = Qt.QFont()
        font.setFamily("Microsoft YaHei UI")
        font.setPointSize(10)
        self.treeView.setFont(font)

    def double_clicked(self,index):
        indexItem = self.model.index(index.row(), 0, index.parent())
        self.chosen_path =self.model.filePath(indexItem)
        print(self.chosen_path)
        self.double_click.emit()

    def index_to(self,index):
        print(index)
        index = self.model.index(index)
        self.treeView.expand(index)
        self.treeView.scrollTo(index)
        self.treeView.setCurrentIndex(index)


    # @Qt.pyqtSlot(Qt.QModelIndex)
    # def on_treeView_clicked(self, index):
    #     indexItem = self.model.index(index.row(), 0, index.parent())
    #     fileName = self.model.fileName(indexItem)
    #     print(fileName)

if __name__ == "__main__":
    import sys

    app = Qt.QApplication(sys.argv)

    main = FolderView('D:\gaussian')
    main.move(app.desktop().screen().rect().center() - main.rect().center())
    main.show()

    sys.exit(app.exec_())