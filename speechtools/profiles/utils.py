import os

from .query import PROFILE_DIR

from .premade import Lab1QueryProfile, Lab2QueryProfile, Lab3QueryProfile

def ensure_existence():
    os.makedirs(PROFILE_DIR, exist_ok = True)
    for profile in [Lab1QueryProfile(),
                    Lab2QueryProfile(),
                    Lab3QueryProfile()]:
        if not os.path.exists(profile.path):
            profile.save_profile()

def available_query_profiles():
    files = os.listdir(PROFILE_DIR)
    profiles = []
    for f in files:
        name, ext = os.path.splitext(f)
        if not ext == '.queryprofile':
            continue
        profiles.append(name.replace('_', ' '))
    return profiles
