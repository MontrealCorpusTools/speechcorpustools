import os
import sys

from speechtools.gui.main import MainWindow, QtWidgets

if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(app)

    app.setActiveWindow(main)
    main.show()
    sys.exit(app.exec_())
