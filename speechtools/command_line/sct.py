import os
import mock
import sys

MOCK_MODULES = ['matplotlib', 'matplotlib.image', 'matplotlib.ticker',
                'matplotlib.pyplot', 'tkinter', 'tkinter.filedialog']

for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = mock.Mock()

import multiprocessing

from speechtools.main import MainWindow, QtWidgets

if __name__ == '__main__':
    multiprocessing.freeze_support()
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(app)

    app.setActiveWindow(main)
    main.show()
    sys.exit(app.exec_())
