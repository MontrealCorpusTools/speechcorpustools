#!/bin/sh


if [ `uname` == Darwin ]; then
    pyinstaller -w --clean --debug -y --additional-hooks-dir=freezing/hooks speechtools/command_line/sct.py --exclude-module sphinx --exclude-module tkinter --exclude-module matplotlib  --exclude-module matplotlib.backends --hidden-import mock --hidden-import setuptools

fi
