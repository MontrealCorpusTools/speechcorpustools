import sys
import numpy as np

from PyQt5 import QtGui, QtCore, QtWidgets
from vispy import app, scene
from vispy.scene import visuals
from vispy.geometry import generation as gen, create_sphere

class DemoScene(QtWidgets.QWidget):
    def __init__(self, keys='interactive'):
        self.keymapping = {'z':self.setZ,
                           'x':self.setX,
                           'y':self.setY,
                           'Space':self.setZoom,
                           '=':self.largermarker,
                           '+':self.largermarker,
                           '-':self.smallermarker,
                           's':self.createsphere}
        super(DemoScene, self).__init__()
        #Layout and canvas creation
        box = QtWidgets.QVBoxLayout(self)
        self.resize(500,500)
        self.setLayout(box)
        self.canvas = scene.SceneCanvas(keys=keys)
        box.addWidget(self.canvas.native)


        #Connect events
        self.canvas.events.mouse_press.connect(self.on_mouse_press)
        self.canvas.events.mouse_release.connect(self.on_mouse_release)
        self.canvas.events.mouse_move.connect(self.on_mouse_move)

        #Setup some defaults
        self.mesh = None
        self.selected = []
        self.white = (1.0, 1.0, 1.0, 1.0)
        self.black = (0.0, 0.0, 0.0, 0.0)

        #Selection
        self.rectselect = False
        self.selectionpolygon = None

        #Camera
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = scene.cameras.TurntableCamera(elevation = 25, azimuth=20, distance = 2.0, center=(0,0,0))
        self.view.camera.set_ortho()
        self.view.camera._update_camera_pos()

        #Test data
        self.data = np.random.uniform(-1, 1, size=(200, 3))
        self.minz = np.min(self.data[:,2])
        self.facecolor = np.ones((200,4), dtype=np.float)
        self.ptsize = 3
        self.scatter = visuals.Markers()
        self.scatter.set_data(self.data, face_color=self.facecolor, edge_color=None, size=self.ptsize)

        #Add scatter to view and find the transform
        self.view.add(self.scatter)
        self.tr = self.scatter.node_transform(self.canvas.canvas_cs)

        #self.mappeddata = self.tr.simplified().map(self.data)

        #self.inv = self.tr.simplified().imap(self.mappeddata)
        #print self.mappeddata[0]
        #print self.data[0]
        #print self.inv[0]

        #print self.tr.simplified().imap(self.mappeddata)
        # Add a 3D axis to keep us oriented
        axis = scene.visuals.XYZAxis(parent=self.view.scene)

    def markselected(self):
        """
        Change the color of the selected point
        """
        self.facecolor[self.facecolor[:,1] != 1.0] = self.white
        self.scatter.set_data(self.data, face_color=self.facecolor, size=self.ptsize)
        for i in self.selected:
            self.facecolor[i] = [1.0, 0.0, 0.0, 1]

        self.scatter.set_data(self.data, face_color = self.facecolor, size=self.ptsize)
        self.scatter.update()

    def keyPressEvent(self, event):
        """
        Bootstrap the Qt keypress event items
        """
        if event.text() in self.keymapping.keys():
            self.keymapping[event.text()]()
        elif event.key() == QtCore.Qt.Key_Shift:
            self.rectselect = True
        elif event.key() == QtCore.Qt.Key_Space:
            self.keymapping['Space']()
        else:
            print(event.text())

    def keyReleaseEvent(self, event):
        """
        Bootstrap the Qt Key release event
        """
        if event.key() == QtCore.Qt.Key_Shift:
            self.rectselect = False

    def on_mouse_press(self, event):
        """
        Mouse button press event
        """
        if event.button == 1 and self.rectselect == False:
            #Ray intersection on the CPU to highlight the selected point(s)
            data = self.tr.simplified().map(self.data)[:,:2]
            m1 = data > (event.pos - 4)
            m2 = data < (event.pos + 4)
            self.selected = np.argwhere(m1[:,0] & m1[:,1] & m2[:,0] & m2[:,1])
            self.markselected()
        elif event.button == 1 and self.rectselect == True:
            #Panning
            pass

        elif event.button == 2 and self.rectselect == True:
            if self.selectionpolygon is None:
                origin = np.array([event.pos[0], event.pos[1], -0.99799905, 1.0])
                origin = self.tr.simplified().imap(origin)
                self.polydata = np.empty((4,3))
                self.polydata[0] = origin[:3]
                self.selectionpolygon = visuals.Polygon(pos=self.polydata, color=(1.0, 0.0, 0.0, 1.0))
                self.view.add(self.selectionpolygon)

    '''
    def contextMenuEvent(self, event):
        """
        Bootstrap the Qt Context menu event
        """
        if len(self.selected) > 0:
            menu = QtGui.QMenu(self)
            menu.addAction('A')
            menu.addAction('B')
            menu.addAction('C')
            action = menu.exec_(event.globalPos())
    '''

    def on_mouse_release(self, event):
        if event.button == 2 and self.rectselect == True:
            #Selecting using a rectangle
            self.facecolor[self.facecolor[:,1] != 1.0] = self.white
            x1, y1 = event.last_event.pos
            x0, y0 = event.press_event.pos

            #Sort for the origin
            if x1 < x0:
                x0, x1 = x1, x0
            if y1 < y0:
                y0, y1 = y1, y0

            data = self.tr.simplified().map(self.data)[:,:2]
            m1 = data[:,0] < x1
            m2 = data[:,0] > x0
            m3 = data[:,1] < y1
            m4 = data[:,1] > y0

            m1 =m1 * m2
            m2 = m3 * m4

            self.selected = np.argwhere(m1 & m2)
            self.markselected()

            #Remove the selection polygon
            self.selectionpolygon = None

    def on_mouse_move(self, event):
        if event.button == 2 and event.is_dragging:
            pos = np.array([event.pos[0], event.pos[1], -0.99799905, 1.0])
            #data = self.tr.simplified().map(self.data)
            #inv = self.tr.simplified().imap(data)
            #pos = self.tr.simplified().map(pos)
            invpos = self.tr.simplified().imap(pos)
            #print data[0], inv[0], invpos
            self.polydata[1] = [self.polydata[0,0], invpos[1], self.polydata[0,2]]
            self.polydata[2] = [invpos[0], invpos[1], self.polydata[0,2]]
            self.polydata[3] = [invpos[0],self.polydata[0,1], self.polydata[0,2]]
            self.selectionpolygon.data = self.polydata
            self.selectionpolygon.update()

    def setZ(self):
        self.view.camera.azimuth = 0
        self.view.camera.elevation = 90
        self.view.camera._update_camera_pos()

    def setX(self):
        self.view.camera.azimuth = 0
        self.view.camera.elevation = 0
        self.view.camera._update_camera_pos()

    def setY(self):
        self.view.camera.azimuth = 90
        self.view.camera.elevation = 0
        self.view.camera._update_camera_pos()

    def setZoom(self):
        #Need bounding box info / functionality
        pass

    def largermarker(self):
        self.ptsize += 2
        self.scatter._v_size_var = self.ptsize
        self.scatter._marker_fun['v_size'] = self.scatter._v_size_var
        self.scatter.update()

    def smallermarker(self):
        self.ptsize -= 2
        self.scatter._v_size_var = self.ptsize
        self.scatter._marker_fun['v_size'] = self.scatter._v_size_var
        self.scatter.update()

    def createsphere(self, nrows=20, ncols=20, radius=1.0):
        if not self.mesh:
            mdata = create_sphere(nrows, ncols, radius)
            self.mesh = visuals.Mesh(meshdata=mdata,vertex_colors='black',
                                     face_colors=(1.0, 0.0, 0.0, 1.0),
                                     color=(0.5, 0.5, 0.5, .75))
            self.view.add(self.mesh)
        else:
            print(dir(self.mesh))

if __name__ == '__main__':
    appQt = QtWidgets.QApplication(sys.argv)
    view = DemoScene(keys='interactive')
    view.show()
    appQt.exec_()
