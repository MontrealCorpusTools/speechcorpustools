
import numpy as np

from vispy import plot as vp
from scipy.io import wavfile

from vispy.scene.cameras.panzoom import PanZoomCamera
from vispy.geometry import Rect
from vispy.plot.plotwidget import PlotWidget
from vispy.visuals.axis import Ticker, _get_ticks_talbot
from vispy.util.fourier import stft
from vispy import scene
from vispy.visuals import ImageVisual, LinePlotVisual,LineVisual

## Helper functions

def get_histogram_mesh_data(data, bins=100, color='k', orientation='h'):
    # shamlessly stolen from vispy.visuals.histogram.__init__()
    data = np.asarray(data)
    if data.ndim != 1:
        raise ValueError('Only 1D data currently supported')
    X, Y = (0, 1) if orientation == 'h' else (1, 0)

    # do the histogramming
    data, bin_edges = np.histogram(data, bins)
    # construct our vertices
    rr = np.zeros((3 * len(bin_edges) - 2, 3), np.float32)
    rr[:, X] = np.repeat(bin_edges, 3)[1:-1]
    rr[1::3, Y] = data
    rr[2::3, Y] = data
    bin_edges.astype(np.float32)
    # and now our tris
    tris = np.zeros((2 * len(bin_edges) - 2, 3), np.uint32)
    offsets = 3 * np.arange(len(bin_edges) - 1,
                            dtype=np.uint32)[:, np.newaxis]
    tri_1 = np.array([0, 2, 1])
    tri_2 = np.array([2, 0, 3])
    tris[::2] = tri_1 + offsets
    tris[1::2] = tri_2 + offsets
    return (rr, tris)

def generate_boundaries(annotations, text = True):
    plotdata = []
    annodata = []
    subannodata = []
    subplotdata = []
    posdata = []
    subposdata = []
    for a in annotations:
        midpoint = ((a['end']-a['begin']) /2) + a['begin']
        annodata.append(a['label'])
        posdata.append((midpoint, 0.5))

        plotdata.append([a['begin'],0])
        plotdata.append([a['begin'],1])
        plotdata.append([a['end'],0])
        plotdata.append([a['end'],1])
        for i, p in enumerate(a.phones):
            p_begin = a.phone_begins[i]
            p_end = a.phone_ends[i]
            midpoint = ((p_end - p_begin) /2) + p_begin
            subannodata.append(p)
            subposdata.append((midpoint, -0.5))

            subplotdata.append([p_begin,-1])
            subplotdata.append([p_begin,0])
            subplotdata.append([p_end,-1])
            subplotdata.append([p_end,0])

    line_outputs = []
    text_outputs = []
    line_outputs.append( np.array(plotdata))
    line_outputs.append(np.array(subplotdata))
    if text:
        text_outputs.append((annodata, np.array(posdata)))
        text_outputs.append((subannodata, np.array(subposdata)))
    return line_outputs, text_outputs

class SCTLinePlotVisual(LineVisual):
    pass

SCTLinePlot = scene.visuals.create_visual_node(SCTLinePlotVisual)

