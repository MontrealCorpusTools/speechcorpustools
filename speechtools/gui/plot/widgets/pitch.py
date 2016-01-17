
from .base import SelectablePlotWidget

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
