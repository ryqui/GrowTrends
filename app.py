import sys
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication, QWidget, QMainWindow

from getPrices import *

class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(200, 200, 500, 300)
        self.setWindowTitle("GrowTrends")
        self.initUi()

    def initUi(self):
        self.label = QtWidgets.QLabel(self)
        self.label.setText("hola")
        self.label.move(20, 10)

        self.b1 = QtWidgets.QPushButton(self)
        self.b1.setText("Click here to process the pet data")
        self.b1.move(20, 40)
        self.b1.clicked.connect(self.clicked)
    
    def clicked(self):
        self.label.setText("pressed!")
        print("hello")
        self.update()
    
    def update(self):
        self.label.adjustSize()

def window():
    app = QApplication(sys.argv)
    win = Window()

    win.show()
    sys.exit(app.exec_())

window()