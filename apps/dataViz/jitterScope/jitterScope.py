#!/usr/bin/python3

import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg
import PyQt5.QtCore as qtc

import pyqtgraph as pg
import serial
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

        self.setWindowTitle('JitterScope (Quadrant: %s)' % FILENAME_SERIAL)
        self.setMinimumWidth(800)
        self.setMinimumHeight(300)

    def keyPressEvent(self, e):
        self.widget.keyPressEvent(e)


class GraphingWidget(qtw.QFrame):

    def __init__(self):
        super().__init__()
        self.setFrameStyle(qtw.QFrame.Box | qtw.QFrame.Plain)
        self.setLineWidth(2)

        self.pgwidget = pg.GraphicsLayoutWidget()
        self.pgwidget.installEventFilter(self)

        self.plots = []
        self.plots.append(self.pgwidget.addPlot(row=0, col=0))

        self.labels= []
        for i in range(1):
            label = pg.LabelItem(f"<b>Channel {i}</b>", size="10pt") 
            label.setParentItem(self.plots[i].getViewBox())
            label.anchor(itemPos=(0.5,0.), parentPos=(0.5,0.01))
            label.html = True
            self.labels.append(label)

        self.reset_zoom()

        self.layout = qtw.QVBoxLayout()
        self.layout.addWidget(self.pgwidget)

        self.setLayout(self.layout)

    def reset_zoom(self):
        for plot in self.plots:
            plot.setXRange(0, 512)
            plot.setYRange(0, 100)

    def update_data(self, data):
        #data is of type np.zeros(512, dtype=np.float32)
        for i in range(1):
            self.plots[i].clear()
            self.plots[i].plot(data)
            cur = data[-1]
            mean = np.mean(data[-50:])
            std = np.std(data[-50:])
            self.labels[i].setText(f"<b>Sample Rate = {cur:.1f}</b> (mean={mean:.1f}, std={std:.1f})")

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

        self.graphing_widget = GraphingWidget()
        self.layout = qtw.QHBoxLayout()
        self.layout.addWidget(self.graphing_widget)
        self.setLayout(self.layout)

        self.running = False

        self.refresh_timer = qtc.QTimer()
        self.refresh_timer.timeout.connect(self.refresh)

        self.quadrant = serial.Serial(FILENAME_SERIAL, 115200, timeout=0.025)
        self.databuf = np.zeros(512, dtype=np.float32)

        self.tlast = None
        self.tnow = None

    def start_stop(self):
        if self.running:
            self.refresh_timer.stop()
            self.running = False
            #self.start_stop_button.setText('Start')
        else:
            self.refresh_timer.start(15)
            self.running = True
            #self.start_stop_button.setText('Stop')

    def refresh(self):
        while self.quadrant.in_waiting:
            report_raw = self.quadrant.readline();
            try:
                report = json.loads(report_raw)
                self.tlast = self.tnow
                self.tnow = report['ts']
                if all(t is not None for t in [self.tlast, self.tnow]):
                    datanew = np.array([1e6/(self.tnow - self.tlast)], dtype=np.float32)
                    self.databuf = np.concatenate((self.databuf[1:], datanew))
                    self.graphing_widget.update_data(self.databuf)
            except json.decoder.JSONDecodeError:
                print('dropped some data')
                continue
            except KeyError:
                continue

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

