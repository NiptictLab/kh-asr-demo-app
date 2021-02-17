import os
import json
import sys

import wave
import pyaudio
from vosk import Model, KaldiRecognizer

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QApplication
from PyQt5.QtCore import QThread


class Ui_MainWindow(object):

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        MainWindow.setMinimumSize(QtCore.QSize(800, 600))
        MainWindow.setMaximumSize(QtCore.QSize(800, 600))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setEnabled(True)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.fileLabel = QtWidgets.QLabel(self.centralwidget)
        self.fileLabel.setObjectName("fileLabel")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.fileLabel)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.file_path = QtWidgets.QLineEdit(self.centralwidget)
        self.file_path.setObjectName("file_path")
        self.horizontalLayout.addWidget(self.file_path)
        self.btn_browse = QtWidgets.QPushButton(self.centralwidget)
        self.btn_browse.setObjectName("btn_browse")
        self.horizontalLayout.addWidget(self.btn_browse)
        self.formLayout.setLayout(0, QtWidgets.QFormLayout.FieldRole, self.horizontalLayout)
        self.outputLabel = QtWidgets.QLabel(self.centralwidget)
        self.outputLabel.setObjectName("outputLabel")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.outputLabel)
        self.txt_output = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.txt_output.setEnabled(True)
        self.txt_output.setMinimumSize(QtCore.QSize(0, 500))
        self.txt_output.setMaximumSize(QtCore.QSize(16777215, 500))
        self.txt_output.setObjectName("txt_output")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.txt_output)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.btn_decode = QtWidgets.QPushButton(self.centralwidget)
        self.btn_decode.setMaximumSize(QtCore.QSize(2000, 16777215))
        self.btn_decode.setObjectName("btn_decode")
        self.horizontalLayout_2.addWidget(self.btn_decode)
        self.formLayout.setLayout(2, QtWidgets.QFormLayout.FieldRole, self.horizontalLayout_2)
        self.verticalLayout.addLayout(self.formLayout)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.worker = DecodeWorker()
        self.worker.decode_partial.connect(self.decode_partial_trans)
        self.worker.decode.connect(self.decode_trans)
        self.worker.decode_done.connect(self.decode_done)
        self.decode = False
        self.text = ''

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Khmer ASR Demo"))
        self.fileLabel.setText(_translate("MainWindow", "FILE"))
        self.btn_browse.setText(_translate("MainWindow", "BROWSE"))
        self.outputLabel.setText(_translate("MainWindow", "OUTPUT"))
        self.btn_decode.setText(_translate("MainWindow", "DECODE"))

    def setupEvent(self):
        self.btn_browse.clicked.connect(self.on_btn_browse_clicked)
        self.btn_decode.clicked.connect(self.on_btn_decode_clicked)

    def on_btn_browse_clicked(self):
        file_name, _ = QFileDialog.getOpenFileName(self.centralwidget, 'Open WAV File', r"<Default dir>",
                                                   "Wav files (*.wav)")

        self.file_path.setText(os.path.basename(file_name))
        self.wav_path = file_name

    def on_btn_decode_clicked(self):
        if self.decode is False:
            self.worker.set_wav_file(self.wav_path)
            self.worker.start()

            self.txt_output.setPlainText('')
            self.btn_decode.setText('STOP')
            QApplication.processEvents()

            self.text = ''
            self.decode = True
        else:
            self.worker.terminate()

            self.btn_decode.setText('DECODE')
            QApplication.processEvents()

            self.decode = False

    def decode_partial_trans(self, trans):
        final_trans = self.text + '\n' + trans

        self.txt_output.setPlainText(final_trans.strip())
        self.txt_output.verticalScrollBar().setValue(self.txt_output.verticalScrollBar().maximum())
        QApplication.processEvents()

    def decode_trans(self, trans):
        self.text += '\n' + trans
        print(self.text)

    def decode_done(self):
        self.btn_decode.setText('DECODE')
        QApplication.processEvents()

        self.decode = False

class DecodeWorker(QThread):
    decode = QtCore.pyqtSignal(str)
    decode_partial = QtCore.pyqtSignal(str)
    decode_done = QtCore.pyqtSignal(str)

    decode_file = None

    def __init__(self):
        super(DecodeWorker, self).__init__()

    def set_wav_file(self, wav_file):
        self.decode_file = wav_file

    def run(self):
        chunk = 1024
        p_audio = pyaudio.PyAudio()
        wf = wave.open(self.decode_file, 'rb')

        stream = p_audio.open(format=p_audio.get_format_from_width(wf.getsampwidth()), channels=wf.getnchannels(),
                              rate=wf.getframerate(), output=True)

        recognizer = KaldiRecognizer(model, 16000)
        while True:
            # read data in chunks
            data = wf.readframes(chunk)
            if len(data) == 0:
                break

            # play the sound by writing the audio data to the stream
            stream.write(data)

            # decode wav
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get('text')

                self.decode.emit(text)
            else:
                result = json.loads(recognizer.PartialResult())
                trans = result.get('partial')
                if trans == '':
                    continue

                self.decode_partial.emit(trans)

        self.decode_done.emit('')

        # close the stream
        p_audio.terminate()
        stream.close()


model = Model('../resource/model')

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()

    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    ui.setupEvent()

    MainWindow.show()
    sys.exit(app.exec_())
