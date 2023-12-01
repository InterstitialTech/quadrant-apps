#!/usr/bin/python3

import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg
import PyQt5.QtCore as qtc

import pyqtgraph as pg
import serial
import struct
import numpy as np
import json
import sys


if len(sys.argv) <= 1:
    FILENAME_SERIAL = '/dev/ttyACM0'
else:
    FILENAME_SERIAL = sys.argv[1]


class MainWindow(qtw.QMainWindow):

    def __init__(self):
        qtw.QMainWindow.__init__(self)

        self.widget = MainWidget()
        self.setCentralWidget(self.widget)

    def keyPressEvent(self, e):
        self.widget.keyPressEvent(e)


class GraphingWidget(qtw.QWidget):

    def __init__(self):
        qtw.QWidget.__init__(self)

        self.pgwidget = pg.GraphicsLayoutWidget()
        self.pgwidget.installEventFilter(self)

        self.plots = []
        self.plots.append(self.pgwidget.addPlot(row=0, col=0))
        self.plots.append(self.pgwidget.addPlot(row=1, col=0))
        self.plots.append(self.pgwidget.addPlot(row=2, col=0))
        self.plots.append(self.pgwidget.addPlot(row=3, col=0))
        self.reset_zoom()

        self.link_axes()
        self.axes_linked = True

        self.layout = qtw.QVBoxLayout()
        self.layout.addWidget(self.pgwidget)

        self.setLayout(self.layout)

    def link_axes(self):
        for i in range(4):
            if i != 0:
                self.plots[i].setXLink(self.plots[0])
                self.plots[i].setYLink(self.plots[0])

    def unlink_axes(self):
        for plot in self.plots:
            vb = plot.getViewBox()
            vb.linkView(vb.XAxis, None)
            vb.linkView(vb.YAxis, None)

    def toggle_axes_linked(self):
        if self.axes_linked:
            self.unlink_axes()
            self.axes_linked = False
        else:
            self.link_axes()
            self.axes_linked = True

    def reset_zoom(self):
        for plot in self.plots:
            plot.setXRange(0, 512)
            plot.setYRange(0, 400)

    def update_data(self, data):
        #data is of type np.zeros((4,512), dtype=np.int32)
        for i in range(4):
            self.plots[i].clear()
            self.plots[i].plot(data[i,:])

    def eventFilter(self, target, e):
        if (target is self.pgwidget):
            if (e.type() == e.MouseButtonPress):
                if e.button() == qtc.Qt.MouseButton.MiddleButton:
                    self.reset_zoom()
                    return True
        return False


class MainWidget(qtw.QWidget):

    def __init__(self):
        qtw.QWidget.__init__(self)

        self.l1 = qtw.QLabel('Streams')
        self.l1.setAlignment(qtc.Qt.AlignCenter)

        self.graphing_widget = GraphingWidget()

        self.start_stop_button = qtw.QPushButton('Start')
        self.start_stop_button.clicked.connect(self.start_stop)

        self.layout = qtw.QVBoxLayout()
        self.layout.addWidget(self.l1)
        self.layout.addWidget(self.graphing_widget)
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
            self.graphing_widget.update_data(self.databuf)

    def keyPressEvent(self, e):
        if e.key() == qtc.Qt.Key_Space:
            self.start_stop()
        elif e.key() == qtc.Qt.Key_Escape:
            self.graphing_widget.toggle_axes_linked()


if __name__ == '__main__':

    app = qtw.QApplication([])
    win = MainWindow()
    win.show()
    app.exec()

