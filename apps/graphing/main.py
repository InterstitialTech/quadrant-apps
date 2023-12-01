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

        self.setWindowTitle('Quadrant Data Visualizer (%s)' % FILENAME_SERIAL)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

    def keyPressEvent(self, e):
        self.widget.keyPressEvent(e)


class CBLabel(qtw.QLabel):

    def __init__(self, text):
        super().__init__(text)
        self.setAlignment(qtc.Qt.AlignCenter)
        self.font = qtg.QFont()
        self.font.setBold(True)
        self.setFont(self.font)


class GraphingWidget(qtw.QFrame):

    def __init__(self):
        super().__init__()
        self.setFrameStyle(qtw.QFrame.Box | qtw.QFrame.Plain)
        self.setLineWidth(2)

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


class ElevationWidget(qtw.QFrame):

    def __init__(self):
        super().__init__()
        self.setFrameStyle(qtw.QFrame.Box | qtw.QFrame.Plain)
        self.setLineWidth(2)
        self.label = CBLabel('[elevation]')
        self.layout = qtw.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def update_report(self, report_dict):
        value = report_dict['value']
        engaged = report_dict['engaged']
        if engaged:
            self.label.setText('Elevation:\n%1.3f' % value)
        else:
            self.label.setText('[elevation]')


class PitchWidget(qtw.QFrame):

    def __init__(self):
        super().__init__()
        self.setFrameStyle(qtw.QFrame.Box | qtw.QFrame.Plain)
        self.setLineWidth(2)
        self.label = CBLabel('[pitch]')
        self.layout = qtw.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def update_report(self, report_dict):
        value = report_dict['value']
        engaged = report_dict['engaged']
        if engaged:
            self.label.setText('Pitch:\n%1.3f' % value)
        else:
            self.label.setText('[pitch]')


class RollWidget(qtw.QFrame):

    def __init__(self):
        super().__init__()
        self.setFrameStyle(qtw.QFrame.Box | qtw.QFrame.Plain)
        self.setLineWidth(2)
        self.label = CBLabel('[roll]')
        self.layout = qtw.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def update_report(self, report_dict):
        value = report_dict['value']
        engaged = report_dict['engaged']
        if engaged:
            self.label.setText('Roll:\n%1.3f' % value)
        else:
            self.label.setText('[roll]')


class ArcWidget(qtw.QFrame):

    def __init__(self):
        super().__init__()
        self.setFrameStyle(qtw.QFrame.Box | qtw.QFrame.Plain)
        self.setLineWidth(2)
        self.label = CBLabel('[arc]')
        self.layout = qtw.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def update_report(self, report_dict):
        value = report_dict['value']
        engaged = report_dict['engaged']
        if engaged:
            self.label.setText('Arc:\n%1.3f' % value)
        else:
            self.label.setText('[arc]')


class SampleRateWidget(qtw.QFrame):

    def __init__(self):
        super().__init__()
        self.setFrameStyle(qtw.QFrame.Box | qtw.QFrame.Plain)
        self.setLineWidth(2)
        self.label = CBLabel('[sample rate]')
        self.layout = qtw.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def update_value(self, value):
        self.label.setText('Sample Rate:\n%1.3f' % value)


class MainWidget(qtw.QWidget):

    def __init__(self):
        qtw.QWidget.__init__(self)

        self.l1 = qtw.QLabel('Streams')
        self.l1.setAlignment(qtc.Qt.AlignCenter)

        self.graphing_widget = GraphingWidget()
        self.elevation_widget = ElevationWidget()
        self.pitch_widget = PitchWidget()
        self.roll_widget = RollWidget()
        self.arc_widget = ArcWidget()
        self.sample_rate_widget = SampleRateWidget()

        self.rhs = qtw.QVBoxLayout()
        self.rhs.addWidget(self.elevation_widget)
        self.rhs.addWidget(self.pitch_widget)
        self.rhs.addWidget(self.roll_widget)
        self.rhs.addWidget(self.arc_widget)
        self.rhs.addWidget(self.sample_rate_widget)

        self.start_stop_button = qtw.QPushButton('Start')
        self.start_stop_button.clicked.connect(self.start_stop)

        self.layout = qtw.QHBoxLayout()
        self.layout.addWidget(self.graphing_widget)
        self.layout.addLayout(self.rhs)

        self.setLayout(self.layout)


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
            # graphing distance
            distance = [report[s]['distance'] for s in ('lidar0', 'lidar1', 'lidar2', 'lidar3')]
            lidar_engaged = [report[s]['engaged'] for s in ('lidar0', 'lidar1', 'lidar2', 'lidar3')]
            datanew = np.array(distance, dtype=np.int32).reshape(4,1)
            self.databuf = np.concatenate((self.databuf[:,1:], datanew), axis=1)
            self.graphing_widget.update_data(self.databuf)
            # elevation
            self.elevation_widget.update_report(report['elevation'])
            # pitch
            self.pitch_widget.update_report(report['pitch'])
            # roll
            self.roll_widget.update_report(report['roll'])
            # arc
            self.arc_widget.update_report(report['arc'])
            # sample rate
            self.sample_rate_widget.update_value(report['sampleRate'])

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

