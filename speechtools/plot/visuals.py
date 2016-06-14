import time
from functools import partial

import numpy as np
import scipy
from scipy.signal import gaussian
from librosa.core.spectrum import stft

from vispy import scene, visuals, gloo

from vispy.geometry import Rect

from vispy.visuals.visual import Visual
from vispy.visuals.shaders import Function
from vispy.visuals import collections
from vispy.color import Color, ColorArray, get_colormap

class WaveformLineVisual(visuals.LineVisual):
    def __init__(self):
        super(WaveformLineVisual, self).__init__(method = 'gl', color = 'k')

    def set_data(self, data):
        if data is not None:
            scene.visuals.Line.set_data(self, pos = data)
        else:
            color = None
            self._bounds = None
            self._changed['pos'] = True
            self._pos = None
            self.update()


class SCTLineVisual(visuals.LineVisual):
    def __init__(self, *args, **kwargs):
        kwargs.update(width = 40)
        visuals.LineVisual.__init__(self, *args, **kwargs)
        self.unfreeze()
        try:
            colormap = get_colormap(self._color)
            color = Function(colormap.glsl_map)
        except KeyError:
            color = Color(self._color).rgba
        self.non_selected_color = color
        self.freeze()

    def set_data(self, data):
        if data is not None:
            color = np.array([self.non_selected_color for x in range(len(data))])
            scene.visuals.Line.set_data(self, pos = data, color = color)
        else:
            color = None
            self._bounds = None
            self._changed['pos'] = True
            self._pos = None
            self.update()

    #Adapted from the vispy line_draw example
    def contains_vert(self, pos):
        try:
            if pos.shape[0] > 1:
                vert = pos[1]
            else:
                vert = pos[0]
        except AttributeError:
            vert = pos
        if self._pos is None:
            return False
        min_vert = self._pos[:, 1].min()
        max_vert = self._pos[:, 1].max()
        if vert <= max_vert and vert >= min_vert:
            return True
        return False

    def select_line(self, event, radius=5):
        if self.pos is None:
            return None, -1
        radius_time = event.source.transform_pos_to_time([radius]) - \
                    event.source.transform_pos_to_time([0])
        pos_scene = event.source.transform_pos_to_time(event.pos)

        index = -1
        for p in self.pos:
            index += 1
            if index % 2 == 0:
                if p[0] != self.pos[index+1][0]:
                    continue
            else:
                if p[0] != self.pos[index-1][0]:
                    continue
            if np.linalg.norm(pos_scene - p[0]) < radius_time:
                # point found, return point and its index
                return p, index
        # no point found, return None
        return None, -1

    def update_boundary(self, selected_index, new_time):
        if 0 <= selected_index < len(self.pos):
            p = self.pos
            p[selected_index][0] = new_time
            p[selected_index + 1][0] = new_time
            if selected_index % 6 == 0:
                p[selected_index+2][0] = new_time
            else:
                p[selected_index - 1][0] = new_time

            scene.visuals.Line.set_data(self, pos = p)


    def update_markers(self, selected_index=-1, highlight_color=(1, 1, 0, 1)):
        """ update marker colors, and highlight a marker with a given color """
        c = np.array([self.non_selected_color for x in range(len(self.pos))])
        if 0 <= selected_index < len(self.pos):
            c[selected_index] = highlight_color
            c[selected_index + 1] = highlight_color

        scene.visuals.Line.set_data(self, color = c)

class LineCollectionVisual(visuals.visual.BaseVisual, collections.agg_segment_collection.AggSegmentCollection):
    pass

class SCTAggLine(visuals.line.line._AggLineVisual):
    def _prepare_draw(self, view):
        bake = False
        if self._parent._changed['pos']:
            if self._parent._pos is None:
                return False
            # todo: does this result in unnecessary copies?
            self._pos = np.ascontiguousarray(
                self._parent._pos.astype(np.float32))
            bake = True

        if self._parent._changed['color']:
            self._color = self._parent._interpret_color()
            bake = True

        if bake:
            if self._parent._connect not in [None, 'strip']:
                segments = SegmentCollection("agg")
                P0 = self._pos[np.arange(0, self._pos.shape[0], 2)]
                P0 = np.hstack((P0, np.zeros((P0.shape[0],1))))
                P1 = self._pos[np.arange(1, self._pos.shape[0], 2)]
                P1 = np.hstack((P1, np.zeros((P1.shape[0],1))))
                c = self._color[np.arange(0, self._color.shape[0], 2)]
                segments.append(P0,
                        P1,
                        color = c)
                segments._update()
                #self.shared_program.bind(segments._vertices_buffer)
                #if self._uniforms_list is not None:
                #    self.shared_program["uniforms"] = segments._uniforms_texture
                #    self.shared_program["uniforms_shape"] = segments._ushape
                #V, I = segments._uniforms_list.data, segments._indices_list.data
            else:
                V, I = self._agg_bake(self._pos, self._color)
                self._vbo.set_data(V)
                self._index_buffer.set_data(I)

                #self._program.prepare()
                self.shared_program.bind(self._vbo)
                uniforms = dict(closed=False, miter_limit=4.0, dash_phase=0.0,
                                linewidth=self._parent._width)
                for n, v in uniforms.items():
                    self.shared_program[n] = v
                for n, v in self._U.items():
                    self.shared_program[n] = v
                self.shared_program['u_dash_atlas'] = self._dash_atlas



