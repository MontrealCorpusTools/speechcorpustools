
from .base import SelectablePlotWidget

from ..visuals import Spectrogram

from ..axis import ScaledTicker

class SpectrogramPlotWidget(SelectablePlotWidget):
    def __init__(self, window_length, step, *args, **kwargs):
        super(SpectrogramPlotWidget, self).__init__(*args, **kwargs)
        self._configure_2d()
        self.unfreeze()
        self.spec = Spectrogram(window_length, step)
        self.freeze()
        self.view.add(self.spec)
        self.yaxis.axis.ticker = ScaledTicker(self.yaxis.axis, scale = self.spec.yscale)
        self.xaxis.axis.ticker = ScaledTicker(self.xaxis.axis, scale = self.spec.xscale)

    def set_signal(self, x, sr):
        self.spec.set_signal(x, sr)
        self.spec.clim = 'auto'
        self.yaxis.axis.ticker.scale = self.spec.yscale
        self.xaxis.axis.ticker.scale = self.spec.xscale

        self.view.camera.set_bounds((self.spec.xmin(), self.spec.xmax()), (self.spec.ymin(), self.spec.ymax()))
        self.view.camera.set_range()

