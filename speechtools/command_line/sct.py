import os
import sys

import mock


MOCK_MODULES = ['matplotlib', 'matplotlib.image',  'matplotlib.pyplot',
                'matplotlib.ticker',
                'librosa.util.feature_extractor',
                'sklearn', 'sklearn.base', 'sklearn.decomposition',
                'sklearn.cluster', 'sklearn.feature_extraction',
                'sklearn.neighbors',
                'tkinter']

for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = mock.Mock()
    if mod_name == 'matplotlib':
        sys.modules[mod_name].__version__ = '0.1'

import multiprocessing

from speechtools.main import MainWindow, QtWidgets

if __name__ == '__main__':
    multiprocessing.freeze_support()
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(app)

    app.setActiveWindow(main)
    main.show()
    sys.exit(app.exec_())
