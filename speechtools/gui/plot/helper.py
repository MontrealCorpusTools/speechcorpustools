import numpy as np


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


def rescale(value, oldmax, newmax):
    return value * newmax/oldmax
