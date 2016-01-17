import numpy as np

from vispy import scene
from vispy.plot.plotwidget import PlotWidget

from ..visuals import SCTLinePlot, SelectionRect

from ..cameras import SCTAudioCamera

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

