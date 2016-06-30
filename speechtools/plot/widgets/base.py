import numpy as np

from vispy import scene
from vispy.plot.plotwidget import PlotWidget

from ..visuals import SCTLinePlot, SelectionRect, SelectionLine, PlayLine

from ..cameras import SCTAudioCamera

class SelectablePlotWidget(PlotWidget):
    def _configure_2d(self, fg_color=None):

        super(SelectablePlotWidget, self)._configure_2d(fg_color)

        self.view.camera = SCTAudioCamera(zoom = None, pan = None)
        self.camera = self.view.camera

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

    def set_selection_time(self, time):
        if time is None:
            self.selection_time_line.visible = False
        else:
            self.selection_time_line.visible = True
            pos = np.array([[time, -1.5], [time, 1.5]])
            self.selection_time_line.set_data(pos = pos)