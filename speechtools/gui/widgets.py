from struct import pack
import time
import numpy as np
from librosa.core import resample
from scipy.io import wavfile
from PyQt5 import QtGui, QtCore, QtWidgets, QtMultimedia

from polyglotdb.gui.widgets import ConnectWidget, ImportWidget, ExportWidget

from .plot import AnnotationWidget, SpectralWidget, SCTSummaryWidget

from .workers import (QueryWorker, DiscourseQueryWorker, DiscourseAudioWorker,
                        Lab1QueryWorker,
                        ExportQueryWorker, PitchGeneratorWorker)

from .models import QueryResultsModel, ProxyModel

from .views import ResultsView

from speechtools.corpus import CorpusContext

def get_system_font_height():
    f = QtGui.QFont()
    fm = QtGui.QFontMetrics(f)
    return fm.height()

class SubannotationDialog(QtWidgets.QDialog):
    def __init__(self, type = None,
                subannotation_types = None, parent = None):
        super(SubannotationDialog, self).__init__(parent)
        layout = QtWidgets.QFormLayout()

        if subannotation_types is None:
            subannotation_types = ['burst', 'voicing']

        self.typeEdit = QtWidgets.QComboBox()
        for sa in subannotation_types:
            self.typeEdit.addItem(sa)

        layout.addRow('Type', self.typeEdit)

        mainlayout = QtWidgets.QVBoxLayout()
        mainlayout.addLayout(layout)

        aclayout = QtWidgets.QHBoxLayout()

        self.acceptButton = QtWidgets.QPushButton('Save')
        self.acceptButton.clicked.connect(self.accept)
        self.rejectButton = QtWidgets.QPushButton('Cancel')
        self.rejectButton.clicked.connect(self.reject)

        aclayout.addWidget(self.acceptButton)
        aclayout.addWidget(self.rejectButton)

        mainlayout.addLayout(aclayout)

        self.setLayout(mainlayout)

        self.setWindowTitle('Add subannotation')

    def value(self):
        return self.typeEdit.currentText()

class NoteDialog(QtWidgets.QDialog):
    def __init__(self, annotation, parent = None):
        super(NoteDialog, self).__init__(parent)
        layout = QtWidgets.QFormLayout()

        self.typeEdit = QtWidgets.QLineEdit()
        self.typeEdit.setText('notes')

        self.notesEdit = QtWidgets.QLineEdit()
        if annotation.notes is not None:
            self.notesEdit.setText(annotation.notes)

        layout.addRow('Note type', self.typeEdit)
        layout.addRow('Note contents', self.notesEdit)

        mainlayout = QtWidgets.QVBoxLayout()
        mainlayout.addLayout(layout)

        aclayout = QtWidgets.QHBoxLayout()

        self.acceptButton = QtWidgets.QPushButton('Save')
        self.acceptButton.clicked.connect(self.accept)
        self.rejectButton = QtWidgets.QPushButton('Cancel')
        self.rejectButton.clicked.connect(self.reject)

        aclayout.addWidget(self.acceptButton)
        aclayout.addWidget(self.rejectButton)

        mainlayout.addLayout(aclayout)

        self.setLayout(mainlayout)

        self.setWindowTitle('Add note')

    def accept(self):
        contents = self.notesEdit.text()
        if not contents:
            self.reject()
        else:
            super(NoteDialog, self).accept()

    def value(self):
        type = self.typeEdit.text()
        if not type:
            type = 'notes'
        contents = self.notesEdit.text()
        return {type: contents}

class Generator(QtCore.QBuffer):

    def __init__(self, format, parent):
        super(Generator, self).__init__(parent)

        self.format = format
        self.signal = None
        self.min_time = None
        self.max_time = None

    def start(self):
        self.open(QtCore.QIODevice.ReadOnly)

    def set_signal(self, data):
        self.signal = data

    def generateData(self, min_time, max_time):
        if min_time == self.min_time and max_time == self.max_time:
            self.reset()
            return
        self.close()
        self.min_time = min_time
        self.max_time = max_time
        m_buffer = QtCore.QByteArray()
        pack_format = ''

        if self.format.sampleSize() == 8:
            if self.format.sampleType() == QtMultimedia.QAudioFormat.UnSignedInt:
                scaler = lambda x: ((1.0 + x) / 2 * 255)
                pack_format = 'B'
            elif self.format.sampleType() == QtMultimedia.QAudioFormat.SignedInt:
                scaler = lambda x: x * 127
                pack_format = 'b'
        elif self.format.sampleSize() == 16:
            if self.format.sampleType() == QtMultimedia.QAudioFormat.UnSignedInt:
                scaler = lambda x: (1.0 + x) / 2 * 65535
                pack_format = '<H' if self.format.byteOrder() == QtMultimedia.QAudioFormat.LittleEndian else '>H'
            elif self.format.sampleType() == QtMultimedia.QAudioFormat.SignedInt:
                scaler = lambda x: x * 32767
                pack_format = '<h' if self.format.byteOrder() == QtMultimedia.QAudioFormat.LittleEndian else '>h'

        assert(pack_format != '')

        sampleIndex = 0
        #print('begin generate')
        #print(min_time, max_time, max_time - min_time)
        min_samp = int(min_time * self.format.sampleRate())
        max_samp = int(max_time * self.format.sampleRate())
        #print(min_samp, max_samp, max_samp - min_samp)
        data = self.signal[min_samp:max_samp]
        for i in range(data.shape[0]):
            packed = pack(pack_format, int(scaler(data[i])))
            for _ in range(self.format.channelCount()):
                m_buffer.append(packed)
        #print(len(m_buffer), len(m_buffer) / self.format.bytesPerFrame())
        #print('end generate')
        self.setData(m_buffer)
        self.start()

