
import numpy as np

from vispy import plot as vp
from scipy.io import wavfile

from vispy.scene.cameras.panzoom import PanZoomCamera
from vispy.geometry import Rect
from vispy.plot.plotwidget import PlotWidget
from vispy.visuals.axis import Ticker, _get_ticks_talbot
from vispy.util.fourier import stft
from vispy import scene
from vispy.visuals.image import ImageVisual


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
    return (((value - oldmin) * newrange) / oldrange) + newmin

class SCTSpectrogramVisual(ImageVisual):
    def __init__(self, x, sr, window_length = 0.005, step = 0.001):
        self._signal = x
        self.window_length = window_length
        self.step = step
        self._window = 'hann'
        self._color_scale='log'
        self._cmap='cubehelix'
        self._clim='auto'
        self._sr = sr
        self.min_time = 0
        self.max_time = len(x) / sr

        self._n_fft = int(window_length * sr)
        data = self._do_spec(self.min_time, self.max_time)

        super(SCTSpectrogramVisual, self).__init__(data,
                clim=self._clim, cmap=self._cmap, interpolation = 'gaussian')

    @property
    def yscale(self):
        return 1 / float(self._n_fft) * float(self._sr)

    def ymax(self):
        return (self._n_fft / 2 + 1)

    def ymin(self):
        return 0

    def xmax(self):
        return self._data.shape[1]

    def xmin(self):
        return 0

    def _do_spec(self, min_time, max_time):
        if min_time < 0:
            min_time = 0
        if max_time - min_time > 30:
            step = 0.1
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

        return data

    def _prepare_draw(self, view):
        seconds = view.canvas[0:2, 0].view.camera.rect.width
        min_time = view.canvas[0:2, 0].view.camera.rect.left
        max_time = view.canvas[0:2, 0].view.camera.rect.right

        self.set_data(self._do_spec(min_time, max_time))
        super(SCTSpectrogramVisual, self)._prepare_draw(view)
        view.canvas[2:4, 0].view.camera.set_bounds((self.xmin(), self.xmax()), (self.ymin(), self.ymax()))
        view.canvas[2:4, 0].view.camera.set_range()

Spectrogram = scene.visuals.create_visual_node(SCTSpectrogramVisual)

class SCTAudioPlotWidget(PlotWidget):
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

    def spectrogram(self, x, window_length, step, sr, max_time):
        self._configure_2d()

        # XXX once we have axes, we should use "fft_freqs", too
        spec = Spectrogram(x, sr, window_length, step)
        #spec._data = spec._data[:,:5000]
        #self.xaxis.axis.ticker = ScaledTicker(self.xaxis.axis, scale = spec.xscale)
        self.yaxis.axis.ticker = ScaledTicker(self.yaxis.axis, scale = spec.yscale)
        self.view.add(spec)
        self.view.camera.set_bounds((spec.xmin(), spec.xmax()), (spec.ymin(), spec.ymax()))
        self.view.camera.set_range()
        return spec

    def annotations(self, data, max_time = None):
        self._configure_1d()
        if max_time is None:
            max_time = max(x['end'] for x in data)

        for v in generate_boundaries(data):
            self.view.add(v)
            self.visuals.append(v)

        breakline = scene.LinePlot([[0,0], [max_time,0]], width = 20, color = 'k')
        self.view.add(breakline)
        self.visuals.append(breakline)
        self.view.camera.set_bounds((0, max_time), (-1, 1))
        self.view.camera.set_range(x = (0, 30))
        #self.view.camera.set_range()

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

    def waveform(self, data, sr, annotations):
        self._configure_2d()
        plotmin = np.min(data)
        plotmax = np.max(data)

        t = np.arange(data.shape[0]) / float(sr)
        data = np.array((t, data)).T
        line = scene.LinePlot(data, connect='strip',marker_size=0)
        self.view.add(line)
        self.visuals.append(line)
        for v in generate_boundaries(annotations, text = False):
            self.view.add(v)
            self.visuals.append(v)

        self.view.camera.set_bounds((0, len(data) / sr), (plotmin, plotmax))
        initial_view = 30
        self.view.camera.set_range(x = (0, initial_view))
        #self.view.camera.set_range()
        return line

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
        line = scene.LinePlot(data, connect='segments', marker_size=0)
        self.view.add(line)
        self.visuals.append(line)
        for v in generate_boundaries(annotations, text = False):
            self.view.add(v)
            self.visuals.append(v)

        self.view.camera.set_bounds((0, max_time), (plotmin[1], plotmax[1]))
        initial_view = 30
        self.view.camera.set_range(x = (0, initial_view))

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

    output = []
    plotdata = np.array(plotdata)
    line = scene.LinePlot(plotdata, connect='segments',
                    width = 20, color = 'r')
    output.append(line)
    line = scene.LinePlot(subplotdata, connect='segments',
                    width = 20, color = 'b')
    output.append(line)
    if text:
        text = ScalingText(annodata, pos = posdata)
        output.append(text)
        text = PhoneScalingText(subannodata, pos = subposdata)
        output.append(text)
    return output

class SCTSummaryWidget(vp.Fig):
    def __init__(self, parent = None):
        super(SCTSummaryWidget, self).__init__(size=(800, 400), show=False)
        self._grid._default_class = SCTAudioPlotWidget
        self.unfreeze()
        self.parent = parent
        self.annotations = None

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



class SCTAudioWidget(vp.Fig):
    def __init__(self):

        super(SCTAudioWidget, self).__init__(size=(800, 400), show=False)
        self._grid._default_class = SCTAudioPlotWidget

    def plot(self, audio_file, annotations):
        import time

        begin = time.time()
        sr, data = wavfile.read(audio_file)
        data = data / 32768
        print('read wav time', time.time() - begin)
        max_time = len(data) / sr
        begin = time.time()
        print(self[0:2, 0])
        self[0:2, 0].annotations(annotations, max_time)
        #self[0:2, 0].xaxis.visible = False
        print('annotation time', time.time() - begin)

        begin = time.time()
        self[2:4, 0].spectrogram(data, 0.005, 0.0001, sr, max_time)
        #self[2:4, 0].xaxis.visible = False
        print('spec time', time.time() - begin)

        begin = time.time()
        self[4:6, 0].waveform(data, sr, annotations)
        print('wave time', time.time() - begin)
        self[4:6, 0].camera.link(self[0:2, 0].camera)

        #begin = time.time()
        #self[6:8, 0].pitch(annotations, max_time)
        #print('pitch time', time.time() - begin)
        #self[6:8, 0].camera.link(self[0:2, 0].camera)



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
        seconds = view.canvas[0:2, 0].view.camera.rect.width
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

class PhoneScalingText(ScalingText):
    minpps = 10
    maxpps = 5000
    min_font_size = 1
    max_font_size = 30
