#!/usr/bin/python3

import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg
import PyQt5.QtCore as qtc

import pyqtgraph as pg
import serial
import struct
import numpy as np
import json


FILENAME_SERIAL = '/dev/ttyACM0'


class MainWindow(qtw.QMainWindow):

    def __init__(self):
        qtw.QMainWindow.__init__(self)

        self.widget = MainWidget()
        self.setCentralWidget(self.widget)

    def keyPressEvent(self, e):
        if e.key() == qtc.Qt.Key_Space:
            self.widget.start_stop()

class MainWidget(qtw.QWidget):

    def __init__(self):
        qtw.QWidget.__init__(self)

        self.l1 = qtw.QLabel('Streams')
        self.l1.setAlignment(qtc.Qt.AlignCenter)

        self.stream_widget = pg.GraphicsLayoutWidget()
        self.streams = []
        self.streams.append(self.stream_widget.addPlot(row=0, col=0))
        self.streams.append(self.stream_widget.addPlot(row=1, col=0))
        self.streams.append(self.stream_widget.addPlot(row=2, col=0))
        self.streams.append(self.stream_widget.addPlot(row=3, col=0))
        for stream in self.streams:
            stream.setYRange(0, 400)

        self.start_stop_button = qtw.QPushButton('Start')
        self.start_stop_button.clicked.connect(self.start_stop)

        self.layout = qtw.QVBoxLayout()
        self.layout.addWidget(self.l1)
        self.layout.addWidget(self.stream_widget)
        self.layout.addWidget(self.start_stop_button)

        self.setLayout(self.layout)

        self.setWindowTitle('Quadrant Data Visualizer')
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        self.running = False

        self.refresh_timer = qtc.QTimer()
        self.refresh_timer.timeout.connect(self.refresh)

        self.quadrant = serial.Serial(FILENAME_SERIAL, 115200, timeout=0.025)
        self.databuf = np.zeros((4,512), dtype=np.int32)

    def start_stop(self):
        if self.running:
            self.refresh_timer.stop()
            self.running = False
            self.start_stop_button.setText('Start')
        else:
            self.refresh_timer.start(50)
            self.running = True
            self.start_stop_button.setText('Stop')

    def refresh(self):
        while self.quadrant.in_waiting:
            report_raw = self.quadrant.readline();
            try:
                report = json.loads(report_raw)
            except json.decoder.JSONDecodeError:
                print('dropped some data')
                continue
            distance = [report[s]['distance'] for s in ('lidar0', 'lidar1', 'lidar2', 'lidar3')]
            engaged = [report[s]['engaged'] for s in ('lidar0', 'lidar1', 'lidar2', 'lidar3')]
            datanew = np.array(distance, dtype=np.int32).reshape(4,1)
            self.databuf = np.concatenate((self.databuf[:,1:], datanew), axis=1)
            for i in range(4):
                self.streams[i].clear()
                self.streams[i].plot(self.databuf[i,:])


if __name__ == '__main__':

    app = qtw.QApplication([])
    win = MainWindow()
    win.show()
    app.exec()