class HierarchyWidget(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(HierarchyWidget, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        self.hierarchy = None
        self.hierarchyLayout = QtWidgets.QVBoxLayout()
        self.hierarchyLayout.setSpacing(0)
        self.hierarchyLayout.setContentsMargins(0,0,0,0)
        self.spectrumLayout = QtWidgets.QVBoxLayout()
        self.spectrumLayout.setSpacing(0)
        self.spectrumLayout.setContentsMargins(0,0,0,0)
        s = QtWidgets.QLabel('Spectrogram')
        self.setFixedWidth(s.fontMetrics().width(s.text())*2)
        f = QtWidgets.QLabel('Formants')
        p = QtWidgets.QLabel('Pitch')
        v = QtWidgets.QLabel('Voicing')
        i = QtWidgets.QLabel('Intensity')
        s.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Minimum)
        f.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Minimum)
        p.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Minimum)
        v.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Minimum)
        i.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Minimum)
        self.spectrumLayout.addWidget(s)
        #self.spectrumLayout.addWidget(f)
        #self.spectrumLayout.addWidget(p)
        #self.spectrumLayout.addWidget(v)
        #self.spectrumLayout.addWidget(i)

        layout.addLayout(self.hierarchyLayout)

        layout.addLayout(self.spectrumLayout)

        self.setLayout(layout)

    def updateHierachy(self, hierarchy):
        if self.hierarchy is not None:
            while self.hierarchyLayout.count():
                item = self.hierarchyLayout.takeAt(0)
                item.widget().deleteLater()
        self.hierarchy = hierarchy
        if self.hierarchy is not None:
            for at in self.hierarchy.highest_to_lowest:
                w = QtWidgets.QLabel(at)
                w.setFixedWidth(w.fontMetrics().width(w.text()))
                #w.clicked.connect(self.updateHierarchyVisibility)
                self.hierarchyLayout.addWidget(w)
        keys = []
        for k, v in sorted(self.hierarchy.subannotations.items()):
            for s in v:
                keys.append((k,s))
        for k in sorted(keys):
            w = QtWidgets.QLabel('{} - {}'.format(*k))
            w.setFixedWidth(w.fontMetrics().width(w.text()))
            #w.clicked.connect(self.updateHierarchyVisibility)
            self.hierarchyLayout.addWidget(w)

