#!/usr/bin/python3

import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg
import PyQt5.QtCore as qtc

import pyqtgraph as pg
import serial
import numpy as np
import json
import sys
import time


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


        self.labels= []
        for i in range(4):
            label = pg.LabelItem(f"<b>Channel {i}</b>", size="10pt") 
            label.setParentItem(self.plots[i].getViewBox())
            label.anchor(itemPos=(0.5,0.), parentPos=(0.5,0.01))
            label.html = True
            self.labels.append(label)

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
        #data is of type np.zeros((4,512), dtype=np.float32)
        for i in range(4):
            self.plots[i].clear()
            self.plots[i].plot(data[i,:])
            cur = data[i,-1]
            mean = np.mean(data[i,-50:])
            std = np.std(data[i,-50:])
            self.labels[i].setText(f"<b>Channel {i} = {cur:.1f}</b> (mean={mean:.1f}, std={std:.1f})")

    def eventFilter(self, target, e):
        if (target is self.pgwidget):
            if (e.type() == e.MouseButtonPress):
                if e.button() == qtc.Qt.MouseButton.MiddleButton:
                    self.reset_zoom()
                    return True
        return False


class GaugeWidget(qtw.QFrame):

    def __init__(self, orientation='vertical', polarity='unipolar'):
        super().__init__()
        self.setFrameStyle(qtw.QFrame.Box | qtw.QFrame.Plain)
        self.setLineWidth(2)
        self.orientation = orientation
        self.polarity = polarity
        self.setMinimumWidth(50)
        self.setMinimumHeight(50)
        self.value = None

    def set_value(self, value):
        # float from [-1,1] (or [0,1] for unipolar) or None
        self.value = value
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = qtg.QPainter(self)
        painter.setPen(qtg.QPen(qtc.Qt.gray,  1, qtc.Qt.DashLine))
        self.draw_center_line(painter)
        if self.value is not None:
            painter.setPen(qtg.QPen(qtc.Qt.red,  2, qtc.Qt.SolidLine))
            self.draw_data_line(painter)
        
    def draw_center_line(self, painter):
        if self.polarity == 'bipolar':
            if self.orientation == 'vertical':
                painter.drawLine(0, self.height()//2, self.width(), self.height()//2)
            elif self.orientation == 'horizontal':
                painter.drawLine(self.width()//2, 0, self.width()//2, self.height())

    def draw_data_line(self, painter):
        if self.orientation == 'vertical':
            if self.polarity == 'unipolar':
                pos = int(self.height() * (1. - self.value))
            elif self.polarity == 'bipolar':
                pos = int(self.height()/2 * (1. - self.value))
            painter.drawLine(0, pos, self.width(), pos)
        elif self.orientation == 'horizontal':
            if self.polarity == 'unipolar':
                pos = int(self.width() * (1. - self.value))
            elif self.polarity == 'bipolar':
                pos = int(self.width()/2 * (1. + self.value))
            painter.drawLine(pos, 0, pos, self.height())


class ElevationWidget(qtw.QFrame):

    def __init__(self):
        super().__init__()
        self.setFrameStyle(qtw.QFrame.Box | qtw.QFrame.Plain)
        self.setLineWidth(2)
        self.label = CBLabel('[elevation]')
        self.gauge = GaugeWidget(orientation='vertical', polarity='unipolar')
        self.layout = qtw.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.gauge)
        self.setLayout(self.layout)

    def update_report(self, report_dict):
        value = report_dict['val']
        engaged = report_dict['en']
        if engaged:
            self.label.setText('Elevation:\n%1.3f' % value)
            self.gauge.set_value(value)
        else:
            self.label.setText('[elevation]')
            self.gauge.set_value(None)


class PitchWidget(qtw.QFrame):

    def __init__(self):
        super().__init__()
        self.setFrameStyle(qtw.QFrame.Box | qtw.QFrame.Plain)
        self.setLineWidth(2)
        self.label = CBLabel('[pitch]')
        self.gauge = GaugeWidget(orientation='vertical', polarity='bipolar')
        self.layout = qtw.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.gauge)
        self.setLayout(self.layout)

    def update_report(self, report_dict):
        value = report_dict['val']
        engaged = report_dict['en']
        if engaged:
            self.label.setText('Pitch:\n%1.3f' % value)
            self.gauge.set_value(value)
        else:
            self.label.setText('[pitch]')
            self.gauge.set_value(None)


