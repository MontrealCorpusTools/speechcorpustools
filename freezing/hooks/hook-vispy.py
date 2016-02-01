
import os

from PyInstaller.utils.hooks import (
    collect_data_files)



hiddenimports = ['vispy', 'six', 'vispy.app.backends._pyqt5', 'matplotlib','tkinter', 'sklearn', 'sklearn.neighbors.typedefs']

datas = collect_data_files('vispy')