class SCTAudioCamera(PanZoomCamera):
    def __init__(self, rect=(0, 0, 1, 1), aspect=None, zoom = 'both', pan = 'both', **kwargs):
        super(SCTAudioCamera, self).__init__(rect, aspect, **kwargs)

        self._zoom_axis = zoom
        self._pan_axis = pan
        self._xbounds = None
        self._ybounds = None

        self._linked_panzoom = []
        self._panned = False
        self._zoomed = False

    def set_bounds(self, xbounds = None, ybounds = None):
        self._xbounds = xbounds
        self._ybounds = ybounds

    def set_range(self, x = None, y = None):
        if x is None:
            x = self._xbounds
        elif self._xbounds:
            if x[0] < self._xbounds[0]:
                x = (self._xbounds[0], x[1])
            if x[1] > self._xbounds[1]:
                x = (x[0], self._xbounds[1])
        if y is None:
            y = self._ybounds
        elif self._ybounds:
            if y[0] < self._ybounds[0]:
                y = (self._ybounds[0], y[1])
            if y[1] > self._ybounds[1]:
                y = (y[0], self._ybounds[1])
        super(SCTAudioCamera, self).set_range(x=x, y=y, margin =0)

    def link(self, camera):
        if camera not in self._linked_panzoom:
            self._linked_panzoom.append(camera)
        if self not in camera._linked_panzoom:
            camera._linked_panzoom.append(self)

    def zoom(self, factor, center=None):
        """ Zoom in (or out) at the given center
        Parameters
        ----------
        factor : float or tuple
            Fraction by which the scene should be zoomed (e.g. a factor of 2
            causes the scene to appear twice as large).
        center : tuple of 2-4 elements
            The center of the view. If not given or None, use the
            current center.
        """
        if self._zoomed:
            return
        assert len(center) in (2, 3, 4)
        # Get scale factor, take scale ratio into account
        if np.isscalar(factor):
            scale = [factor, factor]
        else:
            if len(factor) != 2:
                raise TypeError("factor must be scalar or length-2 sequence.")
            scale = list(factor)
        if self.aspect is not None:
            scale[0] = scale[1]

        # Init some variables
        center = center if (center is not None) else self.center
        # Make a new object (copy), so that allocation will
        # trigger view_changed:
        rect = Rect(self.rect)
        if rect.right - rect.left < 0.1 and scale[0] < 1:
            return
        # Get space from given center to edges
        left_space = center[0] - rect.left
        right_space = rect.right - center[0]
        bottom_space = center[1] - rect.bottom
        top_space = rect.top - center[1]
        # Scale these spaces
        if self._zoom_axis == 'both' or self._zoom_axis == 'x':
            rect.left = center[0] - left_space * scale[0]
            rect.right = center[0] + right_space * scale[0]
        if self._zoom_axis == 'both' or self._zoom_axis == 'y':
            rect.bottom = center[1] - bottom_space * scale[1]
            rect.top = center[1] + top_space * scale[1]
        if self._ybounds is not None:
            if rect.bottom < self._ybounds[0]:
                rect.bottom = self._ybounds[0]
            if rect.top > self._ybounds[1]:
                rect.top = self._ybounds[1]
        if self._xbounds is not None:
            if rect.left < self._xbounds[0]:
                rect.left = self._xbounds[0]
            if rect.right > self._xbounds[1]:
                rect.right = self._xbounds[1]

        self.rect = rect
        self._zoomed = True
        for c in self._linked_panzoom:
            if c._zoomed:
                continue
            new_center = []
            new_center.append(rescale(center[0], self._xbounds[1], c._xbounds[1]))
            new_center.append(rescale(center[1], self._ybounds[1], c._ybounds[1]))
            new_center.extend([0,1])
            c.zoom(factor, np.array(new_center))
        self._zoomed = False

    def pan(self, *pan):
        """Pan the view.
        Parameters
        ----------
        *pan : length-2 sequence
            The distance to pan the view, in the coordinate system of the
            scene.
        """
        if self._panned:
            return
        if len(pan) == 1:
            pan = pan[0]
        pan = list(pan)

        if self._pan_axis == 'x':
            pan[1] = 0
        elif self._pan_axis == 'y':
            pan[0] = 0

        if self._ybounds is not None:
            dist_to_bottom = self._ybounds[0] - self.rect.bottom
            if pan[1] < dist_to_bottom:
                pan[1] = dist_to_bottom
            dist_to_top = self._ybounds[1] - self.rect.top
            if pan[1] > dist_to_top:
                pan[1] = dist_to_top
        if self._xbounds is not None:
            dist_to_left = self._xbounds[0] - self.rect.left
            if pan[0] < dist_to_left:
                pan[0] = dist_to_left
            dist_to_right = self._xbounds[1] - self.rect.right
            if pan[0] > dist_to_right:
                pan[0] = dist_to_right
        self.rect = self.rect + pan
        self._panned = True
        for c in self._linked_panzoom:
            newpan = []
            newpan.append(rescale(pan[0], self._xbounds[1], c._xbounds[1]))
            newpan.append(rescale(pan[1], self._ybounds[1], c._ybounds[1]))
            c.pan(newpan)
        self._panned = False

