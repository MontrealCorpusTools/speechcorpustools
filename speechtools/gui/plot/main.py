
import time

import numpy as np

from vispy import plot as vp, scene

from .widgets import (SummaryPlotWidget,
                    SpectralPlotWidget, AnnotationPlotWidget)

from .helper import get_histogram_mesh_data

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


class SpectralWidget(vp.Fig):
    def __init__(self, window_length = 0.005, time_step = 0.0001):
        self.window_length = window_length
        self.time_step = time_step
        super(SpectralWidget, self).__init__()
        self._grid._default_class = SpectralPlotWidget

    def update_sampling_rate(self, sr):
        self[0:2, 0].set_sampling_rate(sr)

    def update_signal(self, data):
        self[0:2, 0].set_signal(data)

    def update_selection_time(self, pos):
        tr = self.scene.node_transform(self[0:2, 0].spec)
        pos = tr.map([pos, 0])
        pos = pos[0]
        self[0:2, 0].set_selection_time(pos)

    def update_play_time(self, pos):
        tr = self.scene.node_transform(self[0:2, 0].spec)
        pos = tr.map([pos, 0])
        pos = pos[0]
        self[0:2, 0].set_play_time(pos)

class AnnotationWidget(vp.Fig):
    def __init__(self):
        super(AnnotationWidget, self).__init__()
        self._grid._default_class = AnnotationPlotWidget

    def clear(self):
        self.update_signal(None)
        self.update_annotations(None)

    def update_hierarchy(self, hierarchy):
        self[0:2, 0].set_hierarchy(hierarchy)

    def update_signal(self, data):
        self[0:2, 0].set_signal(data)

    def update_annotations(self, annotations):
        self[0:2, 0].set_annotations(annotations)

    def get_play_time(self):
        return self[0:2, 0].play_time_line.pos[0][0]

    def transform_pos_to_time(self, pos):
        tr = self.scene.node_transform(self[0:2, 0].waveform)
        pos = tr.map(pos)
        time = pos[0]
        return time

    def transform_time_to_pos(self, time):
        tr = self.scene.node_transform(self[0:2, 0].waveform)
        pos = tr.imap([time,0])
        pos = pos[0]
        return pos

    def get_key(self, pos):
        tr = self.scene.node_transform(self[0:2, 0].waveform)
        pos = tr.map(pos)
        return self[0:2, 0].pos_to_key(pos)

    def check_selection(self, event):
        if event.source != self:
            return
        pos = event.pos
        tr = self.scene.node_transform(self[0:2, 0].waveform)
        pos = tr.map(pos)
        time = pos[0]
        vert = pos[1]
        key = self[0:2, 0].pos_to_key(pos)
        if key is None:
            return
        p, ind = self[0:2, 0].line_visuals[key].select_line(event)
        self[0:2, 0].line_visuals[key].update_markers(ind)
        if ind == -1:
            return None
        return key, ind

    def update_selected_boundary(self, new_time, key, ind):
        self[0:2, 0].line_visuals[key].update_boundary(ind, new_time)

    def update_selection_time(self, time):
        self[0:2, 0].set_selection_time(time)

    def update_play_time(self, time):
        self[0:2, 0].set_play_time(time)