class SelectableAudioWidget(QtWidgets.QWidget):
    previousRequested = QtCore.pyqtSignal()
    nextRequested = QtCore.pyqtSignal()
    markedAsAnnotated = QtCore.pyqtSignal(bool)
    def __init__(self, parent = None):
        super(SelectableAudioWidget, self).__init__(parent)
        self.signal = None
        self.sr = None
        self.pitch = None
        self.annotations = None
        self.hierarchy = None
        self.config = None
        self.min_time = None
        self.max_time = None
        self.min_vis_time = None
        self.max_vis_time = None
        self.min_selected_time = None
        self.max_selected_time = None
        self.selected_boundary = None
        self.selected_time = None
        self.rectselect = False
        self.allowSubEdit = True
        self.allowEdit = False
        self.selected_annotation = None
        self.unsaved_annotations = []

        layout = QtWidgets.QVBoxLayout()


        toplayout = QtWidgets.QHBoxLayout()
        bottomlayout = QtWidgets.QHBoxLayout()

        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.audioWidget = AnnotationWidget()
        self.audioWidget.events.mouse_press.connect(self.on_mouse_press)
        self.audioWidget.events.mouse_double_click.connect(self.on_mouse_double_click)
        self.audioWidget.events.mouse_release.connect(self.on_mouse_release)
        self.audioWidget.events.mouse_move.connect(self.on_mouse_move)
        self.audioWidget.events.mouse_wheel.connect(self.on_mouse_wheel)
        w = self.audioWidget.native
        w.setFocusPolicy(QtCore.Qt.NoFocus)
        toplayout.addWidget(w)

        layout.addLayout(toplayout)

        self.spectrumWidget = SpectralWidget()
        self.spectrumWidget.events.mouse_press.connect(self.on_mouse_press)
        self.spectrumWidget.events.mouse_release.connect(self.on_mouse_release)
        self.spectrumWidget.events.mouse_move.connect(self.on_mouse_move)
        self.spectrumWidget.events.mouse_wheel.connect(self.on_mouse_wheel)
        w = self.spectrumWidget.native
        w.setFocusPolicy(QtCore.Qt.NoFocus)
        bottomlayout.addWidget(w)

        layout.addLayout(bottomlayout)

        mainlayout = QtWidgets.QHBoxLayout()
        mainlayout.addLayout(layout)

        self.hierarchyWidget = HierarchyWidget()

        mainlayout.addWidget(self.hierarchyWidget)

        self.setLayout(mainlayout)

        self.pitchWorker = PitchGeneratorWorker()
        self.pitchWorker.dataReady.connect(self.updatePitch)

        self.m_device = QtMultimedia.QAudioDeviceInfo.defaultOutputDevice()
        self.m_output = None

        self.m_format = QtMultimedia.QAudioFormat()
        self.m_format.setSampleRate(16000)
        self.m_format.setChannelCount(1)
        self.m_format.setSampleSize(16)
        self.m_format.setCodec('audio/pcm')
        self.m_format.setByteOrder(QtMultimedia.QAudioFormat.LittleEndian)
        self.m_format.setSampleType(QtMultimedia.QAudioFormat.SignedInt)

        info = QtMultimedia.QAudioDeviceInfo(QtMultimedia.QAudioDeviceInfo.defaultOutputDevice())
        if not info.isFormatSupported(self.m_format):
            qWarning("Default format not supported - trying to use nearest")
            self.m_format = info.nearestFormat(self.m_format)

        self.m_audioOutput = QtMultimedia.QAudioOutput(self.m_device, self.m_format)
        self.m_audioOutput.setNotifyInterval(1)
        self.m_audioOutput.setBufferSize(6400)
        self.m_audioOutput.notify.connect(self.notified)

        self.m_generator = Generator(self.m_format, self)

    def updatePlayTime(self, time):
        if time is None:
            pos = None
        else:
            pos = self.audioWidget.transform_time_to_pos(time)
        self.audioWidget.update_play_time(time)
        self.spectrumWidget.update_play_time(pos)

    def notified(self):
        time = self.m_audioOutput.processedUSecs() / 1000000
        #print(time, self.m_audioOutput.state(),
        #self.m_audioOutput.bytesFree(), self.m_audioOutput.bufferSize(), self.m_audioOutput.periodSize())
        time += self.m_generator.min_time
        self.updatePlayTime(time)

    def focusNextPrevChild(self, next_):
        return False

    def keyPressEvent(self, event):
        """
        Bootstrap the Qt keypress event items
        """
        if event.key() == QtCore.Qt.Key_Shift:
            self.rectselect = True
        elif event.key() == QtCore.Qt.Key_Delete:
            if self.selected_annotation is not None:
                if self.selected_annotation._type not in self.hierarchy:
                    self.selected_annotation._annotation.delete_subannotation(self.selected_annotation)
                    self.updateVisible()
        elif event.key() == QtCore.Qt.Key_Return:
            if self.selected_annotation is not None:
                if self.selected_annotation._type in self.hierarchy:
                    if self.selected_annotation.checked:
                        annotated_value = False
                    else:
                        annotated_value = True
                    self.selected_annotation.update_properties(checked = annotated_value)
                    self.selected_annotation.save()
                    self.markedAsAnnotated.emit(annotated_value)
        elif event.key() == QtCore.Qt.Key_Tab:
            if self.signal is None:
                return
            if self.m_audioOutput.state() == QtMultimedia.QAudio.StoppedState or \
                self.m_audioOutput.state() == QtMultimedia.QAudio.IdleState:
                min_time = self.audioWidget.get_play_time()
                if self.min_selected_time is None:
                    if self.max_vis_time - min_time < 0.01 or min_time <= self.min_vis_time:
                        min_time = self.min_vis_time
                else:
                    #print(min_time, self.max_selected_time)
                    if self.max_selected_time - min_time < 0.01 or min_time <= self.min_selected_time:
                        min_time = self.min_selected_time
                if self.max_selected_time is not None:
                    max_time = self.max_selected_time
                else:
                    max_time = self.max_vis_time
                #print(min_time, max_time, max_time - min_time)
                self.m_generator.generateData(min_time, max_time)
                #print(self.m_generator.pos())
                #print(self.m_audioOutput.periodSize())
                self.m_audioOutput.reset() # Needed to prevent OpenError on Macs
                self.m_audioOutput.start(self.m_generator)
                #print(self.m_audioOutput.error(), self.m_audioOutput.state())
                #print(self.m_generator.pos())
            elif self.m_audioOutput.state() == QtMultimedia.QAudio.ActiveState:
                self.m_audioOutput.suspend()
            elif self.m_audioOutput.state() == QtMultimedia.QAudio.SuspendedState:
                self.m_audioOutput.resume()
        elif event.key() == QtCore.Qt.Key_Left:
            if event.modifiers() == QtCore.Qt.ShiftModifier:
                print('shift left')
            else:
                vis = self.max_vis_time - self.min_vis_time
                to_pan = 0.1 * vis * -1
                self.pan(to_pan)
        elif event.key() == QtCore.Qt.Key_Right:
            if event.modifiers() == QtCore.Qt.ShiftModifier:
                print('shift right')
            else:
                vis = self.max_vis_time - self.min_vis_time
                to_pan = 0.1 * vis
                self.pan(to_pan)
        elif event.key() == QtCore.Qt.Key_Up:
            vis = self.max_vis_time - self.min_vis_time
            center_time = self.min_vis_time + vis / 2
            factor = (1 + 0.007) ** (-30)
            self.zoom(factor, center_time)
        elif event.key() == QtCore.Qt.Key_Down:
            vis = self.max_vis_time - self.min_vis_time
            center_time = self.min_vis_time + vis / 2
            factor = (1 + 0.007) ** (30)
            self.zoom(factor, center_time)
        elif event.key() == QtCore.Qt.Key_Comma:
            self.previousRequested.emit()
        elif event.key() == QtCore.Qt.Key_Period:
            self.nextRequested.emit()
        elif self.selected_annotation is not None:
            existing_label = self.selected_annotation.label
            if existing_label is None:
                existing_label = ''
            if event.key() == QtCore.Qt.Key_Backspace:
                new = existing_label[:-1]
            elif event.text():
                new = existing_label + event.text()
            else:
                return

            self.selected_annotation.update_properties(label = new)
            self.selected_annotation.save()
            self.updateVisible()
        else:
            print(event.key())

    def keyReleaseEvent(self, event):
        """
        Bootstrap the Qt Key release event
        """
        if event.key() == QtCore.Qt.Key_Shift:
            self.rectselect = False

    def find_annotation(self, key, time):
        annotation = None
        for a in self.annotations:
            if a.end < self.min_vis_time:
                continue
            if isinstance(key, tuple):
                elements = getattr(a, key[0])
                for e in elements:
                    subs = getattr(e, key[1])
                    for s in subs:
                        if time >= s.begin and time <= s.end:
                            annotation = s
                            break
                    if annotation is not None:
                        break
            elif key != a._type:
                elements = getattr(a, key)
                for e in elements:
                    if time >= e.begin and time <= e.end:
                        annotation = e
                        break
            elif time >= a.begin and time <= a.end:
                annotation = a
            if annotation is not None:
                break
        return annotation

    def on_mouse_press(self, event):
        """
        Mouse button press event
        """
        self.setFocus(True)
        self.selected_annotation = None

        if event.handled:
            return
        if event.button == 1 and self.rectselect == False:
            self.min_selected_time = None
            self.max_selected_time = None
            self.audioWidget.update_selection(self.min_selected_time, self.max_selected_time)
            time = self.audioWidget.transform_pos_to_time(event.pos)
            selection = self.audioWidget.check_selection(event)
            if selection is not None:
                self.selected_boundary = selection
                self.selected_time = time
            else:
                self.audioWidget.update_play_time(time)
                self.spectrumWidget.update_play_time(event.pos[0])

        elif event.button == 1 and self.rectselect == True:
            self.max_selected_time = None
            self.min_selected_time = self.audioWidget.transform_pos_to_time(event.pos)

    def on_mouse_double_click(self, event):
        self.selected_annotation = None
        if event.button == 1:
            key = self.audioWidget.get_key(event.pos)
            if key is None:
                return
            time = self.audioWidget.transform_pos_to_time(event.pos)
            annotation = self.find_annotation(key, time)
            if annotation is None:
                return
            self.selected_annotation = annotation
            self.min_selected_time = annotation.begin
            self.max_selected_time = annotation.end
            self.audioWidget.update_selection(self.min_selected_time, self.max_selected_time)

            if self.signal is None:
                return
            self.updatePlayTime(self.min_selected_time)
            event.handled = True

    def on_mouse_release(self, event):
        if event.handled:
            return
        is_single_click = not event.is_dragging or abs(np.sum(event.press_event.pos - event.pos)) < 10
        if event.button == 1 and is_single_click and self.rectselect == True:
            key = self.audioWidget.get_key(event.pos)
            if key is None:
                return
            time = self.audioWidget.transform_pos_to_time(event.pos)
            annotation = self.find_annotation(key, time)
            self.selected_annotation = annotation
            self.min_selected_time = annotation.begin
            self.max_selected_time = annotation.end
            self.audioWidget.update_selection(self.min_selected_time, self.max_selected_time)
            if self.signal is None:
                return
            self.updatePlayTime(self.min_selected_time)
        elif event.button == 1 and is_single_click and self.rectselect == False and \
                self.selected_annotation is None:
            time = self.audioWidget.transform_pos_to_time(event.pos)
            if self.signal is None:
                return
            self.updatePlayTime(time)

        elif event.button == 1 and self.selected_boundary is not None and \
            ((isinstance(self.selected_boundary[0], tuple) and self.allowSubEdit)
                or (not isinstance(self.selected_boundary[0], tuple) and self.allowEdit)):
            self.save_selected_boundary()
            self.selected_boundary = None
            self.selected_time = None
            self.audioWidget.update_selection_time(self.selected_time)
            self.spectrumWidget.update_selection_time(self.selected_time)
        elif event.button == 2:
            key = self.audioWidget.get_key(event.pos)

            if key is None:
                return
            update = False
            time = self.audioWidget.transform_pos_to_time(event.pos)
            annotation = self.find_annotation(key, time)
            self.selected_annotation = annotation
            self.min_selected_time = annotation.begin
            self.max_selected_time = annotation.end
            self.audioWidget.update_selection(self.min_selected_time, self.max_selected_time)
            if self.signal is not None:
                if self.m_audioOutput.state() == QtMultimedia.QAudio.SuspendedState:
                    self.m_audioOutput.stop()
                    self.m_audioOutput.reset()
            menu = QtWidgets.QMenu(self)

            subannotation_action = QtWidgets.QAction('Add subannotation...', self)
            note_action = QtWidgets.QAction('Add/edit note...', self)
            check_annotated_action = QtWidgets.QAction('Mark as annotated', self)
            mark_absent_action = QtWidgets.QAction('Delete annotation', self)
            if not isinstance(key, tuple):
                if key == 'phones':
                    if annotation.checked:
                        check_annotated_action.setText('Mark as unannotated')
                    menu.addAction(subannotation_action)
                    menu.addAction(check_annotated_action)
                menu.addAction(note_action)
            else:
                menu.addAction(mark_absent_action)

            action = menu.exec_(event.native.globalPos())
            if action == subannotation_action:
                dialog = SubannotationDialog()
                if dialog.exec_():
                    type = dialog.value()
                    if type not in annotation._subannotations or len(annotation._subannotations[type]) == 0:
                        annotation.add_subannotation(type,
                                begin = annotation.begin, end = annotation.end)
                    update = True
            elif action == note_action:
                dialog = NoteDialog(annotation)
                if dialog.exec_():
                    annotation.update_properties(**dialog.value())
            elif action == check_annotated_action:
                if annotation.checked:
                    annotation.update_properties(checked = False)
                else:
                    annotation.update_properties(checked = True)
                    annotation.save()
            elif action == mark_absent_action:
                annotation._annotation.delete_subannotation(annotation)
                update = True
            if update:
                self.updateVisible()

    def on_mouse_move(self, event):
        snap = True
        if event.button == 1 and event.is_dragging and self.rectselect:
            time = self.audioWidget.transform_pos_to_time(event.pos)
            if self.max_selected_time is None:
                if time < self.min_selected_time:
                    self.max_selected_time = self.min_selected_time
                    self.min_selected_time = time
                else:
                    self.max_selected_time = time
            if time > self.max_selected_time:
                self.max_selected_time = time
            elif time < self.min_selected_time:
                self.min_selected_time = time
            else:
                dist_to_min = time - self.min_selected_time
                dist_to_max = self.max_selected_time - time
                if dist_to_min < dist_to_max:
                    self.min_selected_time = time
                else:
                    self.max_selected_time = time
            self.audioWidget.update_selection(self.min_selected_time, self.max_selected_time)
        elif event.button == 1 and event.is_dragging and \
                self.selected_boundary is not None and \
            ((isinstance(self.selected_boundary[0], tuple) and self.allowSubEdit)
                or (not isinstance(self.selected_boundary[0], tuple) and self.allowEdit)):
                self.selected_time = self.audioWidget.transform_pos_to_time(event.pos)
                if snap:
                    keys = self.audioWidget[0:2, 0].rank_key_by_relevance(self.selected_boundary[0])
                    for k in keys:
                        p, ind = self.audioWidget[0:2, 0].line_visuals[k].select_line(event)
                        if ind != -1:
                            self.selected_time = p[0]
                            break
                self.updatePlayTime(self.min_vis_time)
                self.audioWidget.update_selected_boundary(self.selected_time, *self.selected_boundary)

                self.audioWidget.update_selection_time(self.selected_time)
                selected_pos = self.audioWidget.transform_time_to_pos(self.selected_time)
                self.spectrumWidget.update_selection_time(selected_pos)
        elif event.button == 1 and event.is_dragging:
            last_time = self.audioWidget.transform_pos_to_time(event.last_event.pos)
            cur_time = self.audioWidget.transform_pos_to_time(event.pos)
            delta = last_time - cur_time
            self.pan(delta)
            #Figure out how much time it's panned since the last event
            #Update visible bounds
        elif event.button is None:
            self.audioWidget.update_selection_time(None)
            self.spectrumWidget.update_selection_time(None)
            self.audioWidget.check_selection(event)

    def on_mouse_wheel(self, event):
        self.setFocus(True)
        center_time = self.audioWidget.transform_pos_to_time(event.pos)
        factor = (1 + 0.007) ** (-event.delta[1] * 30)
        self.zoom(factor, center_time)
        event.handled = True

    def zoom(self, factor, center_time):
        if self.max_vis_time == self.max_time and self.min_vis_time == self.min_time and factor > 1:
            return

        left_space = center_time - self.min_vis_time
        right_space = self.max_vis_time - center_time

        min_time = center_time - left_space * factor
        max_time = center_time + right_space * factor

        if max_time > self.max_time:
            max_time = self.max_time
        if min_time < self.min_time:
            min_time = self.min_time
        self.max_vis_time = max_time
        self.min_vis_time = min_time
        self.updateVisible()

    def pan(self, time_delta):
        if self.max_vis_time == self.max_time and time_delta > 0:
            return
        if self.min_vis_time == self.min_time and time_delta < 0:
            return
        min_time = self.min_vis_time + time_delta
        max_time = self.max_vis_time + time_delta
        if max_time > self.max_time:
            new_delta = time_delta - (max_time - self.max_time)
            min_time = self.min_vis_time + new_delta
            max_time = self.max_vis_time + new_delta
        if min_time < self.min_time:
            new_delta = time_delta - (min_time - self.min_time)
            min_time = self.min_vis_time + new_delta
            max_time = self.max_vis_time + new_delta
        self.min_vis_time = min_time
        self.max_vis_time = max_time
        self.updateVisible()

    def updateVisible(self):
        if self.annotations is None:
            return
        begin = time.time()
        min_time, max_time = self.min_vis_time, self.max_vis_time
        self.audioWidget.update_time_bounds(min_time, max_time)
        if self.signal is None or self.sr is None:
            self.audioWidget.update_signal(None)
            self.spectrumWidget.update_signal(None)
        else:
            min_samp = np.floor(min_time * self.sr)
            max_samp = np.ceil(max_time * self.sr)
            #print(max_time - min_time)
            if max_time - min_time > 5:
                factor = 100
            elif max_time - min_time > 1:
                factor = 50
            else:
                factor = 1

            sig = self.signal[min_samp:max_samp:factor]

            t = np.arange(sig.shape[0]) / (self.sr/factor) + min_time
            data = np.array((t, sig)).T
            #sp_begin = time.time()
            self.audioWidget.update_signal(data)
            #print('wave_time', time.time() - sp_begin)
            max_samp = np.ceil((max_time) * self.sr)
            #sp_begin = time.time()
            self.spectrumWidget.update_signal(self.signal[min_samp:max_samp])
            #print('spec_time', time.time() - sp_begin)
            self.updatePlayTime(self.min_vis_time)
            #if self.pitch is not None:
            #    self.spectrumWidget.update_pitch([[x[0] - min_time, x[1]] for x in self.pitch if x[0] > min_time - 1 and x[0] < max_time + 1])

            #sp_begin = time.time()
            #print('aud_time', time.time() - sp_begin)
        if self.annotations is None:
            self.audioWidget.update_annotations(None)
        else:
            #sp_begin = time.time()
            annos = [x for x in self.annotations if x.end > self.min_vis_time
                and x.begin < self.max_vis_time]
            self.audioWidget.update_annotations(annos)
            #print('anno_time', time.time() - sp_begin)
        #print(self.signal is None, self.annotations is None, time.time() - begin)

    def save_selected_boundary(self):
        key, ind = self.selected_boundary
        actual_index = int(ind / 4)
        index = 0
        selected_annotation = None
        for a in self.annotations:
            if a.end < self.min_vis_time:
                continue
            if isinstance(key, tuple):
                elements = getattr(a, key[0])
                for e in elements:
                    subs = getattr(e, key[1])
                    for s in subs:
                        if index == actual_index:
                            selected_annotation = s
                            break
                        index += 1
                    if selected_annotation is not None:
                        break
            elif key != a._type:
                elements = getattr(a, key)
                for e in elements:
                    if index == actual_index:
                        selected_annotation = e
                        break
                    index += 1
            elif index == actual_index:
                selected_annotation = a
            if selected_annotation is not None:
                break
        mod = ind % 4
        if mod == 0:
            selected_annotation.update_properties(begin = self.selected_time)
        else:
            selected_annotation.update_properties(end = self.selected_time)
        selected_annotation.save()

    def updateHierachy(self, hierarchy):
        self.hierarchy = hierarchy
        self.hierarchyWidget.updateHierachy(hierarchy)

    def updateHierarchyVisibility(self):
        pass

    def updateAnnotations(self, annotations):
        self.annotations = annotations
        if self.signal is None:
            self.min_time = 0
            if len(self.annotations):
                self.max_time = self.annotations[-1].end
            else:
                self.max_time = 30
            if self.min_vis_time is None:
                self.min_vis_time = 0
                self.max_vis_time = self.max_time

        self.updateVisible()

    def updatePitch(self, pitch):
        self.pitch = pitch
        self.updateVisible()

    def updateAudio(self, audio_file):
        if audio_file is not None:
            #kwargs = {'config':self.config, 'sound_file': audio_file, 'algorithm':'reaper'}
            #self.pitchWorker.setParams(kwargs)
            #self.pitchWorker.start()
            self.sr, self.signal = wavfile.read(audio_file.filepath)
            self.signal = self.signal / 32768

            if self.m_generator.isOpen():
                self.m_generator.close()
            self.m_generator.set_signal(self.signal)
            if self.min_time is None:
                self.min_time = 0
                self.max_time = len(self.signal) / self.sr
            if self.min_vis_time is None:
                self.min_vis_time = 0
                self.max_vis_time = self.max_time
            self.spectrumWidget.update_sampling_rate(self.sr)
            self.updateVisible()
        else:
            self.signal = None
            self.sr = None
            self.spectrumWidget.update_sampling_rate(self.sr)

    def changeView(self, begin, end):
        self.min_vis_time = begin
        self.max_vis_time = end
        #self.updateVisible()

    def clearDiscourse(self):
        self.audioWidget.update_hierarchy(self.hierarchy)
        self.min_time = None
        self.max_time = None
        self.min_selected_time = None
        self.max_selected_time = None
        self.audioWidget.update_selection(self.min_selected_time, self.max_selected_time)
        #self.audioWidget.clear()

