
from PyQt5 import QtGui, QtCore, QtWidgets, QtMultimedia

class MediaPlayer(QtMultimedia.QMediaPlayer):
    def __init__(self):
        super(MediaPlayer, self).__init__()
        self.max_time = None
        self.min_time = None
        self.setNotifyInterval(1)
        self.positionChanged.connect(self.checkStop)

    def setMaxTime(self, max_time):
        self.max_time = max_time * 1000

    def setMinTime(self, min_time):
        self.min_time = min_time * 1000

    def checkStop(self, position):
        #print(self.mediaStatus())
        #print(position, self.max_time)
        if self.state() == QtMultimedia.QMediaPlayer.PlayingState:
            if self.min_time is not None:
                if position < self.min_time:
                    self.setPosition(self.min_time)
            if self.max_time is not None:
                if position > self.max_time:
                    self.stop()