class DashedAgg(visuals.line.line._AggLineVisual):
    def __init__(self, parent):
        self._parent = parent
        self._vbo = gloo.VertexBuffer()

        self._pos = None
        self._color = None

        self._da = visuals.line.dash_atlas.DashAtlas()
        dash_index, dash_period = self._da['dashed']
        joins = visuals.line.line.joins
        caps = visuals.line.line.caps
        self._U = dict(dash_index=dash_index, dash_period=dash_period,
                       linejoin=joins['round'],
                       linecaps=(caps['|'], caps['|']),
                       dash_caps=(caps['='], caps['=']),
                       antialias=1.0)
        self._dash_atlas = gloo.Texture2D(self._da._data)

        Visual.__init__(self, vcode=self.VERTEX_SHADER,
                        fcode=self.FRAGMENT_SHADER)
        self._index_buffer = gloo.IndexBuffer()
        self.set_gl_state('translucent', depth_test=False)
        self._draw_mode = 'triangles'

class SelectionLineVisual(visuals.LineVisual):
    def __init__(self):
        visuals.LineVisual.__init__(self, color = 'r', method = 'agg', width = 1)
        self._line_visual = DashedAgg(self)
        self.add_subvisual(self._line_visual)

class PlayLineVisual(visuals.LineVisual):
    def __init__(self):
        visuals.LineVisual.__init__(self, color = 'y', method = 'agg', width = 1)
        self._line_visual = DashedAgg(self)
        self.add_subvisual(self._line_visual)

class SCTSpectrogramVisual(visuals.ImageVisual):
    def __init__(self, window_length = 0.005, step = 0.001):
        self._signal = None
        self.window_length = window_length
        self.step = step
        self._window = 'hann'
        self._color_scale='log'
        self._cmap='cubehelix'
        self._clim='auto'
        self._dynamic_range = 70
        self._sr = None
        self.min_time = 0
        self.max_time = None
        self._win_len = None

        self._n_fft = None

        super(SCTSpectrogramVisual, self).__init__(None,
                clim=self._clim, cmap=self._cmap, interpolation = 'gaussian')

    def update_windowing(self, window_length, step):
        self.window_length = window_length
        self.step = step

    def set_sampling_rate(self, sr):
        self._sr = sr
        if sr is not None:
            self._win_len = int(self.window_length * self._sr)
        else:
            self._win_len = None

    def set_signal(self, data):
        self._signal = data
        if data is None:
            self._n_fft = None
        else:
            self._n_fft = 256
        self._do_spec()

    @property
    def yscale(self):
        if self._n_fft is not None and self._sr is not None:
            return 1 / float(self._n_fft) * float(self._sr)
        return 1

    @property
    def xscale(self):
        if self._signal is None or len(self._signal) == 0 :
            return 1
        num_steps = self._data.shape[1]
        return num_steps /(len(self._signal) /self._sr)

    def ymax(self):
        if self._n_fft is not None:
            return (self._n_fft / 2 + 1)
        return 1

    def ymin(self):
        return 0

    def xmax(self):
        if self._data is not None:
            return self._data.shape[1]
        return 1

    def xmin(self):
        return 0

    def _do_spec(self):
        if self._signal is None or len(self._signal) == 0:
            self.set_data(np.array([[0.5]]))
            return
        #if len(self._signal) / self._sr > 30:
        num_steps = 1000
        if len(self._signal) < num_steps:
            num_steps = len(self._signal)
        step_samp = int(len(self._signal)/ num_steps)

        #if step_samp < 28:
        #    step_samp = 28
        #    step = step_samp / self._sr
        #self._n_fft = 512
        #window = partial(gaussian, std = 250/12)
        if self._window == 'gaussian':
            window = partial(gaussian, std = 0.45*(self._win_len)/2)
        else:
            window = None
        #import matplotlib.pyplot as plt
        #plt.plot(window(250))
        #plt.show()
        data = stft(self._signal, self._n_fft, step_samp, center = True, win_length = self._win_len, window = window)

        data = np.abs(data)
        data = 20 * np.log10(data) if self._color_scale == 'log' else data

        self.set_data(data)

    def set_data(self, image):
        """Set the data
        Parameters
        ----------
        image : array-like
            The image data.
        """
        data = np.asarray(image)
        max_spec = data.max()
        clim = (max_spec - self._dynamic_range, max_spec)
        self.clim = clim
        if self._data is None or self._data.shape != data.shape:
            self._need_vertex_update = True
        self._data = data
        self._need_texture_upload = True
        self._need_interpolation_update = True
        self._need_colortransform_update = True
        self._need_vertex_update = True
        #view._need_method_update = True

