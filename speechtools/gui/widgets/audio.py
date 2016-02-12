
from struct import pack

from PyQt5 import QtGui, QtCore, QtWidgets, QtMultimedia

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

class AudioOutput(QtMultimedia.QAudioOutput):
    def __init__(self):
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
            QtCore.qWarning("Default format not supported - trying to use nearest")
            self.m_format = info.nearestFormat(self.m_format)
        super(AudioOutput, self).__init__(self.m_device, self.m_format)
        self.setNotifyInterval(1)
        self.setBufferSize(6400)
