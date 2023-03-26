from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, 
                             QFileDialog, QPushButton, QApplication, 
                             QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFontDatabase, QFont

import time
import sys
import os

from getPrices import startAnalysis, writeToFile

class AnalysisWorker(QObject):
    finished = pyqtSignal()
    #progress = pyqtSignal(int)

    def __init__(self, currUI):
        QThread.__init__(self)
        self.currUI = currUI

    itemNamesFile = None
    discordFileName = None

    def run(self):
        self.currUI.itemInformation = startAnalysis(self.itemNamesFile, self.discordFileName, self.currUI)
        self.currUI.runningAnalysis = False
        self.finished.emit()

class ProgressThread(QThread):
    progressSignal = pyqtSignal(int)
    #progress = pyqtSignal(int)

    def __init__(self, currUI):
        QThread.__init__(self)
        self.currUI = currUI

    def __del__(self):
        self.wait()

    def run(self):
        currValue = 0
        while True:
            if currValue == self.currUI.progress:
                time.sleep(0.001)
                continue
            currValue = self.currUI.progress
            self.progressSignal.emit(self.currUI.progress)
            time.sleep(0.01)


class UI(QMainWindow):
    def __init__(self):
        super(UI,self).__init__()
        self.initUI()

    def initUI(self):
        uic.loadUi(os.path.join(os.path.dirname(__file__), "UI\\dialogue.ui"), self)
        #self.setWindowIcon(QtGui.QIcon('UI/GT_favicon.png'))
        self.window().setFixedSize(400, 265)

        self.itemNamesFile = None
        self.discordFileName = None
        self.workerRunning = False
        self.itemInformation = None
        self.savedTextVisible = False
        self.runningAnalysis = False
        self.progress = 0

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
        fileName = QFileDialog.getOpenFileName(self, "Open File", "", "JSON file (*.json)")
        if fileName:
            self.discordFileLabel.setText(os.path.basename(fileName[0]))
        #self.discordFileLabel.adjustSize()
        self.discordFileName = fileName[0]

    def getItemNamesFile(self):
        fileName = QFileDialog.getOpenFileName(self, "Open File", "", "JSON file (*.json)")
        if fileName:
            self.itemNamesFileLabel.setText(os.path.basename(fileName[0]))
        #self.itemNamesFileLabel.adjustSize()
        self.itemNamesFile = fileName[0]
    
    def getRawItemNamesFile(self):
        fileName = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*.*)")
        if fileName:
            self.rawItemNamesFileLabel.setText(os.path.basename(fileName[0]))
        #self.rawItemNamesFileLabel.adjustSize()
        self.rawItemNamesFile = fileName[0]

    def runAnalysis(self):
        if self.itemNamesFile and self.discordFileName and not self.runningAnalysis:
            self.analysisThread = QThread()
            self.analysisWorker = AnalysisWorker(self)
            self.analysisWorker.moveToThread(self.analysisThread)

            self.workerRunning = True

            self.analysisWorker.itemNamesFile = self.itemNamesFile
            self.analysisWorker.discordFileName = self.discordFileName
            
            self.analysisThread.started.connect(self.analysisWorker.run)
            self.analysisWorker.finished.connect(self.analysisThread.quit)
            self.analysisWorker.finished.connect(self.analysisWorker.deleteLater)
            self.analysisThread.finished.connect(self.analysisThread.deleteLater)

            self.analysisThread.start()
            self.runningAnalysis = True
            self.startProgressBar()

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

    def startProgressBar(self):
        self.progress = 0
        self.progressThread = ProgressThread(self)
        self.progressThread.start()
        self.progressThread.progressSignal.connect(self.setProgress)

    def setProgress(self):
        if self.progress <= 100:
            self.progressBar.setValue(self.progress)

def window():
    app = QApplication(sys.argv)
    UIWindow = UI()
    UIWindow.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    window()