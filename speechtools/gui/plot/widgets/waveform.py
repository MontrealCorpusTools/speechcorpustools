import numpy as np

from .base import SelectablePlotWidget

from ..visuals import SCTLinePlot

from ..helper import generate_boundaries

class WaveformPlotWidget(SelectablePlotWidget):
    def __init__(self, num_types, *args, **kwargs):
        super(WaveformPlotWidget, self).__init__(*args, **kwargs)
        self._configure_2d()
        self.unfreeze()
        self.num_types = num_types
        self.waveform = SCTLinePlot(None, connect='strip', color = 'k')
        self.line_visuals = []
        self.freeze()

        for i in range(self.num_types):
            self.line_visuals.append(SCTLinePlot(None, connect='segments',
                        width = 5, color = 'r'))
            self.view.add(self.line_visuals[i])
            self.visuals.append(self.line_visuals[i])

        self.view.add(self.waveform)
        self.visuals.append(self.waveform)

    def set_signal(self, x, sr):
        if x is None:
            self.waveform.set_data(None)
            return
        plotmin = np.min(x)
        plotmax = np.max(x)
        t = np.arange(x.shape[0]) / float(sr)
        data = np.array((t, x)).T
        self.waveform.set_data(data)
        self.view.camera.set_bounds((0, len(x) / sr), (plotmin, plotmax))
        initial_view = 30
        self.view.camera.set_range(x = (0, initial_view))

    def set_annotations(self, annotations):
        if annotations is None:
            for i in range(self.num_types):
                self.line_visuals[i].set_data(None)
            return
        line_data, text_data = generate_boundaries(annotations, text = False)
        for i in range(self.num_types):
            self.line_visuals[i].set_data(line_data[i])
