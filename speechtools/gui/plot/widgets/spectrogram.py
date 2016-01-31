import numpy as np

from .base import SelectablePlotWidget

from ..visuals import Spectrogram, SCTLinePlot, scene

from ..axis import ScaledTicker

class SpectralPlotWidget(SelectablePlotWidget):
    def __init__(self, *args, **kwargs):
        super(SpectralPlotWidget, self).__init__(*args, **kwargs)
        self._configure_2d()
        self.unfreeze()
        self.spec = Spectrogram()
        self.pitchplot = scene.visuals.Line(connect = 'segments', color = 'b')
        self.yaxis.axis.ticker = ScaledTicker(self.yaxis.axis)
        self.xaxis.axis.ticker = ScaledTicker(self.xaxis.axis)
        self.freeze()
        self.view.add(self.spec)
        self.selection_time_line.parent = None
        self.play_time_line.parent = None
        self.pitchplot.parent = None
        self.view.add(self.selection_time_line)
        self.view.add(self.play_time_line)
        self.view.add(self.pitchplot)
        self.play_time_line.visible = True
        self.pitchplot.visible = True

    def set_pitch(self, pitch):
        if not pitch:
            self.pitchplot.visible = False
        else:
            self.pitchplot.visible = True
            print(self.spec.ymax())
            factor = 250 / 600
            data = []
            print('hello')
            print(pitch[0][0], pitch[-1][0])
            print(pitch[-1][0] - pitch[0][0])
            print(len(self.spec._signal) /self.spec._sr)
            for i,(t, p) in enumerate(pitch):
                if p <= 0:
                    continue
                if i <= 0:
                    continue
                if pitch[i-1][1] <= 0:
                    continue
                p = p * factor
                t = t * self.spec.xscale
                prev_p = pitch[i-1]
                prev_p = [prev_p[0] * self.spec.xscale, prev_p[1] * factor]
                data.append(prev_p)
                data.append([t, p])
            data = np.array(data)
            self.pitchplot.set_data(pos = data)
            print(data.shape)

    def set_sampling_rate(self, sr):
        self.spec.set_sampling_rate(sr)

    def set_signal(self, data):
        self.spec.set_signal(data)
        self.spec.clim = 'auto'
        #self.view.camera.set_range()
        #max_time = data[:,0].max()
        #min_time = data[:,0].min()
        #min_ind = min_time / self.spec.step
        #max_ind = max_time / self.spec.step
        self.view.camera.rect = (0, 0, self.spec.xmax(), self.spec.ymax())
        self.yaxis.axis.ticker.scale = self.spec.yscale
        self.xaxis.axis.ticker.scale = 1/ self.spec.xscale

    def set_selection_time(self, pos):
        if pos is None:
            self.selection_time_line.visible = False
        else:
            self.selection_time_line.visible = True
            pos = np.array([[pos, -1], [pos, self.spec.ymax() + 1]])
            self.selection_time_line.set_data(pos = pos)

    def set_play_time(self, pos):
        if pos is None:
            self.play_time_line.visible = False
        else:
            self.play_time_line.visible = True
            pos = np.array([[pos, -1], [pos, self.spec.ymax() + 1]])
            self.play_time_line.set_data(pos = pos)

    def update_windowing(self, window_length, step):
        self.spec.update_windowing(window_length, step)

