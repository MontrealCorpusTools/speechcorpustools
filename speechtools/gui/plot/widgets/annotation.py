
import numpy as np

from .base import SelectablePlotWidget

from ..visuals import SCTLinePlot, ScalingText, PhoneScalingText

from ..helper import generate_boundaries

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
