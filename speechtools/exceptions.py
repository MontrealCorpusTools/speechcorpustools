import os
import sys
import traceback

from polyglotdb.exceptions import *

## Base exceptions

class SCTError(Exception):
    pass

## Acoustic exceptions

class NoSoundFileError(SCTError):
    pass
