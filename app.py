from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, 
                             QFileDialog, QPushButton, QApplication, 
                             QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFontDatabase, QFont

import time
import sys
import os

from getPrices import startAnalysis, writeToFile

class Worker(QObject):
    finished = pyqtSignal()
    #progress = pyqtSignal(int)

    def __init__(self, currUI):
        QThread.__init__(self)
        self.currUI = currUI

    itemNamesFile = None
    discordFileName = None

    def run(self):
        #count = 0
        #while count<100:
        #    count += 1
        #    
        #    time.sleep(0.3)
        #    self.changeValue.emit(int)
        self.currUI.itemInformation = startAnalysis(self.itemNamesFile, self.discordFileName)
        self.finished.emit()
        self.currUI.runningAnalysis = False
        return False


class UI(QMainWindow):
    def __init__(self):
        super(UI,self).__init__()
        self.initUI()

    def initUI(self):
        uic.loadUi("UI//dialogue.ui", self)

        self.itemNamesFile = None
        self.discordFileName = None
        self.workerRunning = False
        self.itemInformation = None
        self.savedTextVisible = False
        self.runningAnalysis = False

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

        self.analyzePricesButton = self.findChild(QPushButton, "analyzePricesButton")
        self.analyzePricesButton.clicked.connect(self.runAnalysis)

        self.saveResultsButton = self.findChild(QPushButton, "saveResults")
        self.saveResultsButton.clicked.connect(self.saveFile)

        self.progressBar = self.findChild(QProgressBar, "progressBar")

        self.savedText = self.findChild(QLabel, "savedText")
        self.savedText.hide()


    def getDiscordFile(self):
        print("Getting discord file...")
        fileName = QFileDialog.getOpenFileName(self, "Open File", "", "JSON file (*.json)")
        if fileName:
            self.discordFileLabel.setText(os.path.basename(fileName[0]))
        #self.discordFileLabel.adjustSize()
        self.discordFileName = fileName[0]

    def getItemNamesFile(self):
        print("Getting item file...")
        fileName = QFileDialog.getOpenFileName(self, "Open File", "", "JSON file (*.json)")
        if fileName:
            self.itemNamesFileLabel.setText(os.path.basename(fileName[0]))
        #self.itemNamesFileLabel.adjustSize()
        self.itemNamesFile = fileName[0]
    
    def getRawItemNamesFile(self):
        print("Getting raw item file...")
        fileName = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*.*)")
        if fileName:
            self.rawItemNamesFileLabel.setText(os.path.basename(fileName[0]))
        #self.rawItemNamesFileLabel.adjustSize()
        self.rawItemNamesFile = fileName[0]

    def runAnalysis(self):
        if self.itemNamesFile and self.discordFileName and not self.runningAnalysis:
            self.thread = QThread()
            self.worker = Worker(self)
            self.worker.moveToThread(self.thread)

            self.workerRunning = True

            self.worker.itemNamesFile = self.itemNamesFile
            self.worker.discordFileName = self.discordFileName
            
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)

            self.thread.start()
            self.runningAnalysis = True
            #self.workerRunning = self.thread.join()

    def saveFile(self):
        if self.savedTextVisible == True:
            self.savedText.hide()
            self.savedTextVisible = True
        if self.itemInformation is not None:
            name = QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv)")
            if name[0]:
                writeToFile(self.itemInformation, name[0], 1)
                self.savedText.show()
                self.savedTextVisible = True
            else:
                self.savedText.hide()
                self.savedTextVisible = False

    #def startProgressBar(self):
        #self.thread = MyThread()
        #self.thread.changeValue.connect(self.setProgress)
        #self.thread.start()

    def setProgress(self, val):
        self.progressBar.setValue(val)


def window():
    app = QApplication(sys.argv)
    UIWindow = UI()
    UIWindow.show()
    sys.exit(app.exec_())

window()