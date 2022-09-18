import os
from git import Repo
from helpers import util


def find_git_dir():
    dirs = os.getcwd().split('/')
    count = len(dirs)

    # Step back through my path looking for .git
    for idx in range(count):
        dir = '/'.join(dirs[:count-idx])

        if os.path.exists(f'{dir}/.git'):
            return dir

    return None


def load_settings():
    if (dir := find_git_dir()) is None:
        return None

    result = {}

    # Define all the settings and their defaults we're going to load
    keys = [
        ('directory', 'nitwit', lambda x: f'{dir}/' + util.xstr(x)),
    ]

    # Load it up
    cr = Repo(dir).config_reader()
    for option, default, func in keys:
        result[option] = func(cr.get_value("nitwit", option, default))

    return result