import numpy as np
from scipy.io import wavfile
from scipy.signal import lfilter
import time

from PyQt5 import QtGui, QtCore, QtWidgets, QtMultimedia

from .audio import AudioOutput, Generator

from .annotation import SubannotationDialog, NoteDialog

from .structure import HierarchyWidget

from ..workers import PitchGeneratorWorker, FormantsGeneratorWorker

from ..plot import AnnotationWidget, SpectralWidget

class SelectableAudioWidget(QtWidgets.QWidget):
    discourseHelpBroadcast = QtCore.pyqtSignal()
    previousRequested = QtCore.pyqtSignal()
    nextRequested = QtCore.pyqtSignal()
    markedAsAnnotated = QtCore.pyqtSignal(bool)
    selectionChanged = QtCore.pyqtSignal(object)
    acousticsSelected = QtCore.pyqtSignal(object)
    def __init__(self, parent = None):
        super(SelectableAudioWidget, self).__init__(parent)
        #self.setMinimumHeight(600)
        self.signal = None
        self.preemph_signal = None
        self.sr = None
        self.pitch = None
        self.formants = None
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
        self.audioQtWidget = self.audioWidget.native
        self.audioQtWidget.setFocusPolicy(QtCore.Qt.NoFocus)
        toplayout.addWidget(self.audioQtWidget)

        layout.addLayout(toplayout)

        self.spectrumWidget = SpectralWidget()
        self.spectrumWidget.events.mouse_press.connect(self.on_mouse_press)
        self.spectrumWidget.events.mouse_release.connect(self.on_mouse_release)
        self.spectrumWidget.events.mouse_move.connect(self.on_mouse_move)
        self.spectrumWidget.events.mouse_wheel.connect(self.on_mouse_wheel)
        w = self.spectrumWidget.native
        w.setFocusPolicy(QtCore.Qt.NoFocus)
        bottomlayout.addWidget(w)

        self.helpButton = QtWidgets.QPushButton()
        self.helpButton.setText("help")
        self.helpButton.clicked.connect(self.discourseHelpBroadcast.emit)
        self.helpButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)
      
        vhelpLayout = QtWidgets.QHBoxLayout()
        vhelpLayout.addStretch(1)
        vhelpLayout.addWidget(self.helpButton)      
        
        helpLayout = QtWidgets.QVBoxLayout()
        helpLayout.addStretch(1)
        helpLayout.addLayout(vhelpLayout)        

        layout.addLayout(bottomlayout)

        

        mainlayout = QtWidgets.QHBoxLayout()
        mainlayout.addLayout(layout)
        mainlayout.setStretchFactor(helpLayout, 2)
        mainlayout.addLayout(helpLayout)

        self.hierarchyWidget = HierarchyWidget()
        self.hierarchyWidget.toggleSpectrogram.connect(self.spectrumWidget.toggle_spectrogram)
        self.hierarchyWidget.togglePitch.connect(self.spectrumWidget.toggle_pitch)
        self.hierarchyWidget.toggleFormants.connect(self.spectrumWidget.toggle_formants)

        mainlayout.addWidget(self.hierarchyWidget)

        self.setLayout(mainlayout)

        self.pitchWorker = PitchGeneratorWorker()
        self.pitchWorker.dataReady.connect(self.updatePitch)

        self.formantsWorker = FormantsGeneratorWorker()
        self.formantsWorker.dataReady.connect(self.updateFormants)

        self.m_audioOutput = AudioOutput()
        self.m_audioOutput.notify.connect(self.notified)
        self.m_audioOutput.stateChanged.connect(self.handleAudioState)

        self.m_generator = Generator(self.m_audioOutput.m_format, self)

    def handleAudioState(self, state):
        if state == QtMultimedia.QAudio.StoppedState:
            if self.min_selected_time is None:
                min_time = self.min_vis_time
            else:
                min_time = self.min_selected_time
            self.updatePlayTime(min_time)

    def updatePlayTime(self, time):
        if time is None:
            pos = None
        else:
            pos = self.audioWidget.transform_time_to_pos(time)
        self.audioWidget.update_play_time(time)
        self.spectrumWidget.update_play_time(pos)

    def notified(self):
        min_time = self.m_generator.min_time
        if min_time is None:
            return
        time = self.m_audioOutput.processedUSecs() / 1000000
        time += min_time
        self.updatePlayTime(time)

    def focusNextPrevChild(self, next_):
        return False

    def keyPressEvent(self, event):
        """
        Bootstrap the Qt keypress event items
        """
        if event.key() == QtCore.Qt.Key_Delete or (event.key() == QtCore.Qt.Key_Backspace and event.modifiers() & QtCore.Qt.AltModifier):
            if self.selected_annotation is not None:
                if self.selected_annotation._type not in self.hierarchy:
                    self.selected_annotation._annotation.delete_subannotation(self.selected_annotation)

                    self.selected_annotation = None
                    self.selectionChanged.emit(None)
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
                    self.selectionChanged.emit(self.selected_annotation)
        elif event.key() == QtCore.Qt.Key_Tab:
            if self.signal is None:
                return
            if self.m_audioOutput.state() == QtMultimedia.QAudio.StoppedState or \
                self.m_audioOutput.state() == QtMultimedia.QAudio.IdleState:
                if self.min_selected_time is None:
                    min_time = self.min_vis_time
                    max_time = self.max_vis_time
                else:
                    min_time = self.min_selected_time
                    max_time = self.max_selected_time
                #print(min_time, max_time, max_time - min_time)
                self.m_generator.generateData(min_time, max_time)
                self.m_audioOutput.reset()
                if self.m_audioOutput.state() == QtMultimedia.QAudio.StoppedState:
                    self.m_audioOutput.start(self.m_generator)
                #print(self.m_audioOutput.error(), self.m_audioOutput.state())
                #print(self.m_generator.pos())

            elif self.m_audioOutput.state() == QtMultimedia.QAudio.ActiveState:
                self.m_audioOutput.suspend()
            elif self.m_audioOutput.state() == QtMultimedia.QAudio.SuspendedState:
                self.m_audioOutput.resume()
        elif event.key() == QtCore.Qt.Key_Left:
            print(event.modifiers())
            if event.modifiers() & QtCore.Qt.ShiftModifier:
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
        elif self.selected_annotation is not None and \
                not event.modifiers() & (QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier):
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
            self.selectionChanged.emit(self.selected_annotation)
            self.updateVisible()
        elif self.selected_annotation is not None:
            if self.selected_annotation._type == self.hierarchy.lowest and\
                event.modifiers() == QtCore.Qt.ControlModifier and \
                event.key() in [QtCore.Qt.Key_C, QtCore.Qt.Key_B, QtCore.Qt.Key_V]:
                if event.key() == QtCore.Qt.Key_C:
                    type = 'closure'
                elif event.key() == QtCore.Qt.Key_B:
                    type = 'burst'
                elif event.key() == QtCore.Qt.Key_V:
                    type = 'voicing'
                self.selected_annotation.add_subannotation(type,
                        begin = self.selected_annotation.begin,
                        end = self.selected_annotation.end)
                self.selected_annotation.save()
                self.updateVisible()
        else:
            print(event.key())

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

    def get_acoustics(self, time):
        acoustics = {}
        if self.pitch is None:
            acoustics['F0'] = None
        else:
            for i,p in enumerate(self.pitch):
                if p[0] > time:
                    if i != 0:
                        prev_time = self.pitch[i-1][0]
                        prev_pitch = self.pitch[i-1][1]
                        dur = p[0] - prev_time
                        cur_time = time - prev_time
                        percent = cur_time / dur
                        acoustics['F0'] = prev_pitch * percent + p[1] * (1 - percent)
                    else:
                        acoustics['F0'] = p[1]
                    break
            else:
                acoustics['F0'] = None
        if self.formants is None:
            acoustics['F1'] = None
            acoustics['F2'] = None
            acoustics['F3'] = None
        else:
            for k,v in self.formants.items():
                for i,f in enumerate(v):
                    if f[0] > time:
                        if i != 0:
                            prev_time = v[i-1][0]
                            prev_formant = v[i-1][1]
                            dur = f[0] - prev_time
                            cur_time = time - prev_time
                            percent = cur_time / dur
                            acoustics[k] = prev_formant * percent + f[1] * (1 - percent)
                        else:
                            acoustics[k] = f[1]
                        break
        self.acousticsSelected.emit(acoustics)

    def on_mouse_press(self, event):
        """
        Mouse button press event
        """
        self.setFocus(True)
        self.selected_annotation = None
        self.selected_boundary = None
        #self.selectionChanged.emit(None)

        if event.handled:
            return
        if event.button == 1 and not event.native.modifiers() & QtCore.Qt.ShiftModifier:
            self.min_selected_time = None
            self.max_selected_time = None
            self.audioWidget.update_selection(self.min_selected_time, self.max_selected_time)
            time = self.audioWidget.transform_pos_to_time(event.pos)
            self.get_acoustics(time)
            selection = self.audioWidget.check_selection(event)
            if selection is not None:
                self.selected_boundary = selection
                self.selected_time = time
            else:
                self.audioWidget.update_play_time(time)
                self.spectrumWidget.update_play_time(event.pos[0])

        elif event.button == 1:
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
                self.selectionChanged.emit(None)
                return
            self.selected_annotation = annotation
            self.selectionChanged.emit(annotation)
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

        time = self.audioWidget.transform_pos_to_time(event.pos)
        key = self.audioWidget.get_key(event.pos)
        if key is None:
            annotation = None
        else:
            annotation = self.find_annotation(key, time)
        if event.button == 1 and is_single_click and \
                    event.native.modifiers() & QtCore.Qt.ShiftModifier and \
            annotation is not None:
            self.selected_annotation = annotation
            self.selectionChanged.emit(annotation)
            self.min_selected_time = annotation.begin
            self.max_selected_time = annotation.end
            self.audioWidget.update_selection(self.min_selected_time, self.max_selected_time)
            if self.signal is None:
                return
            self.updatePlayTime(self.min_selected_time)
        elif event.button == 1 and is_single_click and not event.native.modifiers() & QtCore.Qt.ShiftModifier and \
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
        elif event.button == 2 and annotation is not None:
            key = self.audioWidget.get_key(event.pos)

            update = False
            self.selected_annotation = annotation
            self.selectionChanged.emit(annotation)
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
                    #if type not in annotation._subannotations or len(annotation._subannotations[type]) == 0:
                    annotation.add_subannotation(type,
                            begin = annotation.begin, end = annotation.end)
                    update = True
            elif action == note_action:
                dialog = NoteDialog(annotation)
                if dialog.exec_():
                    annotation.update_properties(**dialog.value())
                    update = True
            elif action == check_annotated_action:
                if annotation.checked:
                    annotation.update_properties(checked = False)
                else:
                    annotation.update_properties(checked = True)
                update = True
            elif action == mark_absent_action:
                annotation._annotation.delete_subannotation(annotation)
                update = True
            if update:
                annotation.save()
                self.updateVisible()
                self.selectionChanged.emit(annotation)
            menu.deleteLater()

    def on_mouse_move(self, event):
        snap = True
        if event.button == 1 and event.is_dragging and event.native.modifiers() & QtCore.Qt.ShiftModifier:
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
                #self.updatePlayTime(self.min_vis_time)
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
        if self.max_vis_time is None:
            return
        if self.max_time is None:
            return
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
        if self.max_vis_time is None:
            return
        if self.max_time is None:
            return
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
        self.audioWidget.update_time_bounds(self.min_vis_time, self.max_vis_time)
        self.drawSignal()
        self.drawAnnotations()
        self.drawFormants()
        self.drawPitch()

    def save_selected_boundary(self):
        key, ind = self.selected_boundary
        actual_index = int(ind / 6)
        index = 0
        selected_annotation = None
        for a in self.annotations:
            if a.end < self.min_vis_time:
                continue
            if isinstance(key, tuple):
                elements = getattr(a, key[0])
                for e in elements:
                    if e.end < self.min_vis_time:
                        continue
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
        mod = ind % 6
        if self.selected_time > self.max_vis_time:
            self.selected_time = self.max_vis_time
        elif self.selected_time < self.min_vis_time:
            self.selected_time = self.min_vis_time
        if mod == 0:
            selected_annotation.update_properties(begin = self.selected_time)
        else:
            selected_annotation.update_properties(end = self.selected_time)
        self.selectionChanged.emit(selected_annotation)
        selected_annotation.save()

    def updateHierachy(self, hierarchy):
        self.hierarchy = hierarchy
        self.hierarchyWidget.hierarchy = hierarchy
        self.audioWidget.update_hierarchy(self.hierarchy)

    def drawSignal(self):
        if self.signal is None or self.sr is None:
            self.audioWidget.update_signal(None)
            self.spectrumWidget.update_signal(None)
        else:
            min_samp = np.floor(self.min_vis_time * self.sr)
            max_samp = np.ceil(self.max_vis_time * self.sr)
            desired = self.audioQtWidget.width() * 3
            actual = max_samp - min_samp
            factor = int(actual/desired)
            if factor == 0:
                factor = 1

            sig = self.signal[min_samp:max_samp:factor]

            t = np.arange(sig.shape[0]) / (self.sr/factor) + self.min_vis_time
            data = np.array((t, sig)).T
            #sp_begin = time.time()
            self.audioWidget.update_signal(data)
            #print('wave_time', time.time() - sp_begin)
            #sp_begin = time.time()
            self.spectrumWidget.update_signal(self.preemph_signal[min_samp:max_samp])
            #print('spec_time', time.time() - sp_begin)
            self.updatePlayTime(self.min_vis_time)
            #sp_begin = time.time()
            #print('aud_time', time.time() - sp_begin)

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
        min_time, max_time = self.min_vis_time, self.max_vis_time
        self.audioWidget.update_time_bounds(min_time, max_time)
        self.drawAnnotations()

    def drawAnnotations(self):
        if self.annotations is None:
            self.audioWidget.update_annotations(None)
        else:
            annos = [x for x in self.annotations if x.end > self.min_vis_time
                and x.begin < self.max_vis_time]
            self.audioWidget.update_annotations(annos)

    def updatePitch(self, pitch):
        self.pitch = pitch
        self.drawPitch()

    def drawPitch(self):
        if self.pitch is not None:
            pitch = [[x[0] - self.min_vis_time, x[1]]
                        for x in self.pitch
                        if x[0] > self.min_vis_time - 0.1
                        and x[0] < self.max_vis_time + 0.1]
            self.spectrumWidget.update_pitch(pitch)
        else:
            self.spectrumWidget.update_pitch([])

    def updateFormants(self, formants):
        self.formants = formants
        self.drawFormants()

    def drawFormants(self):
        if self.formants is not None:
            self.spectrumWidget.update_formants({'F1':[[x[0] - self.min_vis_time, x[1]] for x in self.formants['F1'] if x[0] > self.min_vis_time - 0.1 and x[0] < self.max_vis_time + 0.1],
                                    'F2':[[x[0] - self.min_vis_time, x[1]] for x in self.formants['F2'] if x[0] > self.min_vis_time - 0.1 and x[0] < self.max_vis_time + 0.1],
                                    'F3':[[x[0] - self.min_vis_time, x[1]] for x in self.formants['F3'] if x[0] > self.min_vis_time - 0.1 and x[0] < self.max_vis_time + 0.1],})
        else:
            self.spectrumWidget.update_formants({})

    def updateAudio(self, audio_file):
        if audio_file is not None:
            alpha = 0.95
            kwargs = {'config':self.config, 'sound_file': audio_file, 'algorithm':'reaper'}
            self.pitch = None
            self.pitchWorker.setParams(kwargs)
            self.pitchWorker.start()
            kwargs = {'config':self.config, 'sound_file': audio_file, 'algorithm':'acousticsim'}
            self.formants = None
            self.formantsWorker.setParams(kwargs)
            self.formantsWorker.start()
            self.sr, self.signal = wavfile.read(audio_file.filepath)
            self.signal = self.signal / 32768
            self.preemph_signal = lfilter([1., -alpha], 1, self.signal)

            if self.m_generator.isOpen():
                self.m_generator.close()
            self.m_generator.set_signal(self.signal)
            if self.min_time is None:
                self.min_time = 0
                self.max_time = len(self.signal) / self.sr
            if self.min_vis_time is None:
                self.min_vis_time = 0
                self.max_vis_time = self.max_time
            if self.max_vis_time - self.min_vis_time > 30:
                self.max_vis_time = self.min_vis_time + 30
            self.spectrumWidget.update_sampling_rate(self.sr)
            self.audioWidget.update_time_bounds(self.min_vis_time, self.max_vis_time)
            self.drawSignal()
        else:
            self.signal = None
            self.sr = None
            self.spectrumWidget.update_sampling_rate(self.sr)

    def changeView(self, begin, end):
        self.min_vis_time = begin
        self.max_vis_time = end
        self.selectionChanged.emit(None)
        #self.updateVisible()

    def clearDiscourse(self):
        self.min_time = None
        self.max_time = None
        self.min_selected_time = None
        self.max_selected_time = None
        self.pitch = None
        self.formants = None
        self.signal = None
        self.drawPitch()
        self.drawFormants()
        self.drawSignal()
        self.audioWidget.update_selection(self.min_selected_time, self.max_selected_time)
        #self.audioWidget.clear()