class QueryForm(QtWidgets.QWidget):
    finishedRunning = QtCore.pyqtSignal(object)
    def __init__(self):
        super(QueryForm, self).__init__()
        self.config = None
        headerLayout = QtWidgets.QHBoxLayout()

        self.linguisticSelect = QtWidgets.QComboBox()
        self.executeButton = QtWidgets.QPushButton('Run query')
        self.executeButton.clicked.connect(self.runQuery)
        self.executeButton.setDisabled(True)
        headerLayout.addWidget(QtWidgets.QLabel('Linguistic type'))

        headerLayout.addWidget(self.linguisticSelect)
        headerLayout.addWidget(self.executeButton)

        mainLayout = QtWidgets.QVBoxLayout()
        if False:
            mainLayout.addLayout(headerLayout)

        phon4Layout = QtWidgets.QHBoxLayout()

        self.lab1Button = QtWidgets.QPushButton('Search for Lab 1 stops')
        self.lab1Button.setDisabled(True)
        self.lab1Button.clicked.connect(self.lab1Query)
        self.exportButton = QtWidgets.QPushButton('Export Lab 1 stops')
        self.exportButton.clicked.connect(self.runExportQuery)
        self.exportButton.setDisabled(True)

        phon4Layout.addWidget(self.lab1Button)
        phon4Layout.addWidget(self.exportButton)

        mainLayout.addLayout(phon4Layout)

        self.setLayout(mainLayout)

        self.worker = QueryWorker()
        self.worker.dataReady.connect(self.setResults)

        self.lab1Worker = Lab1QueryWorker()
        self.lab1Worker.dataReady.connect(self.setResults)
        self.lab1Worker.errorEncountered.connect(self.showError)

        self.exportWorker = ExportQueryWorker()
        self.exportWorker.errorEncountered.connect(self.showError)

    def showError(self, e):
        reply = DetailedMessageBox()
        reply.setDetailedText(str(e))
        ret = reply.exec_()

    def lab1Query(self):
        if self.config is None:
            return
        kwargs = {}
        kwargs['config'] = self.config
        self.lab1Worker.setParams(kwargs)
        self.lab1Worker.start()

    def runExportQuery(self):
        if self.config is None:
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export data", filter = "CSV (*.txt  *.csv)")

        if not path:
            return
        kwargs = {}
        kwargs['config'] = self.config
        kwargs['path'] = path
        self.exportWorker.setParams(kwargs)
        self.exportWorker.start()

    def runQuery(self):
        if self.config is None:
            return
        kwargs = {}
        kwargs['annotation_type'] = self.linguisticSelect.currentText()
        kwargs['config'] = self.config
        self.worker.setParams(kwargs)
        self.worker.start()

    def updateConfig(self, config):
        self.config = config
        self.linguisticSelect.clear()
        if self.config is None or self.config.corpus_name == '':
            self.executeButton.setDisabled(True)
            self.lab1Button.setDisabled(True)
            self.exportButton.setDisabled(True)
            return
        self.executeButton.setDisabled(False)
        self.lab1Button.setDisabled(False)
        self.exportButton.setDisabled(False)
        #with CorpusContext(config) as c:
        #    for a in c.annotation_types:
        #        self.linguisticSelect.addItem(a)

    def setResults(self, results):
        self.finishedRunning.emit(results)

