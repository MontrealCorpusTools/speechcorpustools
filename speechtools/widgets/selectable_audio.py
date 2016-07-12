import numpy as np
import librosa
import time

from PyQt5 import QtGui, QtCore, QtWidgets, QtMultimedia

from .base import DetailedMessageBox

from .audio import MediaPlayer

from .annotation import SubannotationDialog, NoteDialog

from .structure import HierarchyWidget

from ..plot import AnnotationWidget, SpectralWidget

from ..workers import PrecedingCacheWorker, FollowingCacheWorker, AudioCacheWorker

class SelectableAudioWidget(QtWidgets.QWidget):
    discourseHelpBroadcast = QtCore.pyqtSignal()
    previousRequested = QtCore.pyqtSignal()
    nextRequested = QtCore.pyqtSignal()
    markedAsAnnotated = QtCore.pyqtSignal(bool)
    selectionChanged = QtCore.pyqtSignal(object)
    acousticsSelected = QtCore.pyqtSignal(object)
    def __init__(self, parent = None):
        super(SelectableAudioWidget, self).__init__(parent)
        self.discourse_model = None
        self.hierarchy = None
        self.config = None

        self.min_selected_time = None
        self.max_selected_time = None
        self.channel = 0
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
        layout.addLayout(bottomlayout)

        mainlayout = QtWidgets.QHBoxLayout()
        mainlayout.addLayout(layout)

        self.hierarchyWidget = HierarchyWidget()
        self.hierarchyWidget.toggleSpectrogram.connect(self.spectrumWidget.toggle_spectrogram)
        self.hierarchyWidget.togglePitch.connect(self.spectrumWidget.toggle_pitch)
        self.hierarchyWidget.toggleFormants.connect(self.spectrumWidget.toggle_formants)
        self.hierarchyWidget.channelChanged.connect(self.updateChannel)
        self.hierarchyWidget.discourseHelpBroadcast.connect(self.discourseHelpBroadcast.emit)

        mainlayout.addWidget(self.hierarchyWidget)

        self.setLayout(mainlayout)

        self.m_audioOutput = MediaPlayer()
        self.m_audioOutput.error.connect(self.showError)
        self.m_audioOutput.positionChanged.connect(self.notified)
        self.m_audioOutput.stateChanged.connect(self.handleAudioState)

        self.view_begin = None
        self.view_end = None
        self.audio = None
        self.cache_window = 5

        self.precedingCacheWorker = PrecedingCacheWorker()
        self.precedingCacheWorker.dataReady.connect(self.addPreceding)
        self.precedingCacheWorker.errorEncountered.connect(self.showError)
        self.followingCacheWorker = FollowingCacheWorker()
        self.followingCacheWorker.dataReady.connect(self.addFollowing)
        self.followingCacheWorker.errorEncountered.connect(self.showError)

        self.audioCacheWorker = AudioCacheWorker()
        self.audioCacheWorker.dataReady.connect(self.updateAudio)
        self.audioCacheWorker.errorEncountered.connect(self.showError)

    def showError(self, e):
        reply = DetailedMessageBox()
        reply.setDetailedText(str(e))
        ret = reply.exec_()

    def updateAudio(self, audio):
        self.audio = audio
        if self.audio is not None:
            p = QtCore.QUrl.fromLocalFile(self.audio.path)
            self.m_audioOutput.setMedia(QtMultimedia.QMediaContent(p))
            self.spectrumWidget.update_sampling_rate(self.audio.sr)
            self.hierarchyWidget.setNumChannels(self.audio.num_channels)

    def cachePreceding(self):
        if self.audio is not None:
            if self.audio.cached_begin != 0 and self.view_begin < self.audio.cached_begin + self.cache_window:
                self.audioCacheWorker.setParams({'sound_file':self.discourse_model.sound_file, 'begin': self.view_begin, 'end': self.view_end})
                self.audioCacheWorker.start()
        if not self.precedingCacheWorker.finished:
            return
        if not self.discourse_model.cached_to_begin and self.view_begin < self.discourse_model.cached_begin + self.cache_window:
            print('beginning!')
            kwargs = {'config': self.config,
                        'begin': self.discourse_model.cached_begin - 2 * self.cache_window,
                        'end': self.discourse_model.cached_begin,
                        'discourse': self.discourse_model.name}
            self.precedingCacheWorker.setParams(kwargs)
            self.precedingCacheWorker.start()


    def cacheFollowing(self):
        if self.audio is not None:
            if self.audio.cached_end != self.audio.duration and self.view_end > self.audio.cached_end - self.cache_window:
                self.audioCacheWorker.setParams({'sound_file':self.discourse_model.sound_file, 'begin': self.view_begin, 'end': self.view_end})
                self.audioCacheWorker.start()
        if not self.followingCacheWorker.finished:
            return
        if not self.discourse_model.cached_to_end and self.view_end > self.discourse_model.cached_end - self.cache_window:
            end = self.discourse_model.cached_end + 2 * self.cache_window
            if self.view_end > end:
                end = self.view_end + 2 * self.cache_window
            kwargs = {'config': self.config,
                        'begin': self.discourse_model.cached_end,
                        'end': end,
                        'discourse': self.discourse_model.name}
            self.followingCacheWorker.setParams(kwargs)
            self.followingCacheWorker.start()

    def addPreceding(self, results):
        if self.discourse_model is None:
            return
        self.discourse_model.add_preceding(results)
        self.updateVisible()

    def addFollowing(self, results):
        if self.discourse_model is None:
            return
        self.discourse_model.add_following(results)
        self.updateVisible()

    def updateChannel(self, channel):
        self.channel = channel
        self.updateVisible()

    def handleAudioState(self, state):
        if state == QtMultimedia.QAudio.StoppedState:
            if self.min_selected_time is None:
                min_time = self.view_begin
            else:
                min_time = self.min_selected_time
            self.updatePlayTime(min_time)
            self.m_audioOutput.setPosition(0)

    def updatePlayTime(self, time):
        if time is None:
            pos = None
        else:
            pos = self.audioWidget.transform_time_to_pos(time)
        self.audioWidget.update_play_time(time)
        self.spectrumWidget.update_play_time(pos)

    def notified(self, position):
        time = position / 1000
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
            if self.audio is None:
                return
            if self.m_audioOutput.state() == QtMultimedia.QMediaPlayer.StoppedState or \
                self.m_audioOutput.state() == QtMultimedia.QMediaPlayer.PausedState:
                if self.min_selected_time is None:
                    min_time = self.view_begin
                    max_time = self.view_end
                else:
                    min_time = self.min_selected_time
                    max_time = self.max_selected_time
                self.m_audioOutput.setMinTime(min_time)
                self.m_audioOutput.setMaxTime(max_time)
                if self.m_audioOutput.state() == QtMultimedia.QMediaPlayer.StoppedState:
                    self.m_audioOutput.play()
            elif self.m_audioOutput.state() == QtMultimedia.QMediaPlayer.PlayingState:
                self.m_audioOutput.pause()
            elif self.m_audioOutput.state() == QtMultimedia.QMediaPlayer.PausedState:
                self.m_audioOutput.play()
        elif event.key() == QtCore.Qt.Key_Left:
            print(event.modifiers())
            if event.modifiers() & QtCore.Qt.ShiftModifier:
                print('shift left')
            else:
                vis = self.view_end - self.view_begin
                to_pan = 0.1 * vis * -1
                self.pan(to_pan)
        elif event.key() == QtCore.Qt.Key_Right:
            if event.modifiers() == QtCore.Qt.ShiftModifier:
                print('shift right')
            else:
                vis = self.view_end - self.view_begin
                to_pan = 0.1 * vis
                self.pan(to_pan)
        elif event.key() == QtCore.Qt.Key_Up:
            vis = self.view_end - self.view_begin
            center_time = self.view_begin + vis / 2
            factor = (1 + 0.007) ** (-30)
            self.zoom(factor, center_time)
        elif event.key() == QtCore.Qt.Key_Down:
            vis = self.view_end - self.view_begin
            center_time = self.view_begin + vis / 2
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
        return self.discourse_model.find_annotation(key, time, channel = self.channel)

    def get_acoustics(self, time):
        acoustics = self.discourse_model.get_acoustics(time)
        self.acousticsSelected.emit(acoustics)

    def on_mouse_press(self, event):
        """
        Mouse button press event
        """
        self.setFocus(True)
        self.selected_annotation = None
        self.selected_boundary = None

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

            if self.audio is None:
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
            if self.audio is None:
                return
            self.updatePlayTime(self.min_selected_time)
        elif event.button == 1 and is_single_click and not event.native.modifiers() & QtCore.Qt.ShiftModifier and \
                self.selected_annotation is None:
            time = self.audioWidget.transform_pos_to_time(event.pos)
            if self.audio is None:
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
            if self.audio is not None:
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
        if self.discourse_model is None:
            return
        if self.view_end == self.discourse_model.max_time \
                    and self.view_begin == 0 and factor > 1:
            return

        left_space = center_time - self.view_begin
        right_space = self.view_end - center_time

        min_time = center_time - left_space * factor
        max_time = center_time + right_space * factor

        if max_time > self.discourse_model.max_time:
            max_time = self.discourse_model.max_time
        if min_time < 0:
            min_time = 0
        self.view_begin = min_time
        self.view_end = max_time
        self.updateVisible()

    def pan(self, time_delta):
        if self.discourse_model is None:
            return
        if self.view_end == self.discourse_model.max_time and time_delta > 0:
            return
        if self.view_begin == 0 and time_delta < 0:
            return

        min_time = self.view_begin + time_delta
        max_time = self.view_end + time_delta
        if max_time > self.discourse_model.max_time:
            new_delta = time_delta - (max_time - self.discourse_model.max_time)
            min_time = self.view_begin + new_delta
            max_time = self.view_end + new_delta
        if min_time < 0:
            new_delta = time_delta - (min_time)
            min_time = self.view_begin + new_delta
            max_time = self.view_end + new_delta
        self.view_begin = min_time
        self.view_end = max_time
        self.updateVisible()

    def updateVisible(self):
        if self.discourse_model is None:
            return
        self.cacheFollowing()
        self.cachePreceding()
        self.audioWidget.update_time_bounds(self.view_begin, self.view_end)
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
            if a.end < self.view_begin:
                continue
            if isinstance(key, tuple):
                elements = getattr(a, key[0])
                for e in elements:
                    if e.end < self.view_begin:
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
        if self.selected_time > self.view_end:
            self.selected_time = self.view_end
        elif self.selected_time < self.view_begin:
            self.selected_time = self.view_begin
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
        if self.audio is None:
            self.audioWidget.update_signal(None)
            self.spectrumWidget.update_signal(None)
        else:
            if self.view_end - self.view_begin < 15:
                sig = self.audio.visible_signal(self.view_begin, self.view_end, self.channel)
                sr = self.audio.sr
            elif self.view_end - self.view_begin < 60:
                sig = self.audio.visible_downsampled_1000(self.view_begin, self.view_end, self.channel)
                sr = 1000
            else:
                sig = self.audio.visible_downsampled_100(self.view_begin, self.view_end, self.channel)
                sr = 100
            preemph_signal  = self.audio.visible_preemph_signal(self.view_begin, self.view_end, self.channel)

            t = np.arange(sig.shape[0]) / (sr) + self.view_begin

            data = np.array((t, sig)).T
            begin = time.time()
            self.audioWidget.update_signal(data)
            begin = time.time()
            self.spectrumWidget.update_sampling_rate(self.audio.sr)
            self.spectrumWidget.update_signal(preemph_signal)
            self.updatePlayTime(self.view_begin)

    def updateDiscourseModel(self, discourse_model):
        discourse_model, begin, end = discourse_model
        self.discourse_model = discourse_model
        self.audio = None
        if discourse_model.sound_file is not None:
            self.audioCacheWorker.setParams({'sound_file':self.discourse_model.sound_file, 'begin': begin, 'end': end})
            self.audioCacheWorker.start()
        if begin is None:
            begin = 0
        if end is None or end > self.discourse_model.max_time:
            end = self.discourse_model.max_time
        self.view_begin, self.view_end = begin, end
        self.audioWidget.update_time_bounds(self.view_begin, self.view_end)
        self.updateVisible()

    def drawAnnotations(self):
        annotations = self.discourse_model.annotations(begin = self.view_begin, end = self.view_end, channel = self.channel)
        self.audioWidget.update_annotations(annotations)

    def drawPitch(self):
        pitch = self.discourse_model.pitch_from_begin(begin = self.view_begin, end = self.view_end, channel = self.channel)
        self.spectrumWidget.update_pitch(pitch)

    def drawFormants(self):
        formants = self.discourse_model.formants_from_begin(begin = self.view_begin, end = self.view_end, channel = self.channel)
        self.spectrumWidget.update_formants(formants)

    def changeView(self, begin, end):
        if self.discourse_model is None:
            return
        self.discourse_model.update_times(begin, end)
        self.selectionChanged.emit(None)

    def clearDiscourse(self):
        self.discourse_model = None

        self.min_selected_time = None
        self.max_selected_time = None
        self.audioWidget.update_selection(self.min_selected_time, self.max_selected_time)
        self.need_update = False
