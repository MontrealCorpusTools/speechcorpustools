import sys
import os
import scipy.special
import PyQt5
from cx_Freeze import setup, Executable

def readme():
    with open('README.md') as f:
        return f.read()


ufuncs_path = scipy.special._ufuncs.__file__
incl_files = [(ufuncs_path,os.path.split(ufuncs_path)[1])]
base = None
if sys.platform == "win32":
    base = "Win32GUI"
    libegl = os.path.join(os.path.dirname(PyQt5.__file__),'libEGL.dll')
    incl_files.append((libegl,os.path.split(libegl)[1]))

group_name = 'SCT'

exe_name = 'Speech Corpus Tools'

shortcut_table = [
    ("StartMenuShortcut",        # Shortcut
     "ProgramMenuFolder",          # Directory_
     "%s" % (exe_name,),           # Name
     "TARGETDIR",              # Component_
     "[TARGETDIR]pct.exe",# Target
     None,                     # Arguments
     None,                     # Description
     None,                     # Hotkey
     None,   # Icon
     None,                     # IconIndex
     None,                     # ShowCmd
     'TARGETDIR'               # WkDir
     )
    ]

build_exe_options = {"excludes": [
                        'matplotlib',
                        "tcl",
                        'ttk',
                        "tkinter",],
                    "include_files":incl_files,
                    "includes": [
                            "PyQt5",
                            "PyQt5.QtWebKitWidgets",
                            "PyQt5.QtWebKit",
                            "PyQt5.QtPrintSupport",
                            "PyQt5.QtMultimedia",
                            "numpy",
                            "scipy",
                            "numpy.lib.format",
                            "numpy.linalg",
                            "numpy.linalg._umath_linalg",
                            "numpy.linalg.lapack_lite",
                            "scipy.io.matlab.streams",
                            "scipy.integrate",
                            "scipy.integrate.vode",
                            #"scipy.sparse.linalg.dsolve.umfpack",
                            "scipy.integrate.lsoda",
                            "scipy.special",
                            "scipy.special._ufuncs_cxx",
                            "scipy.sparse.csgraph._validation",
                            "acousticsim",
                            "textgrid",
                            "sys"]
                            }


bdist_mac_options = {'iconfile':'docs/images/icon.icns',
                    'qt_menu_nib':'/opt/local/share/qt5/plugins/platforms',
                    'bundle_name':'Speech Corpus Tools',
                    #'include_frameworks':["/Library/Frameworks/Tcl.framework",
                    #                    "/Library/Frameworks/Tk.framework"]
                                        }
bdist_dmg_options = {'applications_shortcut':True}

setup(name='Speech Corpus Tools',
      version='0.0.1',
      description='',
      long_description='',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering',
        'Topic :: Text Processing :: Linguistic',
      ],
      keywords='speech corpus phonetics',
      url='https://github.com/MontrealCorpusTools/speechcorpustools',
      author='Montreal Corpus Tools',
      author_email='michael.e.mcauliffe@gmail.com',
      packages=['speechtools',
                'speechtools.command_line',
                'speechtools.acoustics',
                'speechtools.graph',
                'speechtools.gui',
                'speechtools.gui.plot',
                'speechtools.gui.plot.widgets',
                'speechtools.io',
                'speechtools.sql'],
      executables = [Executable('speechtools/command_line/sct.py',
                            #targetName = 'pct',
                            base='Console',
                            #shortcutDir=r'[StartMenuFolder]\%s' % group_name,
                            #shortcutName=exe_name,
                            #icon='docs/images/icon.icns'
                            )],
      options={
          'build_exe': build_exe_options,
          'bdist_mac':bdist_mac_options,
          'bdist_dmg':bdist_dmg_options}
      )