class QueryResults(QtWidgets.QWidget):
    def __init__(self, results):
        super(QueryResults, self).__init__()

        self.query = results[0]

        self.resultsModel = QueryResultsModel(results[1])

        self.tableWidget = ResultsView()

        self.proxyModel = ProxyModel()
        self.proxyModel.setSourceModel(self.resultsModel)
        self.tableWidget.setModel(self.proxyModel)

        layout = QtWidgets.QVBoxLayout()

        layout.addWidget(self.tableWidget)

        self.setLayout(layout)

class QueryWidget(QtWidgets.QWidget):
    viewRequested = QtCore.pyqtSignal(str, float, float)
    def __init__(self):
        super(QueryWidget, self).__init__()
        self.config = None
        self.tabs = QtWidgets.QTabWidget()
        self.currentIndex = 1
        self.queryForm = QueryForm()
        self.queryForm.finishedRunning.connect(self.updateResults)

        self.tabs.addTab(self.queryForm, 'New query')

        layout = QtWidgets.QVBoxLayout()

        layout.addWidget(self.tabs)

        self.setLayout(layout)

    def updateConfig(self, config):
        self.config = config

        self.queryForm.updateConfig(config)

    def updateResults(self, results):
        name = 'Query {}'.format(self.currentIndex)
        self.currentIndex += 1
        widget = QueryResults(results)
        widget.tableWidget.viewRequested.connect(self.viewRequested.emit)
        self.tabs.addTab(widget, name)

    def markAnnotated(self, value):
        w = self.tabs.currentWidget()
        if not isinstance(w, QueryResults):
            return
        w.tableWidget.markAnnotated(value)

    def requestNext(self):
        w = self.tabs.currentWidget()
        if not isinstance(w, QueryResults):
            return
        w.tableWidget.selectNext()

    def requestPrevious(self):
        w = self.tabs.currentWidget()
        if not isinstance(w, QueryResults):
            return
        w.tableWidget.selectPrevious()

