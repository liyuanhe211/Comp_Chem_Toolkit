# -*- coding: utf-8 -*-
import sys
from PyQt5 import Qt

if __name__ == '__main__':
    Application = Qt.QApplication(sys.argv)
    from Drag_drop_window import Ui_Form

class override_textEdit(Qt.QTextEdit):
    drop_accepted_signal = Qt.pyqtSignal(str)
    def __init__(self):
        super(override_textEdit,self).__init__()
        self.setText("123")
        self.setAcceptDrops(True)

    def dropEvent(self, event):
        if len(event.mimeData().urls())==1:
            event.accept()
            self.drop_accepted_signal.emit(event.mimeData().urls()[0].toLocalFile())

        else:
            Qt.QMessageBox.critical(self,"Accept Single File Only","Accept Single File Only",Qt.QMessageBox.Abort)

            event.ignore()

class myWidget(Qt.QWidget):
    def __init__(self):
        super(myWidget, self).__init__()
        self.main = Ui_Form()
        self.main.setupUi(self)

        self.main.textEdit = override_textEdit()
        self.main.verticalLayout.addWidget(self.main.textEdit)
        self.main.textEdit.drop_accepted_signal.connect(self.test)

        self.show()

    def test(self,filename):
        self.main.lineEdit.setText(filename)



if __name__ == '__main__':
    my_Qt_Program = myWidget()

    my_Qt_Program.show()
    sys.exit(Application.exec_())