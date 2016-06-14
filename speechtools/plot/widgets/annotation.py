
import numpy as np
import copy
import time

from vispy import scene

from vispy.visuals.text.text import FontManager

from .base import SelectablePlotWidget, PlotWidget

from ..visuals import SCTLinePlot, ScalingText, SCTAnnotation, SelectionLine, TierRectangle, WaveformPlot

from ..helper import generate_boundaries

class AnnotationPlotWidget(SelectablePlotWidget):

    def __init__(self, *args, **kwargs):
        super(AnnotationPlotWidget, self).__init__(*args, **kwargs)
        self.unfreeze()
        self.hierarchy = None
        self.num_types = 0
        self.annotation_visuals = {}
        self.annotations = None
        self.min_time = None
        self.max_time = None
        self.line_visuals = {}
        self.box_visuals = {}
        self.font_manager = FontManager()
        self.breakline = SCTLinePlot(None, width = 1, color = 'k')
        self.waveform = WaveformPlot()
        self.freeze()
        self._configure_2d()

    def _configure_2d(self, fg_color = None):
        super(AnnotationPlotWidget, self)._configure_2d(fg_color)
        self.view.add(self.breakline)
        self.view.add(self.waveform)
        self.visuals.append(self.breakline)
        self.visuals.append(self.waveform)
        self.play_time_line.visible = True

    def set_time_bounds(self, min_time, max_time):
        self.min_time = min_time
        self.max_time = max_time
        self.view.camera.rect = (min_time, -1, max_time - min_time, 2)
        self.set_play_time(min_time)
        for v in self.box_visuals.values():
            v.update_times(min_time, max_time)

    def set_selection(self, min_time, max_time):
        try:
            self.selection_rect.update_selection(min_time, max_time)
        except AttributeError:
            pass

    def pos_to_key(self, pos):
        for k, v in self.line_visuals.items():
            if v.contains_vert(pos):
                return k
        return None

    def set_hierarchy(self, hierarchy):
        self.hierarchy = hierarchy
        if self.hierarchy is None:
            return
        try:
            for k,v in self.annotation_visuals.items():
                v.parent = None
            for k,v in self.line_visuals.items():
                v.parent = None
            self.num_types = len(self.hierarchy.keys())
            keys = []
            for k, v in sorted(self.hierarchy.subannotations.items()):
                for s in v:
                    keys.append((k,s))
            self.annotation_visuals = {}
            self.line_visuals = {}
            cycle = ['b', 'r']
            for i, k in enumerate(self.hierarchy.highest_to_lowest):
                c = cycle[i % len(cycle)]
                self.annotation_visuals[k] = ScalingText(face = 'OpenSans', font_manager = self.font_manager) #FIXME Need to get a better font that covers more scripts, i.e. Thai (**Only applies to windows)
                if k == self.hierarchy.lowest:
                    self.annotation_visuals[k].set_lowest()
                self.line_visuals[k] = SCTLinePlot(connect = 'segments', color = c)
                #self.box_visuals[k] = TierRectangle(i, self.num_types, len(keys))
                #self.view.add(self.box_visuals[k])
                self.view.add(self.annotation_visuals[k])
                self.view.add(self.line_visuals[k])
            ind = len(self.hierarchy.highest_to_lowest)
            for k in sorted(keys):
                c = cycle[ind % len(cycle)]
                self.annotation_visuals[k] = ScalingText(face = 'OpenSans', font_manager = self.font_manager)
                self.annotation_visuals[k].set_lowest()
                self.line_visuals[k] = SCTLinePlot(connect = 'segments', color = c)
                #self.box_visuals[k] = TierRectangle(ind, self.num_types, len(keys))
                #self.view.add(self.box_visuals[k])
                self.view.add(self.annotation_visuals[k])
                self.view.add(self.line_visuals[k])
                ind += 1
        except AttributeError:
            pass
    def set_annotations(self, data):
        #Assume that data is the highest level of the hierarchy
        self.annotations = data
        if data is None:
            if self.hierarchy is not None:
                for k in self.hierarchy.keys():
                    self.line_visuals[k].visible = False
                    self.line_visuals[k].set_data(None)
                    self.annotation_visuals[k].visible = False
                    self.annotation_visuals[k].set_data(None, None)
                for k,v in self.hierarchy.subannotations.items():
                    for s in v:
                        self.line_visuals[k, s].visible = False
                        self.line_visuals[k, s].set_data(None)
                        self.annotation_visuals[k, s].visible = False
                        self.annotation_visuals[k, s].set_data(None, None)
            return
        if self.hierarchy is not None:
            line_data, text_data = generate_boundaries(data, self.hierarchy, self.min_time, self.max_time)
            for k in self.hierarchy.keys():
                if text_data[k][0] and (self.max_time - self.min_time < 10 or k != self.hierarchy.lowest):
                        self.line_visuals[k].set_data(line_data[k])
                        self.line_visuals[k].visible = True
                        self.annotation_visuals[k].set_data(text_data[k][0], pos = text_data[k][1])
                        self.annotation_visuals[k].visible = True
                else:
                    self.line_visuals[k].set_data(None)
                    self.annotation_visuals[k].set_data(None, None)
            for k, v in self.hierarchy.subannotations.items():
                for s in v:
                    if text_data[k, s][0] and self.max_time - self.min_time < 10:
                        self.line_visuals[k, s].set_data(line_data[k, s])
                        self.line_visuals[k, s].visible = True
                        self.annotation_visuals[k, s].set_data(text_data[k, s][0], pos = text_data[k, s][1])
                        self.annotation_visuals[k, s].visible = True
                    else:
                        self.line_visuals[k, s].visible = False
                        self.line_visuals[k, s].set_data(None)
                        self.annotation_visuals[k, s].visible = False
                        self.annotation_visuals[k, s].set_data(None, None)

    def rank_key_by_relevance(self, key):
        ranking = []
        if isinstance(key, tuple):
            for k, v in self.hierarchy.subannotations.items():
                for s in v:
                    if (k,s) == key:
                        continue
                    ranking.append((k,s))
        for k in reversed(self.hierarchy.highest_to_lowest):
            if k == key:
                continue
            ranking.append(k)
        return ranking

    def set_signal(self, data):
        if data is None or data.shape[0] == 0:
            self.waveform.visible = False
            self.waveform.set_data(None)
            return
        max_sig = np.abs(data[:,1]).max()
        if max_sig < 0.5:
            ratio = 0.5 / max_sig
            data[:,1] *=  ratio

        self.waveform.set_data(data)
        self.waveform.visible = True

    def set_play_time(self, time):
        if time is None:
            self.play_time_line.visible = False
        else:
            self.play_time_line.visible = True
            pos = np.array([[time, -1.5], [time, 1.5]])
            self.play_time_line.set_data(pos = pos)
