
from PyQt5 import QtGui, QtCore, QtWidgets

from ..helper import get_system_font_height

class ClickableLabel(QtWidgets.QLabel):
    clicked = QtCore.pyqtSignal()
    def __init__(self, *args, **kwargs):
        super(ClickableLabel, self).__init__(*args, **kwargs)

        self.enabled = True

    def toggle(self):
        self.enabled = not self.enabled
        if self.enabled:
            self.setStyleSheet("QLabel { color : black; }")
        else:
            self.setStyleSheet("QLabel { color : grey; }")

    def mousePressEvent(self, event):
        self.clicked.emit()

class HierarchyWidget(QtWidgets.QWidget):
    toggleSpectrogram = QtCore.pyqtSignal()
    toggleFormants = QtCore.pyqtSignal()
    togglePitch = QtCore.pyqtSignal()
    channelChanged = QtCore.pyqtSignal(int)
    def __init__(self, parent = None):
        super(HierarchyWidget, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        self.hierarchy = None
        base_size =  get_system_font_height()
        self.hierarchyLayout = QtWidgets.QVBoxLayout()
        self.hierarchyLayout.setSpacing(0)
        self.hierarchyLayout.setStretch(0, 0)
        self.hierarchyLayout.setContentsMargins(0,0,0,0)
        self.hierarchyLayout.setAlignment(QtCore.Qt.AlignTop)
        self.spectrumLayout = QtWidgets.QFormLayout()
        self.spectrumLayout.setSpacing(0)
        self.spectrumLayout.setContentsMargins(0,0,0,0)

        self.specLabel = ClickableLabel('Spectrogram')
        self.specLabel.clicked.connect(self.toggleSpecLabel)
        self.setFixedWidth(self.specLabel.fontMetrics().width(self.specLabel.text())*2)
        self.specLabel.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Minimum)

        self.formantLabel = ClickableLabel('Formants')
        self.formantLabel.clicked.connect(self.toggleFormantLabel)
        #self.setFixedWidth(self.formantLabel.fontMetrics().width(self.formantLabel.text())*2)
        self.formantLabel.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Minimum)

        self.pitchLabel = ClickableLabel('Pitch')
        self.pitchLabel.clicked.connect(self.togglePitchLabel)
        #self.setFixedWidth(self.pitchLabel.fontMetrics().width(self.pitchLabel.text())*2)
        self.pitchLabel.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Minimum)
        v = ClickableLabel('Voicing')
        i = ClickableLabel('Intensity')
        v.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Minimum)
        i.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Minimum)
        self.spectrumLayout.addRow(self.specLabel)
        self.spectrumLayout.addRow(self.formantLabel)
        self.spectrumLayout.addRow(self.pitchLabel)

        self.channelSelect = QtWidgets.QComboBox()
        self.setNumChannels(1)
        self.channelSelect.currentIndexChanged.connect(self.channelChanged.emit)
        self.spectrumLayout.addRow('Audio channel', self.channelSelect)

        #self.spectrumLayout.addWidget(v)
        #self.spectrumLayout.addWidget(i)
        self.hWidget = QtWidgets.QWidget()
        self.hWidget.setLayout(self.hierarchyLayout)

        
        
        layout.addWidget(self.hWidget)

        layout.addLayout(self.spectrumLayout)

        self.setLayout(layout)

    def setNumChannels(self, n_channels):
        self.channelSelect.clear()
        for i in range(n_channels):
            self.channelSelect.addItem(str(i+1))

    def toggleSpecLabel(self):
        self.toggleSpectrogram.emit()
        self.specLabel.toggle()

    def toggleFormantLabel(self):
        self.toggleFormants.emit()
        self.formantLabel.toggle()

    def togglePitchLabel(self):
        self.togglePitch.emit()
        self.pitchLabel.toggle()

    def resizeEvent(self, event):
        super(HierarchyWidget, self).resizeEvent(event)
        self.updateHierachy(self.hierarchy)

    def updateHierachy(self, hierarchy):
        while self.hierarchyLayout.count():
            item = self.hierarchyLayout.takeAt(0)
            if item.widget() is None:
                continue
            item.widget().deleteLater()
        self.hierarchy = hierarchy
        if self.hierarchy is not None:
            if len(self.hierarchy.keys()) == 0:
                return
            space = (self.height() / 2) * 0.75
            half_space = space / 2
            per_type = half_space / len(self.hierarchy.keys())
            base_size =  get_system_font_height()
            spacing = (per_type - base_size) / 2
            self.hierarchyLayout.addSpacing(spacing * 2)
            for at in self.hierarchy.highest_to_lowest:
                w = QtWidgets.QLabel(at)
                w.setFixedWidth(w.fontMetrics().width(w.text()))
                w.setFixedHeight(base_size)
                w.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Minimum)
                #w.clicked.connect(self.updateHierarchyVisibility)
                self.hierarchyLayout.addSpacing(spacing)
                self.hierarchyLayout.addWidget(w)
                self.hierarchyLayout.addSpacing(spacing)
            keys = []
            for k, v in sorted(self.hierarchy.subannotations.items()):
                for s in v:
                    keys.append((k,s))
            if keys:
                per_sub_type = half_space / len(keys)
                spacing = (per_sub_type - base_size) / 2
                for k in sorted(keys):
                    w = QtWidgets.QLabel('{} - {}'.format(*k))
                    w.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Minimum)
                    w.setFixedWidth(w.fontMetrics().width(w.text()))
                    w.setFixedHeight(base_size)
                    #w.clicked.connect(self.updateHierarchyVisibility)
                    self.hierarchyLayout.addSpacing(spacing)
                    self.hierarchyLayout.addWidget(w)
                    self.hierarchyLayout.addSpacing(spacing)
