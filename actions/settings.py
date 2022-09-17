import os
from git import Repo

def find_git_dir():
    dirs = os.path.dirname(os.path.abspath(__file__)).split('/')

    # Step back through my path looking for .git
    for idx in range(len(dirs)):
        dir = '/'.join(dirs[:-idx])

        if os.path.exists(f'{dir}/.git'):
            return dir

    return None


def load_settings():
    if (dir := find_git_dir()) is None:
        return None

    result = {}

    # Load it up
    cr = Repo.config_reader()
    cr.get_value("nitwit", "option")

    return result