
from functools import partial

import numpy as np
import scipy
from scipy.signal import gaussian
from librosa.core.spectrum import stft

from vispy import scene
from vispy import visuals
from vispy import gloo

from vispy.geometry import Rect

from vispy.visuals.visual import Visual
from vispy.visuals.shaders import Function
from vispy.color import Color, ColorArray, get_colormap



class SCTLinePlot(scene.visuals.Line):
    def __init__(self, *args, **kwargs):
        scene.visuals.Line.__init__(self, *args, **kwargs)
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

        index = 0
        for p in self.pos:
            if np.linalg.norm(pos_scene - p[0]) < radius_time:
                # point found, return point and its index
                return p, index
            index += 1
        # no point found, return None
        return None, -1

    def update_boundary(self, selected_index, new_time):
        if 0 <= selected_index < len(self.pos):
            p = self.pos
            p[selected_index][0] = new_time
            p[selected_index + 1][0] = new_time

            scene.visuals.Line.set_data(self, pos = p)


    def update_markers(self, selected_index=-1, highlight_color=(1, 1, 0, 1)):
        """ update marker colors, and highlight a marker with a given color """
        c = np.array([self.non_selected_color for x in range(len(self.pos))])
        if 0 <= selected_index < len(self.pos):
            c[selected_index] = highlight_color
            c[selected_index + 1] = highlight_color

        scene.visuals.Line.set_data(self, color = c)

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
        if self._signal is None:
            return 1
        num_steps = 1000
        if len(self._signal) < num_steps:
            num_steps = len(self._signal)
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
        if self._signal is None:
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
        #import matplotlib.pyplot as plt
        #plt.plot(window(250))
        #plt.show()
        data = stft(self._signal, self._n_fft, step_samp, center = True, win_length = self._win_len)#, window = window)

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
        self.max_font_size = 20
        super(ScalingText, self).__init__(*args, **kwargs)

    def set_lowest(self):
        self.maxpps = 5000
        self.max_font_size = 18

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

class SCTAnnotationVisual(visuals.CompoundVisual):
    def __init__(self, data = None, hierarchy = None):
        self._rect = visuals.RectangleVisual(border_color = 'b', border_width = 2)
        self._text = ScalingText()
        self.annotation = None
        self.hierarchy = hierarchy
        visuals.CompoundVisual.__init__(self, [self._rect, self._text])
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