SelectionLine = scene.visuals.create_visual_node(SelectionLineVisual)
PlayLine = scene.visuals.create_visual_node(PlayLineVisual)

Spectrogram = scene.visuals.create_visual_node(SCTSpectrogramVisual)
SCTLinePlot = scene.visuals.create_visual_node(SCTLineVisual)
WaveformPlot = scene.visuals.create_visual_node(WaveformLineVisual)

class TierRectangle(scene.Rectangle):
    def __init__(self, tier_index, num_types, num_sub_types):
        self.min_time = None
        self.max_time = None
        self.tier_index = tier_index
        self.num_types = num_types
        self.num_sub_types = num_sub_types

        super(TierRectangle, self).__init__()
        self._color.alpha = 0.1
        if self.tier_index % 2 == 0:
            self.visible = True
        else:
            self.visible = False

    def update_times(self, min_time, max_time):
        if self.tier_index  < self.num_types:
            if self.num_types == 0:
                return
            height = 1 / self.num_types
            vert_min = 1 - height * (self.tier_index+1)
            vert_mid = height/2 + vert_min
        else:
            if self.num_sub_types == 0:
                return
            height = 1 / self.num_sub_types
            vert_min = 0 - height * ((self.tier_index - self.num_types)+1)
            vert_mid = height/2 + vert_min

        self.min_time = min_time
        self.max_time = max_time
        width = self.max_time - self.min_time
        center = self.min_time + width / 2

        self.center = [center, vert_mid]
        self.width = width
        self.height = height

class SelectionRect(scene.Rectangle):
    def __init__(self):
        self.min_time = None
        self.max_time = None

        super(SelectionRect, self).__init__(color = 'y')
        self._color.alpha = 0.5

    def contains(self, time):
        if self.center is None:
            return False
        w = self.width / 2
        begin = self.center[0] - w
        end = self.center[0] + w
        return time >= begin and time <= end

    def set_initial_time(self, time):
        self.initial_point = time

        self.update_selection()

    def set_final_time(self, time):
        self.end_point = time
        self.update_selection()

    def update_selection(self, min_time, max_time):
        self.min_time = min_time
        self.max_time = max_time
        if min_time is None or max_time is None or min_time == max_time:
            self.center = None
            self.width = 1
            self.visible = False
            return
        width = self.max_time - self.min_time
        center = self.min_time + width / 2
        height = 2
        self.center = [center, 0]
        self.width = width
        self.height = height
        self.visible = True

class ScalingText(scene.visuals.Text):

    def __init__(self, *args, **kwargs):
        self.minpps = 10
        self.maxpps = 3000
        self.min_font_size = 1
        self.max_font_size = 18
        super(ScalingText, self).__init__(*args, **kwargs)

    def set_lowest(self):
        self.maxpps = 5000
        self.max_font_size = 16

    def _prepare_draw(self, view):
        if len(self.text) == 0:
            return False
        seconds = view.canvas[0:2,0].view.camera.rect.width
        pixels = view.canvas.physical_size[0]
        pps = pixels / seconds

        if pps < self.minpps:
            font_size = self.min_font_size
        elif pps > self.maxpps:
            font_size = self.max_font_size
        else:
            per = (pps - self.minpps) / (self.maxpps - self.minpps)
            font_size = self.min_font_size + (self.max_font_size - self.min_font_size) * per
        self.font_size = font_size
        super(ScalingText, self)._prepare_draw(view)

    def set_data(self, text, pos):

        self.text = None
        if pos is None:
            pos = [0,0]
        self.pos = pos
        self.text = text

#ScalingText = scene.visuals.create_visual_node(ScalingTextVisual)

class SCTAnnotationVisual(visuals.visual.CompoundVisual):
    def __init__(self, data = None, hierarchy = None):
        self._rect = visuals.RectangleVisual(border_color = 'b', border_width = 2)
        self._text = ScalingText()
        self.annotation = None
        self.hierarchy = hierarchy
        visuals.visual.CompoundVisual.__init__(self, [self._rect, self._text])
        self.set_data(data)

    def set_data(self, data = None, selected = False):
        self.annotation = data
        self._rect.center = None

        if data is None:
            self._text.set_data(None)
            return
        self.update_annotation()

    def update_annotation(self):
        width = self.annotation.end - self.annotation.begin
        center_time = self.annotation.begin + width / 2
        if self.annotation._type == self.hierarchy.lowest:
            vert_center = -0.75
            height = 0.5
        else:
            try:
                height = 1 / (len(self.hierarchy.keys()) - 1)
            except ZeroDivisionError:
                height = 1
            for i, t in enumerate(self.hierarchy.highest_to_lowest):
                if t == self.annotation._type:
                    vert_center = 1 - (height * (i+1)) / 2
                    break

        center = (center_time, vert_center)
        self._rect.width = width
        self._rect.height = height
        self._rect.center = center

SCTAnnotation = scene.visuals.create_visual_node(SCTAnnotationVisual)