class RollWidget(qtw.QFrame):

    def __init__(self):
        super().__init__()
        self.setFrameStyle(qtw.QFrame.Box | qtw.QFrame.Plain)
        self.setLineWidth(2)
        self.label = CBLabel('[roll]')
        self.gauge = GaugeWidget(orientation='horizontal', polarity='bipolar')
        self.layout = qtw.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.gauge)
        self.setLayout(self.layout)

    def update_report(self, report_dict):
        value = report_dict['val']
        engaged = report_dict['en']
        if engaged:
            self.label.setText('Roll:\n%1.3f' % value)
            self.gauge.set_value(value)
        else:
            self.label.setText('[roll]')
            self.gauge.set_value(None)


class ArcWidget(qtw.QFrame):

    def __init__(self):
        super().__init__()
        self.setFrameStyle(qtw.QFrame.Box | qtw.QFrame.Plain)
        self.setLineWidth(2)
        self.label = CBLabel('[arc]')
        self.gauge = GaugeWidget(orientation='vertical', polarity='bipolar')
        self.layout = qtw.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.gauge)
        self.setLayout(self.layout)

    def update_report(self, report_dict):
        value = report_dict['val']
        engaged = report_dict['en']
        if engaged:
            self.label.setText('Arc:\n%1.3f' % value)
            self.gauge.set_value(value)
        else:
            self.label.setText('[arc]')
            self.gauge.set_value(None)


class SampleRateWidget(qtw.QFrame):

    def __init__(self):
        super().__init__()
        self.setFrameStyle(qtw.QFrame.Box | qtw.QFrame.Plain)
        self.setLineWidth(2)
        self.label = CBLabel('[sample rate]')
        self.layout = qtw.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        self.tlast = 0
        self.tnow = 0

    def update_report(self, timestamp_us):
        self.tlast = self.tnow
        self.tnow = timestamp_us
        if all(t is not None for t in [self.tlast, self.tnow]):
            self.label.setText('Sample Rate:\n%.1f Hz' % (1e6/(self.tnow - self.tlast)))


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
        self.databuf = np.zeros((4,512), dtype=np.float32)
        self.datanew = np.zeros(4, dtype=np.float32).reshape(4,1)

        self.tnow = 0
        self.tlast = 0

    def start_stop(self):
        if self.running:
            self.refresh_timer.stop()
            self.running = False
            self.start_stop_button.setText('Start')
        else:
            self.refresh_timer.start(15)
            self.running = True
            self.start_stop_button.setText('Stop')

    def refresh(self):
        while self.quadrant.in_waiting:
            report_raw = self.quadrant.readline();
            try:
                report = json.loads(report_raw)
            except json.decoder.JSONDecodeError:
                print('failed to parse')
                continue
            # throttle
            self.tnow = report['ts']
            self.sample_rate_widget.update_report(self.tnow)
            if self.tnow - self.tlast > 30000:
                # graphing distance
                for i,s in enumerate(['l0', 'l1', 'l2', 'l3']):
                    try:
                        self.datanew[i,0] = report[s]['dist']
                    except KeyError:
                        print('keyerror: dist')
                        self.datanew[i,0] = 8190
                self.databuf = np.concatenate((self.databuf[:,1:], self.datanew), axis=1)
                self.graphing_widget.update_data(self.databuf)
                # parameter widgets
                for s,w in zip(('elevation', 'pitch', 'roll', 'arc'),
                                (self.elevation_widget, self.pitch_widget, self.roll_widget,
                                    self.arc_widget)):
                    try:
                        w.update_report(report[s])
                    except KeyError:
                        print('keyerror: report')
                        pass
                self.tlast = self.tnow

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

