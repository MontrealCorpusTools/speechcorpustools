import numpy as np

from vispy import scene
from vispy.plot.plotwidget import PlotWidget

from ..visuals import SCTLinePlot, SelectionRect, SelectionLine, PlayLine

from ..cameras import SCTAudioCamera, BaseCamera

class SelectablePlotWidget(PlotWidget):
    def __init__(self, *args, **kwargs):
        super(SelectablePlotWidget, self).__init__(*args, **kwargs)

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

        self.view = self.grid.add_view(row=2, col=4,
                                       border_color='grey', bgcolor="#efefef")

        self.view.camera = SCTAudioCamera(zoom = None, pan = None)
        self.camera = self.view.camera

        self.xaxis.link_view(self.view)
        self.yaxis.link_view(self.view)
        self.unfreeze()
        self.selection_time_line = SelectionLine()
        self.selection_time_line.visible = False
        self.selection_rect = SelectionRect()
        self.selection_rect.visible = False
        self.play_time_line = PlayLine()
        self.play_time_line.visible = False
        self.view.add(self.selection_time_line)
        self.view.add(self.play_time_line)
        self.view.add(self.selection_rect)
        self.freeze()
        self._configured = True

    def set_selection_time(self, time):
        if time is None:
            self.selection_time_line.visible = False
        else:
            self.selection_time_line.visible = True
            pos = np.array([[time, -1.5], [time, 1.5]])
            self.selection_time_line.set_data(pos = pos)
