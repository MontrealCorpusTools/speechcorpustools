
import os
import pickle
from polyglotdb.config import BASE_DIR

PROFILE_DIR = os.path.join(BASE_DIR, 'profiles')
os.makedirs(PROFILE_DIR, exist_ok = True)

class BaseProfile(object):
    extension = ''
    def __init__(self):
        self.name = ''

    @property
    def path(self):
        return os.path.join(PROFILE_DIR, self.name.replace(' ', '_') + self.extension)

    @classmethod
    def load_profile(cls, name):
        path = os.path.join(PROFILE_DIR, name.replace(' ', '_') + cls.extension)
        with open(path, 'rb') as f:
            obj = pickle.load(f)
        return obj

    def save_profile(self):
        with open(self.path, 'wb') as f:
            pickle.dump(self, f)

