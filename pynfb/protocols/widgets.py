import time
from PyQt4 import QtCore
import numpy as np
import pyqtgraph as pg

from pynfb.protocols.psycho.cross_present import PsyExperiment


class ProtocolWidget(pg.PlotWidget):
    def __init__(self, **kwargs):
        super(ProtocolWidget, self).__init__(**kwargs)
        width = 5
        self.setYRange(-width, width)
        self.setXRange(-width, width)
        size = 500
        #self.setMaximumWidth(size)
        #self.setMaximumHeight(size)
        #self.setMnimumWidth(size)
        #self.setMinimumHeight(size)
        self.hideAxis('bottom')
        self.hideAxis('left')
        self.setBackgroundBrush(pg.mkBrush('#252120'))
        self.reward_str = '<font size="4" color="#B48375">Reward: </font><font size="5" color="#91C7A9">{}</font>'
        self.reward = pg.TextItem(html=self.reward_str.format(0))
        self.reward.setPos(-4.7, 4.7)
        self.reward.setTextWidth(300)
        self.addItem(self.reward)
        self.clear_all()

    def clear_all(self):
        for item in self.items():
            self.removeItem(item)
        self.addItem(self.reward)

    def update_reward(self, reward):
        self.reward.setHtml(self.reward_str.format(reward))

    def show_reward(self, flag):
        if flag:
            self.reward.show()
        else:
            self.reward.hide()


class Painter:
    def __init__(self, show_reward=False):
        self.show_reward = show_reward

    def prepare_widget(self, widget):
        widget.show_reward(self.show_reward)


class CircleFeedbackProtocolWidgetPainter(Painter):
    def __init__(self, noise_scaler=2, show_reward=False, radius = 3, circle_border=0, m_threshold=1):
        super(CircleFeedbackProtocolWidgetPainter, self).__init__(show_reward=show_reward)
        self.noise_scaler = noise_scaler
        self.x = np.linspace(-np.pi/2, np.pi/2, 100)
        np.random.seed(42)
        self.noise = np.sin(15*self.x)*0.5-0.5 if not circle_border else np.random.uniform(-0.5, 0.5, 100)-0.5
        self.widget = None
        self.radius = radius
        self.m_threshold = m_threshold

    def prepare_widget(self, widget):
        super(CircleFeedbackProtocolWidgetPainter, self).prepare_widget(widget)
        self.p1 = widget.plot(np.sin(self.x), np.cos(self.x), pen=pg.mkPen(229, 223, 213)).curve
        self.p2 = widget.plot(np.sin(self.x), -np.cos(self.x), pen=pg.mkPen(229, 223, 213)).curve
        fill = pg.FillBetweenItem(self.p1, self.p2, brush=(229, 223, 213, 25))
        self.fill = fill
        widget.addItem(fill)

    def set_red_state(self, flag):
        if flag:
            self.p1.setPen(pg.mkPen(176, 35, 48))
            self.p2.setPen(pg.mkPen(176, 35, 48))
            self.fill.setBrush(176, 35, 48, 25)
        else:
            self.p1.setPen(pg.mkPen(229, 223, 213))
            self.p2.setPen(pg.mkPen(229, 223, 213))
            self.fill.setBrush(229, 223, 213, 25)

    def redraw_state(self, sample, m_sample):
        if m_sample is not None:
            self.set_red_state(m_sample > self.m_threshold)
        if np.ndim(sample)>0:
            sample = np.sum(sample)
        noise_ampl = -np.tanh(sample + self.noise_scaler) + 1
        noise = self.noise*noise_ampl
        self.p1.setData(self.radius * np.sin(self.x)*(1+noise), self.radius * np.cos(self.x)*(1+noise))
        self.p2.setData(self.radius * np.sin(self.x)*(1+noise), -self.radius * np.cos(self.x)*(1+noise))
        pass


class BarFeedbackProtocolWidgetPainter(Painter):#TODO: remove Mock
    def __init__(self, noise_scaler=2, show_reward=False, radius = 3, circle_border=0, m_threshold=1):
        super(BarFeedbackProtocolWidgetPainter, self).__init__(show_reward=show_reward)
        self.x = np.linspace(-1, 1, 100)
        self.widget = None
        self.m_threshold = m_threshold

    def prepare_widget(self, widget):
        super(BarFeedbackProtocolWidgetPainter, self).prepare_widget(widget)
        self.p1 = widget.plot(self.x, np.zeros_like(self.x), pen=pg.mkPen(229, 223, 213)).curve
        self.p2 = widget.plot(self.x, np.zeros_like(self.x)-5, pen=pg.mkPen(229, 223, 213)).curve
        fill = pg.FillBetweenItem(self.p1, self.p2, brush=(229, 223, 213, 25))
        self.fill = fill
        widget.addItem(fill)

    def set_red_state(self, flag):
        if flag:
            self.p1.setPen(pg.mkPen(176, 35, 48))
            self.p2.setPen(pg.mkPen(176, 35, 48))
            self.fill.setBrush(176, 35, 48, 25)
        else:
            self.p1.setPen(pg.mkPen(229, 223, 213))
            self.p2.setPen(pg.mkPen(229, 223, 213))
            self.fill.setBrush(229, 223, 213, 25)

    def redraw_state(self, sample, m_sample):
        if m_sample is not None:
            self.set_red_state(m_sample > self.m_threshold)
        if np.ndim(sample)>0:
            sample = np.sum(sample)
        self.p1.setData(self.x, np.zeros_like(self.x)+max(min(sample, 5), -5))
        self.p2.setData(self.x, np.zeros_like(self.x)-5)
        pass

