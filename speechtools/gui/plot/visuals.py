
from functools import partial

import numpy as np
import scipy
from scipy.signal import gaussian
import scipy.fftpack as fft

from vispy import scene
from vispy import visuals
from vispy import gloo

from vispy.geometry import Rect

from vispy.visuals.visual import Visual
from vispy.visuals.shaders import Function
from vispy.color import Color, ColorArray, get_colormap
from numpy.lib.stride_tricks import as_strided

#Reproduced from librosa to avoid lots of imports
MAX_MEM_BLOCK = 2**8 * 2**10
def frame(y, frame_length=2048, hop_length=512):
    '''Slice a time series into overlapping frames.
    This implementation uses low-level stride manipulation to avoid
    redundant copies of the time series data.
    Parameters
    ----------
    y : np.ndarray [shape=(n,)]
        Time series to frame. Must be one-dimensional and contiguous
        in memory.
    frame_length : int > 0 [scalar]
        Length of the frame in samples
    hop_length : int > 0 [scalar]
        Number of samples to hop between frames
    Returns
    -------
    y_frames : np.ndarray [shape=(frame_length, N_FRAMES)]
        An array of frames sampled from `y`:
        `y_frames[i, j] == y[j * hop_length + i]`
    Raises
    ------
    ParameterError
        If `y` is not contiguous in memory, framing is invalid.
        See `np.ascontiguous()` for details.
        If `hop_length < 1`, frames cannot advance.
    Examples
    --------
    Extract 2048-sample frames from `y` with a hop of 64 samples per frame
    >>> y, sr = librosa.load(librosa.util.example_audio_file())
    >>> librosa.util.frame(y, frame_length=2048, hop_length=64)
    array([[ -9.216e-06,   7.710e-06, ...,  -2.117e-06,  -4.362e-07],
           [  2.518e-06,  -6.294e-06, ...,  -1.775e-05,  -6.365e-06],
           ...,
           [ -7.429e-04,   5.173e-03, ...,   1.105e-05,  -5.074e-06],
           [  2.169e-03,   4.867e-03, ...,   3.666e-06,  -5.571e-06]], dtype=float32)
    '''

    if hop_length < 1:
        raise ParameterError('Invalid hop_length: {:d}'.format(hop_length))

    if not y.flags['C_CONTIGUOUS']:
        raise ParameterError('Input buffer must be contiguous.')

    valid_audio(y)

    # Compute the number of frames that will fit. The end may get truncated.
    n_frames = 1 + int((len(y) - frame_length) / hop_length)

    if n_frames < 1:
        raise ParameterError('Buffer is too short (n={:d})'
                                    ' for frame_length={:d}'.format(len(y),
                                                                    frame_length))
    # Vertical stride is one sample
    # Horizontal stride is `hop_length` samples
    y_frames = as_strided(y, shape=(frame_length, n_frames),
                          strides=(y.itemsize, hop_length * y.itemsize))
    return y_frames


def valid_audio(y, mono=True):
    '''Validate whether a variable contains valid, mono audio data.
    Parameters
    ----------
    y : np.ndarray
      The input data to validate
    mono : bool
      Whether or not to force monophonic audio
    Returns
    -------
    valid : bool
        True if all tests pass
    Raises
    ------
    ParameterError
        If `y` fails to meet the following criteria:
            - `type(y)` is `np.ndarray`
            - `mono == True` and `y.ndim` is not 1
            - `mono == False` and `y.ndim` is not 1 or 2
            - `np.isfinite(y).all()` is not True
    Examples
    --------
    >>> # Only allow monophonic signals
    >>> y, sr = librosa.load(librosa.util.example_audio_file())
    >>> librosa.util.valid_audio(y)
    True
    >>> # If we want to allow stereo signals
    >>> y, sr = librosa.load(librosa.util.example_audio_file(), mono=False)
    >>> librosa.util.valid_audio(y, mono=False)
    True
    '''

    if not isinstance(y, np.ndarray):
        raise ParameterError('data must be of type numpy.ndarray')

    if mono and y.ndim != 1:
        raise ParameterError('Invalid shape for monophonic audio: '
                                    'ndim={:d}, shape={}'.format(y.ndim,
                                                                 y.shape))
    elif y.ndim > 2:
        raise ParameterError('Invalid shape for audio: '
                                    'ndim={:d}, shape={}'.format(y.ndim,
                                                                 y.shape))

    if not np.isfinite(y).all():
        raise ParameterError('Audio buffer is not finite everywhere')

    return True

