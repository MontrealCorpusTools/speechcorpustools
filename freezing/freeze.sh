#!/bin/sh


if [ `uname` == Darwin ]; then
    pyinstaller -w --clean --debug -y --additional-hooks-dir=freezing/hooks speechtools/command_line/sct.py --exclude-module tkinter --exclude-module matplotlib --hidden-import mock

fi