class HelpWidget(QtWidgets.QWidget):
    def __init__(self):
        super(HelpWidget, self).__init__()

        layout = QtWidgets.QHBoxLayout()

        layout.addWidget(QtWidgets.QLabel('Placeholder help, kinda useless, oh well'))
        self.setLayout(layout)

class DiscourseWidget(QtWidgets.QWidget):
    discourseChanged = QtCore.pyqtSignal(str)
    viewRequested = QtCore.pyqtSignal(object, object)
    def __init__(self):
        super(DiscourseWidget, self).__init__()

        self.config = None

        layout = QtWidgets.QHBoxLayout()

        self.discourseList = QtWidgets.QListWidget()
        self.discourseList.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.discourseList.currentItemChanged.connect(self.changeDiscourse)

        layout.addWidget(self.discourseList)

        self.setLayout(layout)

    def changeDiscourse(self):
        item = self.discourseList.currentItem()
        if item is None:
            discourse = None
        else:
            discourse = item.text()
        self.discourseChanged.emit(discourse)
        self.viewRequested.emit(None, None)

    def changeView(self, discourse, begin, end):
        self.viewRequested.emit(begin, end)
        for i in range(self.discourseList.count()):
            item = self.discourseList.item(i)
            if item.text() == discourse:
                index = self.discourseList.model().index(i, 0)
                self.discourseList.selectionModel().select(index,
                                QtCore.QItemSelectionModel.ClearAndSelect|QtCore.QItemSelectionModel.Rows)

                break
        self.discourseChanged.emit(discourse)


    def updateConfig(self, config):
        self.config = config
        self.discourseList.clear()
        if self.config is None or self.config.corpus_name == '':
            return
        with CorpusContext(self.config) as c:
            for d in sorted(c.discourses):
                self.discourseList.addItem(d)