def pad_center(data, size, axis=-1, **kwargs):
    '''Wrapper for np.pad to automatically center an array prior to padding.
    This is analogous to `str.center()`
    Examples
    --------
    >>> # Generate a vector
    >>> data = np.ones(5)
    >>> librosa.util.pad_center(data, 10, mode='constant')
    array([ 0.,  0.,  1.,  1.,  1.,  1.,  1.,  0.,  0.,  0.])
    >>> # Pad a matrix along its first dimension
    >>> data = np.ones((3, 5))
    >>> librosa.util.pad_center(data, 7, axis=0)
    array([[ 0.,  0.,  0.,  0.,  0.],
           [ 0.,  0.,  0.,  0.,  0.],
           [ 1.,  1.,  1.,  1.,  1.],
           [ 1.,  1.,  1.,  1.,  1.],
           [ 1.,  1.,  1.,  1.,  1.],
           [ 0.,  0.,  0.,  0.,  0.],
           [ 0.,  0.,  0.,  0.,  0.]])
    >>> # Or its second dimension
    >>> librosa.util.pad_center(data, 7, axis=1)
    array([[ 0.,  1.,  1.,  1.,  1.,  1.,  0.],
           [ 0.,  1.,  1.,  1.,  1.,  1.,  0.],
           [ 0.,  1.,  1.,  1.,  1.,  1.,  0.]])
    Parameters
    ----------
    data : np.ndarray
        Vector to be padded and centered
    size : int >= len(data) [scalar]
        Length to pad `data`
    axis : int
        Axis along which to pad and center the data
    kwargs : additional keyword arguments
      arguments passed to `np.pad()`
    Returns
    -------
    data_padded : np.ndarray
        `data` centered and padded to length `size` along the
        specified axis
    Raises
    ------
    ParameterError
        If `size < data.shape[axis]`
    See Also
    --------
    numpy.pad
    '''

    kwargs.setdefault('mode', 'constant')

    n = data.shape[axis]

    lpad = int((size - n) // 2)

    lengths = [(0, 0)] * data.ndim
    lengths[axis] = (lpad, int(size - n - lpad))

    if lpad < 0:
        raise ParameterError(('Target size ({:d}) must be '
                                     'at least input size ({:d})').format(size,
                                                                          n))

    return np.pad(data, lengths, **kwargs)

def stft(y, n_fft=2048, hop_length=None, win_length=None, window=None,
         center=True, dtype=np.complex64):
    """Short-time Fourier transform (STFT)
    Returns a complex-valued matrix D such that
        `np.abs(D[f, t])` is the magnitude of frequency bin `f`
        at frame `t`
        `np.angle(D[f, t])` is the phase of frequency bin `f`
        at frame `t`
    Parameters
    ----------
    y : np.ndarray [shape=(n,)], real-valued
        the input signal (audio time series)
    n_fft : int > 0 [scalar]
        FFT window size
    hop_length : int > 0 [scalar]
        number audio of frames between STFT columns.
        If unspecified, defaults `win_length / 4`.
    win_length  : int <= n_fft [scalar]
        Each frame of audio is windowed by `window()`.
        The window will be of length `win_length` and then padded
        with zeros to match `n_fft`.
        If unspecified, defaults to ``win_length = n_fft``.
    window : None, function, np.ndarray [shape=(n_fft,)]
        - None (default): use an asymmetric Hann window
        - a window function, such as `scipy.signal.hanning`
        - a vector or array of length `n_fft`
    center      : boolean
        - If `True`, the signal `y` is padded so that frame
          `D[:, t]` is centered at `y[t * hop_length]`.
        - If `False`, then `D[:, t]` begins at `y[t * hop_length]`
    dtype       : numeric type
        Complex numeric type for `D`.  Default is 64-bit complex.
    Returns
    -------
    D : np.ndarray [shape=(1 + n_fft/2, t), dtype=dtype]
        STFT matrix
    Raises
    ------
    ParameterError
        If `window` is supplied as a vector of length `n_fft`.
    See Also
    --------
    istft : Inverse STFT
    ifgram : Instantaneous frequency spectrogram
    Examples
    --------
    >>> y, sr = librosa.load(librosa.util.example_audio_file())
    >>> D = librosa.stft(y)
    >>> D
    array([[  2.576e-03 -0.000e+00j,   4.327e-02 -0.000e+00j, ...,
              3.189e-04 -0.000e+00j,  -5.961e-06 -0.000e+00j],
           [  2.441e-03 +2.884e-19j,   5.145e-02 -5.076e-03j, ...,
             -3.885e-04 -7.253e-05j,   7.334e-05 +3.868e-04j],
          ...,
           [ -7.120e-06 -1.029e-19j,  -1.951e-09 -3.568e-06j, ...,
             -4.912e-07 -1.487e-07j,   4.438e-06 -1.448e-05j],
           [  7.136e-06 -0.000e+00j,   3.561e-06 -0.000e+00j, ...,
             -5.144e-07 -0.000e+00j,  -1.514e-05 -0.000e+00j]], dtype=complex64)
    Use left-aligned frames, instead of centered frames
    >>> D_left = librosa.stft(y, center=False)
    Use a shorter hop length
    >>> D_short = librosa.stft(y, hop_length=64)
    Display a spectrogram
    >>> import matplotlib.pyplot as plt
    >>> librosa.display.specshow(librosa.logamplitude(np.abs(D)**2,
    ...                                               ref_power=np.max),
    ...                          y_axis='log', x_axis='time')
    >>> plt.title('Power spectrogram')
    >>> plt.colorbar(format='%+2.0f dB')
    >>> plt.tight_layout()
    """

    # By default, use the entire frame
    if win_length is None:
        win_length = n_fft

    # Set the default hop, if it's not already specified
    if hop_length is None:
        hop_length = int(win_length / 4)

    if window is None:
        # Default is an asymmetric Hann window
        fft_window = scipy.signal.hann(win_length, sym=False)

    elif callable(window):
        # User supplied a window function
        fft_window = window(win_length)

    else:
        # User supplied a window vector.
        # Make sure it's an array:
        fft_window = np.asarray(window)

        # validate length compatibility
        if fft_window.size != n_fft:
            raise ParameterError('Size mismatch between n_fft and len(window)')

    # Pad the window out to n_fft size
    fft_window = pad_center(fft_window, n_fft)

    # Reshape so that the window can be broadcast
    fft_window = fft_window.reshape((-1, 1))

    # Pad the time series so that frames are centered
    if center:
        valid_audio(y)
        y = np.pad(y, int(n_fft // 2), mode='reflect')

    # Window the time series.
    y_frames = frame(y, frame_length=n_fft, hop_length=hop_length)

    # Pre-allocate the STFT matrix
    stft_matrix = np.empty((int(1 + n_fft // 2), y_frames.shape[1]),
                           dtype=dtype,
                           order='F')

    # how many columns can we fit within MAX_MEM_BLOCK?
    n_columns = int(MAX_MEM_BLOCK / (stft_matrix.shape[0] *
                                          stft_matrix.itemsize))

    for bl_s in range(0, stft_matrix.shape[1], n_columns):
        bl_t = min(bl_s + n_columns, stft_matrix.shape[1])

        # RFFT and Conjugate here to match phase from DPWE code
        stft_matrix[:, bl_s:bl_t] = fft.fft(fft_window *
                                            y_frames[:, bl_s:bl_t],
                                            axis=0)[:stft_matrix.shape[0]].conj()

    return stft_matrix

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
        else:
            color = None
        scene.visuals.Line.set_data(self, pos = data, color = color)

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
        print(dash_index, dash_period)
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
        self.xscale = 1
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
        print(len(self._signal) / self._sr)
        print(len(self._signal))
        #window = partial(gaussian, std = 250/12)
        #import matplotlib.pyplot as plt
        #plt.plot(window(250))
        #plt.show()
        data = stft(self._signal, self._n_fft, step_samp, center = False, win_length = self._win_len)#, window = window)

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
        self.initial_point = None
        self.end_point = None

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

    def maximum_time(self):
        if self.initial_point is None or self.end_point is None:
            return None
        if self.initial_point >= self.end_point:
            return self.initial_point
        return self.end_point

class ScalingText(scene.visuals.Text):
    minpps = 10
    maxpps = 3000
    min_font_size = 1
    max_font_size = 30

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

class PhoneScalingText(ScalingText):
    minpps = 10
    maxpps = 5000
    min_font_size = 1
    max_font_size = 30

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



