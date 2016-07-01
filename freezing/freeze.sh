#!/bin/sh


if [ `uname` == Darwin ]; then
    pyinstaller --clean --debug -y --additional-hooks-dir=freezing/hooks speechtools/command_line/sct.py

fi
