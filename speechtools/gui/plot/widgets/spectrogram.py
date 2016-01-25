import numpy as np

from .base import SelectablePlotWidget

from ..visuals import Spectrogram

from ..axis import ScaledTicker

class SpectralPlotWidget(SelectablePlotWidget):
    def __init__(self, *args, **kwargs):
        super(SpectralPlotWidget, self).__init__(*args, **kwargs)
        self._configure_2d()
        self.unfreeze()
        self.spec = Spectrogram()
        self.yaxis.axis.ticker = ScaledTicker(self.yaxis.axis)
        self.freeze()
        self.view.add(self.spec)
        self.selection_time_line.parent = None
        self.play_time_line.parent = None
        self.view.add(self.selection_time_line)
        self.view.add(self.play_time_line)
        self.play_time_line.visible = True

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

    def set_selection_time(self, pos):
        if pos is None:
            self.selection_time_line.visible = False
        else:
            self.selection_time_line.visible = True
            pos = np.array([[pos, -1], [pos, self.spec.ymax() + 1]])
            self.selection_time_line.set_data(pos = pos)

    def set_play_time(self, pos):
        pos = np.array([[pos, -1], [pos, self.spec.ymax() + 1]])
        self.play_time_line.set_data(pos = pos)

    def update_windowing(self, window_length, step):
        self.spec.update_windowing(window_length, step)

