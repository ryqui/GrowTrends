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
from formatItemName import appendItemNames

class Worker(QObject):
    finished = pyqtSignal()
    #progress = pyqtSignal(int)

    def __init__(self, currUI):
        QThread.__init__(self)
        self.currUI = currUI

    itemNamesFile = None
    discordFileName = None

    def run(self):
<<<<<<< Updated upstream
        #count = 0
        #while count<100:
        #    count += 1
        #    
        #    time.sleep(0.3)
        #    self.changeValue.emit(int)
        self.currUI.itemInformation = startAnalysis(self.itemNamesFile, self.discordFileName)
=======
        self.currUI.analysisResults = startAnalysis(self.itemNamesFile, self.discordFileName, self.currUI)
>>>>>>> Stashed changes
        self.currUI.runningAnalysis = False
        self.finished.emit()


class UI(QMainWindow):
    def __init__(self):
        super(UI,self).__init__()
        self.initUI()

    def initUI(self):
        uic.loadUi("UI//dialogue.ui", self)
        self.setWindowIcon(QtGui.QIcon('UI/GT_favicon.png'))
        self.window().setFixedSize(400, 265)

        self.itemNamesFile = None
        self.discordFileName = None
        self.workerRunning = False
        self.analysisResults = None
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
            if self.analysisResults:
                self.analysisResults = None
            if self.itemNamesFile:
                self.outputMessage("Processing raw item names...")
                appendItemNames(self.itemNamesFile, self.rawItemNamesFile)
                time.sleep(10)

            self.outputMessage("Running analysis...")
            
            self.analysisThread = QThread()
            self.analysisWorker = AnalysisThread(self)
            self.analysisWorker.moveToThread(self.analysisThread)

            self.workerRunning = True

            self.worker.itemNamesFile = self.itemNamesFile
            self.worker.discordFileName = self.discordFileName
            
            self.analysisThread.started.connect(self.analysisWorker.run)
            self.analysisWorker.finished.connect(self.analysisThread.quit)
            self.analysisWorker.finished.connect(lambda x = "Analysis Finished.": self.outputMessage(x, 1) if self.analysisResults else None)
            self.analysisWorker.finished.connect(self.analysisWorker.deleteLater)
            self.analysisThread.finished.connect(self.analysisThread.deleteLater)

            self.thread.start()
            self.runningAnalysis = True
            #self.workerRunning = self.thread.join()

    def saveFile(self):
        if self.savedTextVisible == True and self.analysisResults:
            self.bottomText.hide()
            self.savedTextVisible = True

        #only allow file saving if analysis has been completed successfully
        if self.analysisResults is not None:
            name = QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv)")
            
            if name[0]:
                try:
                    writeToFile(self.analysisResults, name[0], 1)
                    self.outputMessage("Saved Successfully.", 1)
                except PermissionError:
                    self.outputMessage("Unable to save file. File is open in another window.", -1)
                except:
                    self.outputMessage("Error saving file.", -1)

                self.savedTextVisible = True
    
    def outputMessage(self, message, messageType=0):
        self.bottomText.setText(message)
        self.bottomText.repaint()
        self.bottomText.show()
        if messageType == -1:
            self.bottomText.setStyleSheet("color: red;")
        elif messageType == 0:
            self.bottomText.setStyleSheet("color: white;")
        elif messageType == 1:
            self.bottomText.setStyleSheet("color: rgb(80,200,25);")

    def setProgress(self, val):
        self.progressBar.setValue(val)


def window():
    app = QApplication(sys.argv)
    UIWindow = UI()
    UIWindow.show()
    sys.exit(app.exec_())

window()