def rescale(value, oldmax, newmax):
    return value * newmax/oldmax

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

class SummaryPlotWidget(PlotWidget):
    def _configure_2d(self, fg_color=None):
        if self._configured:
            return
        if fg_color is None:
            fg = self._fg
        else:
            fg = fg_color
        self.yaxis = scene.AxisWidget(orientation='left', text_color=fg,
                                      axis_color=fg, tick_color=fg)
        self.yaxis.stretch = (0.1, 1)
        self.grid.add_widget(self.yaxis, row=2, col=2)

        self.ylabel = scene.Label("", rotation=-90)
        self.ylabel.stretch = (0.05, 1)
        self.grid.add_widget(self.ylabel, row=2, col=1)

        self.xaxis = scene.AxisWidget(orientation='bottom', text_color=fg,
                                      axis_color=fg, tick_color=fg)
        self.xaxis.stretch = (1, 0.1)
        self.grid.add_widget(self.xaxis, row=3, col=3)

        self.xlabel = scene.Label("")
        self.xlabel.stretch = (1, 0.05)
        self.grid.add_widget(self.xlabel, row=4, col=3)

        self.view.camera = SCTAudioCamera(zoom = 'x', pan = 'x')
        self.camera = self.view.camera

        self.xaxis.link_view(self.view)
        self.yaxis.link_view(self.view)
        self._configured = True

    def durations(self, data, bins = 100):
        # histogram of word or phone durations
        self._configure_2d()
        # init histogram and make visible
        self.unfreeze()
        self.hist = scene.Histogram(data, bins, color = 'k', orientation = 'h')
        self.view.add(self.hist)
        self.visuals.append(self.hist)
        # set histogram bounds and range
        self.view.camera.set_bounds((0, max(data+[1])))
        self.view.camera.set_range(x = (0, 30))

class SelectablePlotWidget(PlotWidget):
    def __init__(self, *args, **kwargs):
        super(SelectablePlotWidget, self).__init__(*args, **kwargs)

        self.unfreeze()
        self.playLine = SCTLinePlot(np.array([[0,-1], [0,1]]), width = 5, color = 'r')
        self.selectRect = SelectionRect()
        self.freeze()

        self.view.add(self.playLine)
        self.visuals.append(self.playLine)
        self.playLine.method = 'agg'

        self.view.add(self.selectRect)
        self.visuals.append(self.selectRect)

    def set_play_time(self, time):
        self.playLine.set_data(np.array([[time, -2], [time, 2]]), width = 5)

    def set_begin_selection_time(self, time):
        self.selectRect.set_initial_time(time)

        mintime = self.selectRect.minimum_time()
        if mintime is not None:
            self.set_play_time(mintime)

    def set_end_selection_time(self, time):
        self.selectRect.set_final_time(time)

        mintime = self.selectRect.minimum_time()
        if mintime is not None:
            self.set_play_time(mintime)

    def _configure_1d(self, fg_color=None):
        if self._configured:
            return
        if fg_color is None:
            fg = self._fg
        else:
            fg = fg_color
        self.yaxis = scene.AxisWidget(orientation='left', text_color=fg,
                                      axis_color=fg, tick_color=fg)
        self.yaxis.stretch = (0.1, 1)
        self.grid.add_widget(self.yaxis, row=2, col=2)

        self.ylabel = scene.Label("", rotation=-90)
        self.ylabel.stretch = (0.05, 1)
        self.grid.add_widget(self.ylabel, row=2, col=1)

        self.yaxis.visible = False

        self.xaxis = scene.AxisWidget(orientation='bottom', text_color=fg,
                                      axis_color=fg, tick_color=fg)
        self.xaxis.stretch = (1, 0.1)
        self.grid.add_widget(self.xaxis, row=3, col=3)

        self.xlabel = scene.Label("")
        self.xlabel.stretch = (1, 0.05)
        self.grid.add_widget(self.xlabel, row=4, col=3)

        self.view.camera = SCTAudioCamera(zoom = 'x', pan = 'x')
        self.camera = self.view.camera

        self.xaxis.link_view(self.view)
        self.yaxis.link_view(self.view)
        self._configured = True

    def _configure_2d(self, fg_color=None):
        if self._configured:
            return
        if fg_color is None:
            fg = self._fg
        else:
            fg = fg_color
        self.yaxis = scene.AxisWidget(orientation='left', text_color=fg,
                                      axis_color=fg, tick_color=fg)
        self.yaxis.stretch = (0.1, 1)
        self.grid.add_widget(self.yaxis, row=2, col=2)

        self.ylabel = scene.Label("", rotation=-90)
        self.ylabel.stretch = (0.05, 1)
        self.grid.add_widget(self.ylabel, row=2, col=1)

        self.xaxis = scene.AxisWidget(orientation='bottom', text_color=fg,
                                      axis_color=fg, tick_color=fg)
        self.xaxis.stretch = (1, 0.1)
        self.grid.add_widget(self.xaxis, row=3, col=3)

        self.xlabel = scene.Label("")
        self.xlabel.stretch = (1, 0.05)
        self.grid.add_widget(self.xlabel, row=4, col=3)

        self.view.camera = SCTAudioCamera(zoom = 'x', pan = 'x')
        self.camera = self.view.camera

        self.xaxis.link_view(self.view)
        self.yaxis.link_view(self.view)
        self._configured = True


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



