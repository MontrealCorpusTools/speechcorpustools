
import time

import numpy as np
from scipy.io import wavfile

from vispy import plot as vp, scene

from .widgets import (SummaryPlotWidget, WaveformPlotWidget,
                    SpectrogramPlotWidget, AnnotationPlotWidget, PitchPlotWidget)

from .helper import get_histogram_mesh_data

class SCTGrid(scene.widgets.Grid):
    def __init__(self, num_types, window_length, time_step, spacing=6, **kwargs):
        self.num_types = num_types
        self.window_length = window_length
        self.time_step = time_step
        super(SCTGrid, self).__init__(spacing, **kwargs)

    def __getitem__(self, plot_type):
        """Return an item or create it if the location is available"""
        if plot_type == 'waveform':
            idxs = (slice(4, 6), 0)
        elif plot_type == 'spectrogram':
            idxs = (slice(2,4), 0)
        elif plot_type == 'annotations':
            idxs = (slice(0,2), 0)
        if not isinstance(idxs, tuple):
            idxs = (idxs,)
        if len(idxs) == 1:
            idxs = idxs + (slice(None),)
        elif len(idxs) != 2:
            raise ValueError('Incorrect index: %s' % (idxs,))
        lims = np.empty((2, 2), int)
        for ii, idx in enumerate(idxs):
            if isinstance(idx, int):
                idx = slice(idx, idx + 1, None)
            if not isinstance(idx, slice):
                raise ValueError('indices must be slices or integers, not %s'
                                 % (type(idx),))
            if idx.step is not None and idx.step != 1:
                raise ValueError('step must be one or None, not %s' % idx.step)
            start = 0 if idx.start is None else idx.start
            end = self.grid_size[ii] if idx.stop is None else idx.stop
            lims[ii] = [start, end]
        layout = self.layout_array
        existing = layout[lims[0, 0]:lims[0, 1], lims[1, 0]:lims[1, 1]] + 1
        if existing.any():
            existing = set(list(existing.ravel()))
            ii = list(existing)[0] - 1
            if len(existing) != 1 or ((layout == ii).sum() !=
                                      np.prod(np.diff(lims))):
                raise ValueError('Cannot add widget (collision)')
            return self._grid_widgets[ii][-1]
        spans = np.diff(lims)[:, 0]

        if plot_type == 'waveform':
            obj = WaveformPlotWidget(self.num_types)
        elif plot_type == 'spectrogram':
            obj = SpectrogramPlotWidget(self.window_length, self.time_step)
        elif plot_type == 'annotations':
            obj = AnnotationPlotWidget(self.num_types)
        item = self.add_widget(obj,
                               row=lims[0, 0], col=lims[1, 0],
                               row_span=spans[0], col_span=spans[1])
        return item

class SCTCentralWidget(scene.widgets.Widget):

    def add_grid(self, *args, **kwargs):
        """
        Create a new Grid and add it as a child widget.
        All arguments are given to Grid().
        """
        grid = SCTGrid(*args, **kwargs)
        return self.add_widget(grid)

class SCTSummaryWidget(vp.Fig):
    def __init__(self, parent = None):
        super(SCTSummaryWidget, self).__init__(size=(800, 400), show=False)
        self._grid._default_class = SummaryPlotWidget
        self.unfreeze()
        self.parent = parent
        self.annotations = None

    def updatePlots(self, data):
        annotations = data[0]
        self.plot(annotations)

    def plot(self, annotations):
        self.annotations = annotations
        self[0:2,0].durations(self.init_data('w')) # word duration histogram
        self[2:4,0].durations(self.init_data('p')) # phone duration histogram

    def init_data(self, dur_type):
        if dur_type == 'w': # get word durations
            words = set([x['label'] for x in self.annotations])
            data = [x['end']-x['begin'] for x in self.annotations]
            self.parent.wordList.addItems(sorted(list(words)))
        else: # get phone durations
            phones = set(np.concatenate([np.array(x['phones']) for x in self.annotations], axis = 0))
            data = np.concatenate([np.array(x['phone_ends'])-np.array(x['phone_begins']) for x in self.annotations], axis = 0)
            self.parent.phoneList.addItems(sorted(list(phones)))
        return data

    def update_data(self, labels, plot_type):
        if self.annotations:
            if plot_type == 'w':
                data = [x['end']-x['begin'] for x in self.annotations if x['label'] in labels]
                data = get_histogram_mesh_data(data)
                self[0:2, 0].hist.set_data(*data)
            elif plot_type == 'p':
                data = np.concatenate([np.array(x['phone_ends'])-np.array(x['phone_begins']) for x in self.annotations], axis = 0)
                phones = np.concatenate([np.array(x['phones']) for x in self.annotations], axis = 0)
                data = [p[1] for p in zip(phones, data) if p[0] in labels]
                data = get_histogram_mesh_data(data)
                self[2:4, 0].hist.set_data(*data)



class SCTAudioWidget(scene.SceneCanvas):
    def __init__(self, num_types, window_length = 0.005, time_step = 0.0001):
        self._plot_widgets = []
        self._grid = None  # initialize before the freeze occurs
        super(SCTAudioWidget, self).__init__(size=(800, 400), bgcolor = 'w', show=False)
        self._grid = self.central_widget.add_grid(num_types, window_length, time_step)
        self._grid._default_class = SummaryPlotWidget
        self['waveform']
        self['spectrogram']
        self['annotations']
        self['waveform'].camera.link(self['annotations'].camera)

    @property
    def central_widget(self):
        """ Returns the default widget that occupies the entire area of the
        canvas.
        """
        if self._central_widget is None:
            self._central_widget = SCTCentralWidget(size=self.size, parent=self.scene)
        return self._central_widget

    @property
    def plot_widgets(self):
        """List of the associated PlotWidget instances"""
        return tuple(self._plot_widgets)

    def __getitem__(self, idxs):
        """Get an axis"""
        pw = self._grid.__getitem__(idxs)
        self._plot_widgets += [pw]
        return pw

    def clear_discourse(self):
        self['spectrogram'].set_signal(None, None)
        self['annotations'].set_annotations(None)
        self['annotations'].set_max_time(None)
        self['waveform'].set_signal(None, None)
        self['waveform'].set_annotations(None)

    def update_audio(self, audio_file):
        begin = time.time()
        sr, data = wavfile.read(audio_file)
        data = data / 32768
        print('read wav time', time.time() - begin)
        max_time = len(data) / sr

        begin = time.time()
        self['annotations'].set_max_time(max_time)
        self['spectrogram'].set_signal(data, sr)
        print('spec time', time.time() - begin)

        begin = time.time()
        self['waveform'].set_signal(data, sr)
        print('wave time', time.time() - begin)


    def update_annotations(self, annotations):

        begin = time.time()
        self['annotations'].set_annotations(annotations)
        self['waveform'].set_annotations(annotations)
        print('annotation time', time.time() - begin)
