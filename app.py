from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QFileDialog, QPushButton, QApplication
import sys
import os

class UI(QMainWindow):
    def __init__(self):
        super(UI,self).__init__()
        self.initUI()

    def initUI(self):
        uic.loadUi("UI//dialogue.ui", self)

        #discord file button
        self.discordFileButton = self.findChild(QPushButton, "selectDiscordDataFile")
        self.discordFileLabel = self.findChild(QLabel, "discordDataFileName")

        self.discordFileButton.clicked.connect(self.getDiscordFile)

        #item names file button
        self.itemNamesButton = self.findChild(QPushButton, "selectItemNamesFile")
        self.itemNamesFileLabel = self.findChild(QLabel, "itemNamesFileName")

        self.itemNamesButton.clicked.connect(self.getItemNamesFile)

        self.rawItemNamesButton = self.findChild(QPushButton, "selectRawItemNamesFile")
        self.rawItemNamesFileLabel = self.findChild(QLabel, "rawItemNamesFileName")

        self.rawItemNamesButton.clicked.connect(self.getRawItemNamesFile)


    def getDiscordFile(self):
        print("Getting discord file...")
        fileName = QFileDialog.getOpenFileName(self, "Open File", "", "JSON file (*.json)")
        if fileName:
            self.discordFileLabel.setText(os.path.basename(fileName[0]))
        self.discordFileLabel.adjustSize()

    def getItemNamesFile(self):
        print("Getting item file...")
        fileName = QFileDialog.getOpenFileName(self, "Open File", "", "JSON file (*.json)")
        if fileName:
            self.itemNamesFileLabel.setText(os.path.basename(fileName[0]))
        self.itemNamesFileLabel.adjustSize()
    
    def getRawItemNamesFile(self):
        print("Getting discord file...")
        fileName = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*.*)")
        if fileName:
            self.rawItemNamesFileLabel.setText(os.path.basename(fileName[0]))
        self.rawItemNamesFileLabel.adjustSize()

def window():
    app = QApplication(sys.argv)
    UIWindow = UI()
    UIWindow.show()
    sys.exit(app.exec_())

window()