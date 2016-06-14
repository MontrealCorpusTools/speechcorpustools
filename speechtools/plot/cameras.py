import numpy as np

from vispy.scene.cameras.panzoom import PanZoomCamera
from vispy.geometry import Rect

from .helper import rescale

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
        if self.zoom is None:
            return
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
        if self._pan_axis is None:
            return
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