class BarFeedbackProtocolWidgetPainter(Painter):
    def __init__(self, noise_scaler=2, show_reward=False, radius = 3, circle_border=0, m_threshold=1):
        super(BarFeedbackProtocolWidgetPainter, self).__init__(show_reward=show_reward)

        self.bar_width = 0.5
        self.x = np.linspace(-self.bar_width, self.bar_width, 100)
        self.widget = None
        self.counter = 0
        self.reward_counter = 0
        self.m_threshold = m_threshold
        self.timer = time.time()


    def update_reward(self):
        self.points.setHtml(self.points_str.format(self.reward_counter))

    def prepare_widget(self, widget):
        super(BarFeedbackProtocolWidgetPainter, self).prepare_widget(widget)
        self.p1 = widget.plot(self.x, np.zeros_like(self.x)-4, pen=pg.mkPen(229, 223, 213)).curve
        self.p2 = widget.plot(self.x, np.zeros_like(self.x)-5, pen=pg.mkPen(229, 223, 213)).curve
        widget.plot([-self.bar_width, -self.bar_width], [-5, 5], pen=pg.mkPen(229, 223, 213))
        widget.plot([self.bar_width, self.bar_width], [-5, 5], pen=pg.mkPen(229, 223, 213))
        for k in range(11):
            widget.plot(self.x, np.zeros_like(self.x) - 5 + k, pen=pg.mkPen(229, 223, 213))
        self.fill = pg.FillBetweenItem(self.p1, self.p2, brush=(229, 223, 213, 255))
        #self.fill2 = pg.FillBetweenItem(self.p3, self.p2, brush=(229, 223, 213))
        widget.addItem(self.fill)

        self.points_str = '<font size="5" color="#91C7A9">{}$</font>'
        self.points = pg.TextItem(html=self.points_str.format(0))
        self.points.setPos(-4.7, 4.7)
        self.points.setScale(4)
        widget.addItem(self.points)

        # fix cross
        self.cross = pg.TextItem(html='<font size="5" color="#FFFFFF">+</font>', anchor=(0.5, 0.5))
        self.cross.setScale(2)
        self.cross.setPos(0, self.counter + 1.5 - 5)
        widget.addItem(self.cross)

        r1 = widget.plot([5, 6], [6, 6], pen=pg.mkPen(0, 0, 0)).curve
        r2 = widget.plot([5, 6], [5, 5], pen=pg.mkPen(0, 0, 0)).curve
        self.rect = pg.FillBetweenItem(r1, r2, brush=(255, 255, 255))
        widget.addItem(self.rect)

    def set_red_state(self, flag):
        pass

    def redraw_state(self, sample, m_sample):
        stimulus_presented = 0
        if m_sample is not None:
            self.set_red_state(m_sample > self.m_threshold)
        if np.ndim(sample) > 0:
            sample = np.sum(sample)
        if self.give_reward(sample) and time.time() - self.timer > 1:
            self.timer = time.time()
            self.counter = (self.counter + 1) % 10
            stimulus_presented = 1
            if self.counter == 0:
                self.reward_counter += 1
                self.update_reward()
                stimulus_presented = 2
            if self.counter == 9:
                QtCore.QTimer.singleShot(500, lambda: self.p1.setData(self.x, np.zeros_like(self.x)-5))
            self.p1.setData(self.x, np.zeros_like(self.x)+ self.counter + 1 - 5)
            self.rect.setBrush(255, 255, 255)
            QtCore.QTimer.singleShot(50, lambda: self.rect.setBrush(255, 255, 255, 0))
            self.cross.setPos(0, (self.counter + 1)%10 - 5 +0.5)
        return stimulus_presented


    @staticmethod
    def give_reward(sample):
        return sample > 2

class PsyProtocolWidgetPainter(Painter):
    def __init__(self, detection=False):
        print('DETECTION', detection)
        self.detection = detection
        super(PsyProtocolWidgetPainter, self).__init__()
        print('inited')
        self.t_start_trial = 0

    def prepare_widget(self, widget):
        self.exp = PsyExperiment(widget, detection_task=self.detection)
        #self.exp.run()
        print('prepared')

    def redraw_state(self, sample, m_sample):
        stimulus_presented = self.exp.run_trial(sample)
        if stimulus_presented:
            print('STIMULUS PRESENTED')
        return stimulus_presented

    def close(self):
        pass


