
pyinstaller -F --clean -y ^
--additional-hooks-dir=freezing\hooks ^
--exclude-module matplotlib ^
--exclude-module tkinter ^
--exclude-module pygments ^
--exclude-module sklearn ^
--exclude-module sphinx ^
--exclude-module docutils ^
--exclude-module scikits.samplerate ^
speechtools\command_line\sct.py
