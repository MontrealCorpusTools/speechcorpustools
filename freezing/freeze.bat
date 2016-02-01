
pyinstaller -c --clean --debug -y ^
--additional-hooks-dir=freezing\hooks ^
speechtools\command_line\sct.py
