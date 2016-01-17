
import numpy as np

from vispy import scene
from vispy.visuals import ImageVisual, LinePlotVisual,LineVisual
from vispy.util.fourier import stft
from vispy.geometry import Rect

class SCTLinePlotVisual(LineVisual):
    pass

class SCTSpectrogramVisual(ImageVisual):
    def __init__(self, window_length = 0.005, step = 0.001):
        self._signal = None
        self.window_length = window_length
        self.step = step
        self.xscale = 1
        self._window = 'hann'
        self._color_scale='log'
        self._cmap='cubehelix'
        self._clim='auto'
        self._sr = None
        self.min_time = 0
        self.max_time = None

        self._n_fft = None

        super(SCTSpectrogramVisual, self).__init__(None,
                clim=self._clim, cmap=self._cmap, interpolation = 'gaussian')

    def set_signal(self, x, sr):
        self._signal = x
        self._sr = sr
        if x is None:
            self.max_time = None
            self._n_fft = None
        else:
            self.max_time = len(x) / sr
            self._n_fft = int(self.window_length * sr)
        self._do_spec(0, 30)

    @property
    def yscale(self):
        if self._n_fft is not None and self._sr is not None:
            return 1 / float(self._n_fft) * float(self._sr)
        return 1

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

    def _do_spec(self, min_time, max_time):
        if self._signal is None:
            self.set_data(np.array([[0.5]]))
            return
        if min_time < 0:
            min_time = 0
        if max_time - min_time > 30:
            step = (max_time - min_time) / 1000
        else:
            step = self.step
        step = (max_time - min_time) / 1000

        min_samp = int(min_time * self._sr)
        max_samp = int(max_time * self._sr)
        self.xscale = step
        step_samp = int(step * self._sr)
        #if step_samp < 28:
        #    step_samp = 28
        #    step = step_samp / self._sr
        if self._n_fft < 32:
            self._n_fft = 32
        #self._n_fft = 512
        data = stft(self._signal[min_samp:max_samp], self._n_fft, step_samp, self._sr, self._window)
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



    def _prepare_draw(self, view):
        min_time = view.canvas['annotations'].view.camera.rect.left
        max_time = view.canvas['annotations'].view.camera.rect.right
        self._do_spec(min_time, max_time)
        super(SCTSpectrogramVisual, self)._prepare_draw(view)

Spectrogram = scene.visuals.create_visual_node(SCTSpectrogramVisual)

SCTLinePlot = scene.visuals.create_visual_node(SCTLinePlotVisual)

class SelectionRect(scene.Rectangle):
    def __init__(self):
        self.initial_point = None
        self.end_point = None

        super(SelectionRect, self).__init__(color = 'y')
        self._color.alpha = 0.5

    def set_initial_time(self, time):
        self.initial_point = time

        self.update_selection()

    def set_final_time(self, time):
        self.end_point = time
        self.update_selection()

    def update_selection(self):
        if self.initial_point is None or self.end_point is None:
            self.visible = False
            return
        if self.initial_point < self.end_point:
            width = self.end_point - self.initial_point
            center = width / 2 + self.initial_point
        elif self.initial_point > self.end_point:
            width = self.initial_point - self.end_point
            center = width / 2 + self.end_point
        else:
            self.visible = False
            return
        height = 2
        self.center = [center, 0]
        self.width = width
        self.height = height
        self.visible = True

    def minimum_time(self):
        if self.initial_point is None or self.end_point is None:
            return None
        if self.initial_point <= self.end_point:
            return self.initial_point
        return self.end_point

class ScalingText(scene.Text):
    minpps = 10
    maxpps = 3000
    min_font_size = 1
    max_font_size = 30

    def _prepare_draw(self, view):
        if len(self.text) == 0:
            return False
        seconds = view.canvas['annotations'].view.camera.rect.width
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

        self.pos = pos
        self.text = text

class PhoneScalingText(ScalingText):
    minpps = 10
    maxpps = 5000
    min_font_size = 1
    max_font_size = 30
