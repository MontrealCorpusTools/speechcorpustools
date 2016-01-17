
from vispy import scene

from vispy.plot.plotwidget import PlotWidget

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