class AnnotationPlotWidget(SelectablePlotWidget):
    def __init__(self, num_types, *args, **kwargs):
        super(AnnotationPlotWidget, self).__init__(*args, **kwargs)
        self._configure_1d()
        self.unfreeze()
        self.num_types = num_types
        self.annotation_visuals = []
        self.line_visuals = []
        self.breakline = SCTLinePlot(None, width = 5, color = 'k')
        self.breakline.method = 'agg'
        self.view.add(self.breakline)
        self.visuals.append(self.breakline)
        self.freeze()

        cycle = ['b', 'r']

        for i in range(self.num_types):
            c = cycle[i % len(cycle)]
            self.line_visuals.append(SCTLinePlot(None, connect='segments',
                        width = 5, color = c))
            self.view.add(self.line_visuals[i])
            self.visuals.append(self.line_visuals[i])

            self.annotation_visuals.append(ScalingText(None, pos = [0, 0]))
            self.view.add(self.annotation_visuals[i])
            self.visuals.append(self.annotation_visuals[i])

    def set_max_time(self, max_time):
        if max_time is None:
            self.view.camera.set_bounds((0, 1), (-1, 1))
            self.breakline.set_data(None)
        else:
            self.breakline.set_data(np.array([[-1,0], [max_time+1,0]]))
            self.view.camera.set_bounds((0, max_time), (-1, 1))

    def set_annotations(self, data):
        if data is None:
            for i in range(self.num_types):
                self.line_visuals[i].set_data(None)
                self.annotation_visuals[i].set_data(None, [0, 0])
            return

        line_data, text_data = generate_boundaries(data)
        for i in range(self.num_types):
            self.line_visuals[i].set_data(line_data[i])
            self.annotation_visuals[i].set_data(text_data[i][0], pos = text_data[i][1])

        self.view.camera.set_range(x = (0, 30))

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

