import os
import sys

def ensure_proper_setup():
    if sys.platform == 'win32':
        prog_path = r'C:\Program Files'
        config_path = os.path.expanduser(r'~\AppData\Roaming\Neo4j Community Edition')

    elif sys.platform == 'darwin':