class DetailedMessageBox(QtWidgets.QMessageBox):
    # Adapted from http://stackoverflow.com/questions/2655354/how-to-allow-resizing-of-qmessagebox-in-pyqt4
    def __init__(self, *args, **kwargs):
        super(DetailedMessageBox, self).__init__(*args, **kwargs)
        self.setWindowTitle('Error encountered')
        self.setIcon(QtWidgets.QMessageBox.Critical)
        self.setStandardButtons(QtWidgets.QMessageBox.Close)
        self.setText("Something went wrong!")
        self.setInformativeText("Please copy the text below and send to Michael.")

        self.setFixedWidth(200)

    def resizeEvent(self, event):
        result = super(DetailedMessageBox, self).resizeEvent(event)
        details_box = self.findChild(QtWidgets.QTextEdit)
        if details_box is not None:
            details_box.setFixedHeight(details_box.sizeHint().height())
        return result

class ViewWidget(QtWidgets.QWidget):
    changingDiscourse = QtCore.pyqtSignal()
    connectionIssues = QtCore.pyqtSignal()
    def __init__(self, parent = None):
        super(ViewWidget, self).__init__(parent)

        layout = QtWidgets.QHBoxLayout()

        tabs = QtWidgets.QTabWidget()

        self.discourseWidget = SelectableAudioWidget()

        self.summaryWidget = SCTSummaryWidget(self)

        self.dataTabs = QtWidgets.QTabWidget()

        self.phoneList = DataListWidget(self.summaryWidget, 'p')
        self.phoneList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.wordList = DataListWidget(self.summaryWidget, 'w')
        self.wordList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.dataTabs.addTab(self.phoneList, 'Phones')
        self.dataTabs.addTab(self.wordList, 'Words')

        summaryTab = CollapsibleWidgetPair(QtCore.Qt.Horizontal, self.summaryWidget.native, self.dataTabs)

        tabs.addTab(self.discourseWidget, 'Discourse')
        tabs.addTab(summaryTab, 'Summary')

        layout.addWidget(tabs, 1)

        self.setLayout(layout)

        self.audioWorker = DiscourseAudioWorker()
        self.audioWorker.dataReady.connect(self.discourseWidget.updateAudio)
        self.audioWorker.errorEncountered.connect(self.showError)

        self.worker = DiscourseQueryWorker()
        self.worker.dataReady.connect(self.discourseWidget.updateAnnotations)
        self.changingDiscourse.connect(self.worker.stop)
        self.changingDiscourse.connect(self.discourseWidget.clearDiscourse)
        self.worker.errorEncountered.connect(self.showError)
        self.worker.connectionIssues.connect(self.connectionIssues.emit)

    def showError(self, e):
        reply = DetailedMessageBox()
        reply.setDetailedText(str(e))
        ret = reply.exec_()

    def changeDiscourse(self, discourse):
        if discourse:
            self.changingDiscourse.emit()
            kwargs = {}

            kwargs['config'] = self.config
            kwargs['discourse'] = discourse

            self.audioWorker.setParams(kwargs)
            self.audioWorker.start()
            kwargs = {}
            with CorpusContext(self.config) as c:
                self.discourseWidget.updateHierachy(c.hierarchy)
                kwargs['seg_type'] = c.hierarchy.lowest
                kwargs['word_type'] = c.hierarchy.highest

            kwargs['config'] = self.config
            kwargs['discourse'] = discourse

            self.worker.setParams(kwargs)
            self.worker.start()

    def updateConfig(self, config):
        self.config = config
        self.changingDiscourse.emit()
        self.discourseWidget.config = config
        if self.config is None:
            return
        with CorpusContext(self.config) as c:
            self.discourseWidget.hierarchy = c.hierarchy