class PitchPlotWidget(SelectablePlotWidget):

    def pitch(self, annotations, max_time = None):
        self._configure_2d()
        data = []
        try:
            for x in annotations:
                keys = list(x.pitch.keys())
                for i,(t, p) in enumerate(x.pitch.items()):
                    if p <= 0:
                        continue
                    if i <= 0:
                        continue
                    if x.pitch[keys[i-1]] <= 0:
                        continue
                    data.append([keys[i-1], x.pitch[keys[i-1]]])
                    data.append([t, p])
        except AttributeError:
            return
        print(len(data))
        data = np.array(data)
        print(data.shape)
        plotmin = np.amin(data, 0)
        plotmax = np.amax(data, 0)
        print(plotmin, plotmax)
        if max_time is None:
            max_time = plotmax[0]
        line = SCTLinePlot(data, connect='segments', marker_size=0)
        self.view.add(line)
        self.visuals.append(line)
        for v in generate_boundaries(annotations, text = False):
            self.view.add(v)
            self.visuals.append(v)

        self.view.camera.set_bounds((0, max_time), (plotmin[1], plotmax[1]))
        initial_view = 30
        self.view.camera.set_range(x = (0, initial_view))

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

class SCTCentralWidget(scene.widgets.Widget):

    def add_grid(self, *args, **kwargs):
        """
        Create a new Grid and add it as a child widget.
        All arguments are given to Grid().
        """
        grid = SCTGrid(*args, **kwargs)
        return self.add_widget(grid)


class SCTAudioWidget(scene.SceneCanvas):
    def __init__(self, num_types, window_length = 0.005, time_step = 0.0001):
        self._plot_widgets = []
        self._grid = None  # initialize before the freeze occurs
        super(SCTAudioWidget, self).__init__(size=(800, 400), bgcolor = 'w', show=False)
        self._grid = self.central_widget.add_grid(num_types, window_length, time_step)
        self._grid._default_class = PlotWidget
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
        import time
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
        import time

        begin = time.time()
        self['annotations'].set_annotations(annotations)
        self['waveform'].set_annotations(annotations)
        print('annotation time', time.time() - begin)


class ScaledTicker(Ticker):
    def __init__(self, axis, scale = None):
        self.axis = axis
        self.scale = scale

    def _get_tick_frac_labels(self):
        """Get the major ticks, minor ticks, and major labels"""
        minor_num = 4  # number of minor ticks per major division
        if (self.axis.scale_type == 'linear'):
            domain = self.axis.domain
            if domain[1] < domain[0]:
                flip = True
                domain = domain[::-1]
            else:
                flip = False
            offset = domain[0]
            scale = domain[1] - domain[0]

            transforms = self.axis.transforms
            length = self.axis.pos[1] - self.axis.pos[0]  # in logical coords
            n_inches = np.sqrt(np.sum(length ** 2)) / transforms.dpi

            # major = np.linspace(domain[0], domain[1], num=11)
            # major = MaxNLocator(10).tick_values(*domain)
            major = _get_ticks_talbot(domain[0], domain[1], n_inches, 2)

            if self.scale is not None:
                labels = ['%g' % (x * self.scale,) for x in major]
            else:
                labels = ['%g' % x for x in major]
            majstep = major[1] - major[0]
            minor = []
            minstep = majstep / (minor_num + 1)
            minstart = 0 if self.axis._stop_at_major[0] else -1
            minstop = -1 if self.axis._stop_at_major[1] else 0
            for i in range(minstart, len(major) + minstop):
                maj = major[0] + i * majstep
                minor.extend(np.linspace(maj + minstep,
                                         maj + majstep - minstep,
                                         minor_num))
            major_frac = (major - offset) / scale
            minor_frac = (np.array(minor) - offset) / scale
            major_frac = major_frac[::-1] if flip else major_frac
            use_mask = (major_frac > -0.0001) & (major_frac < 1.0001)
            major_frac = major_frac[use_mask]
            labels = [l for li, l in enumerate(labels) if use_mask[li]]
            minor_frac = minor_frac[(minor_frac > -0.0001) &
                                    (minor_frac < 1.0001)]
        elif self.axis.scale_type == 'logarithmic':
            return NotImplementedError
        elif self.axis.scale_type == 'power':
            return NotImplementedError
        return major_frac, minor_frac, labels

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
