
import os
import sys

from PyInstaller.utils.hooks import (
    collect_data_files, collect_dynamic_libs)



hiddenimports = ['vispy', 'six', 'vispy.app.backends._pyqt5',
'matplotlib','tkinter', 'sklearn', 'sklearn.neighbors.typedefs']

if sys.platform == 'win32':
    hiddenimports += ['tkinter.filedialog']
    binaries = [(r"C:\Miniconda3\envs\sct\Lib\site-packages\numpy\core\mkl_intel_thread.dll", '.')]

datas = collect_data_files('vispy')