class CollapsibleWidgetPair(QtWidgets.QSplitter):
    def __init__(self, orientation, widgetOne, widgetTwo, collapsible = 1, parent = None):
        super(CollapsibleWidgetPair, self).__init__(orientation, parent)
        self.collapsible = collapsible
        self.addWidget(widgetOne)
        self.addWidget(widgetTwo)
        self.setCollapsible(0, False)
        self.setCollapsible(1, False)

        if self.orientation() == QtCore.Qt.Horizontal:
            if self.collapsible == 1:
                self.uncollapsed_arrow = QtCore.Qt.RightArrow
                self.collapsed_arrow = QtCore.Qt.LeftArrow
            else:
                self.uncollapsed_arrow = QtCore.Qt.LeftArrow
                self.collapsed_arrow = QtCore.Qt.RightArrow
        else:
            if self.collapsible == 1:
                self.uncollapsed_arrow = QtCore.Qt.DownArrow
                self.collapsed_arrow = QtCore.Qt.UpArrow
            else:
                self.uncollapsed_arrow = QtCore.Qt.UpArrow
                self.collapsed_arrow = QtCore.Qt.DownArrow

        #size_unit = get_system_font_height()
        #handle = self.handle(1)
        #self.button = QtWidgets.QToolButton(handle)
        #if self.orientation() == QtCore.Qt.Horizontal:
        #    self.button.setMinimumHeight(8 * size_unit)
        #    layout = QtWidgets.QVBoxLayout()
        #    self.button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        #else:
        #    self.button.setMinimumWidth(8 * size_unit)
        #    layout = QtWidgets.QHBoxLayout()
        #    self.button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)

        #self.button.setArrowType(self.uncollapsed_arrow)
        #layout.setContentsMargins(0, 0, 0, 0)
        #self.button.clicked.connect(self.onCollapse)
        #layout.addWidget(self.button)
        #handle.setLayout(layout)
        #self.setHandleWidth(size_unit)

    #def onCollapse(self):
    #    if self.collapsible == 1:
    #        collapsed_size = [1, 0]
    #        uncollapsed_size = [1000,1]
    #    else:
    #        collapsed_size = [0, 1]
    #        uncollapsed_size = [1, 1000]
    #    if self.sizes()[self.collapsible]:
    #        self.setSizes(collapsed_size)
    #        self.button.setArrowType(self.collapsed_arrow)
    #    else:
    #        self.setSizes(uncollapsed_size)
    #        self.button.setArrowType(self.uncollapsed_arrow)


class DataListWidget(QtWidgets.QListWidget):
    def __init__(self, plot, plot_type, parent = None):
        super(DataListWidget, self).__init__(parent)
        self.plot = plot
        self.plot_type = plot_type
        self.itemSelectionChanged.connect(self.update_plot)

    def selectAll(self):
        for i in range(self.count()): self.item(i).setSelected(True)

    def update_plot(self):
        labels = [i.text() for i in self.selectedItems()]
        self.plot.update_data(labels, self.plot_type)
