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
        self.formantplots = {'F1':scene.visuals.Line(connect = 'strip', color = 'r'),
                            'F2':scene.visuals.Line(connect = 'strip', color = 'r'),
                            'F3':scene.visuals.Line(connect = 'strip', color = 'r')}
        self.yaxis.axis.ticker = ScaledTicker(self.yaxis.axis)
        self.xaxis.axis.ticker = ScaledTicker(self.xaxis.axis)
        self.view.add(self.pitchplot)
        for k,v in self.formantplots.items():
            self.view.add(v)
        self.show_pitch = True
        self.show_spec = True
        self.show_voicing = False
        self.show_formants = True
        self.freeze()
        self.view.add(self.spec)
        self.selection_time_line.parent = None
        self.play_time_line.parent = None
        self.view.add(self.selection_time_line)
        self.view.add(self.play_time_line)
        self.play_time_line.visible = True

    def set_pitch(self, pitch):
        if pitch is None or not len(pitch):
            self.pitchplot._bounds = None
            self.pitchplot._changed['pos'] = True
            self.pitchplot._pos = None
            self.pitchplot.update()
        else:
            factor = 125 / 600
            data = []
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

    def set_formants(self, formants):
        for k,v in self.formantplots.items():
            if formants is None or k not in formants or not formants[k]:
                self.formantplots[k]._bounds = None
                self.formantplots[k]._changed['pos'] = True
                self.formantplots[k]._pos = None
                self.formantplots[k].update()
            else:
                data = []
                for i,(t, f) in enumerate(formants[k]):
                    if f <= 0:
                        continue
                    if i <= 0:
                        continue
                    if formants[k][i-1][1] <= 0:
                        continue
                    t = t * self.spec.xscale
                    f = f / self.spec.yscale
                    data.append([t, f])
                data = np.array(data)
                self.formantplots[k].set_data(pos = data)


    def set_sampling_rate(self, sr):
        self.spec.set_sampling_rate(sr)

    def set_signal(self, data):
        if not self.show_spec:
            self.spec.visible = False
        self.spec.set_signal(data)
        self.view.camera.rect = (0, 0, self.spec.xmax(), self.spec.ymax())
        self.yaxis.axis.ticker.scale = self.spec.yscale
        #self.xaxis.axis.ticker.scale = 1/ self.spec.xscale

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