class BaselineProtocolWidgetPainter(Painter):
    def __init__(self, text='Relax', show_reward=False):
        super(BaselineProtocolWidgetPainter, self).__init__(show_reward=show_reward)
        self.text = text

    def prepare_widget(self, widget):
        super(BaselineProtocolWidgetPainter, self).prepare_widget(widget)
        self.text_item = pg.TextItem(html='<center><font size="7" color="#e5dfc5">{}</font></center>'.format(self.text),
                                anchor=(0.5, 0.5))
        self.text_item.setTextWidth(500)
        widget.addItem(self.text_item)
        self.plotItem = widget.plotItem

    def redraw_state(self, sample, m_sample):
        pass

    def set_message(self, text):
        self.text = text
        self.text_item.setHtml('<center><font size="7" color="#e5dfc5">{}</font></center>'.format(self.text))

class ThresholdBlinkFeedbackProtocolWidgetPainter(Painter):
    def __init__(self, threshold=2000, time_ms=50, show_reward=False):
        super(ThresholdBlinkFeedbackProtocolWidgetPainter, self).__init__(show_reward=show_reward)
        self.threshold = threshold
        self.time_ms = time_ms
        self.blink_start_time = -1
        self.widget = None
        self.x = np.linspace(-10, 10, 2)
        self.previous_sample = -np.inf

    def prepare_widget(self, widget):
        super(ThresholdBlinkFeedbackProtocolWidgetPainter, self).prepare_widget(widget)
        self.p1 = widget.plot([-10, 10], [10, 10], pen=pg.mkPen(77, 144, 254)).curve
        self.p2 = widget.plot([-10, 10], [-10, -10], pen=pg.mkPen(77, 144, 254)).curve
        self.fill = pg.FillBetweenItem(self.p1, self.p2, brush=(255, 255, 255, 25))
        widget.addItem(self.fill)

    def redraw_state(self, samples, m_sample):
        samples = np.abs(samples)
        if np.ndim(samples)==0:
            samples = samples.reshape((1, ))

        previous_sample = self.previous_sample
        do_blink = False
        for sample in samples:
            if (sample >= self.threshold >= previous_sample) and (self.blink_start_time < 0):
                do_blink = True
            previous_sample = sample

        if do_blink:
            self.blink_start_time = time.time()

        if ((time.time() - self.blink_start_time < self.time_ms * 0.001) and (self.blink_start_time > 0)):
            self.fill.setBrush((255, 255, 255, 255))
        else:
            self.blink_start_time = -1
            self.fill.setBrush((255, 255, 255, 10))


        self.previous_sample = previous_sample
        pass


class VideoProtocolWidgetPainter(Painter):
    def __init__(self, video_file_path):
        super(VideoProtocolWidgetPainter, self).__init__()
        self.widget = None
        self.video = None
        self.timer = time.time()
        self.timer_period = 1 / 30
        self.frame_counter = 0
        self.n_frames = None
        self.err_msg = "Could't open video file. "
        import os.path
        if os.path.isfile(video_file_path):
            try:
                import imageio as imageio
                self.video = imageio.get_reader(video_file_path,  'ffmpeg')
                self.n_frames = self.video.get_length() - 1
            except ImportError as e:
                print(e.msg)
                self.err_msg += e.msg
        else:
            self.err_msg = "No file {}".format(video_file_path)


    def prepare_widget(self, widget):
        super(VideoProtocolWidgetPainter, self).prepare_widget(widget)
        if self.video is not None:
            self.img = pg.ImageItem()
            self.img.setScale(10 / self.video.get_data(0).shape[1])
            self.img.rotate(-90)
            self.img.setX(-5)
            self.img.setY(5/self.video.get_data(0).shape[1]*self.video.get_data(0).shape[0])
            widget.addItem(self.img)

        else:
            text_item = pg.TextItem(html='<center><font size="6" color="#a92f41">{}'
                                         '</font></center>'.format(self.err_msg),
                                    anchor=(0.5, 0.5))
            text_item.setTextWidth(500)
            widget.addItem(text_item)

    def redraw_state(self, sample, m_sample):
        if self.video is not None:
            timer = time.time()
            if timer - self.timer > self.timer_period:
                self.timer = timer
                self.frame_counter = (self.frame_counter + 1) % self.n_frames
                self.img.setImage(self.video.get_data(self.frame_counter))
            pass


if __name__ == '__main__':
    from PyQt4 import QtGui
    from PyQt4 import QtCore
    a = QtGui.QApplication([])
    w = ProtocolWidget()
    w.show()
    b = BarFeedbackProtocolWidgetPainter()
    b.prepare_widget(w)
    timer = QtCore.QTimer()
    timer.start(1000/500)
    timer.timeout.connect(lambda: b.redraw_state(np.random.normal(), np.random.normal(scale=0.1)))
    a.exec_()
    #for k in range(10000):
    #    sleep(1/30)
    #    b.redraw_state(np.random.normal(size=1))


