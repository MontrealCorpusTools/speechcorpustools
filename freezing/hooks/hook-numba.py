
import os
import sys

from PyInstaller.utils.hooks import (
    collect_data_files, collect_dynamic_libs)

hiddenimports = ['llvmlite']

if sys.platform == 'win32':
    binaries = [(r"C:\Miniconda3\envs\sct\Lib\site-packages\llvmlite\binding\llvmlite.dll", '.')]


