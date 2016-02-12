
from PyQt5 import QtGui, QtCore, QtWidgets

def get_system_font_height():
    f = QtGui.QFont()
    fm = QtGui.QFontMetrics(f)
    return fm.height()
