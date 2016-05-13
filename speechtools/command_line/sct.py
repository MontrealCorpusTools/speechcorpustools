import os
import sys
import multiprocessing

from speechtools.main import MainWindow, QtWidgets

if __name__ == '__main__':
    multiprocessing.freeze_support()
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(app)

    app.setActiveWindow(main)
    main.show()
    sys.exit(app.exec_())
