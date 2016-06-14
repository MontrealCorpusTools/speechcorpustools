
import os
import sys

from PyInstaller.utils.hooks import (
    collect_data_files, collect_dynamic_libs)



hiddenimports = ['vispy', 'six', 'vispy.app.backends._pyqt5',
'vispy.app.backends._pyqt4', 'vispy.app.backends._pyside',
'vispy.app.backends._pyglet','vispy.app.backends._glfw',
'vispy.app.backends._sdl2','vispy.app.backends._wx',
'vispy.app.backends._egl','vispy.app.backends._osmesa',
'vispy.app.backends._test',
'sklearn', 'sklearn.neighbors.typedefs']

if sys.platform == 'win32':
    binaries = [
    #(r"C:\Miniconda3\envs\sct\Lib\site-packages\numpy\core\mkl_intel_thread.dll", '.'),
    (r"C:\Miniconda3\envs\sct\Library\bin\mkl_avx2.dll", '.'),
    (r"C:\Miniconda3\envs\sct\Library\bin\mkl_def.dll", '.'),
    ]

datas = collect_data_files('vispy')

