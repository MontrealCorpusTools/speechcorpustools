
pyinstaller -c -F --clean -y ^
--additional-hooks-dir=freezing\hooks ^
--exclude-module matplotlib ^
--exclude-module tkinter ^
speechtools\command_line\sct.py
