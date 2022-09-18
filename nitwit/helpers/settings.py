import os, git

from nitwit.helpers import util


## Defines the configuration section of the git file
NAMESPACE = 'nitwit'
CONF = [
    ('directory',       'examples', util.xstr),
    ('defaultcategory', 'pending', util.xstr),
]
CATEGORIES = [
    'pending',
    'in_progress',
    'testing',
    'completed',
    'trash'
]

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

    # Load it up
    cr = git.Repo(dir).config_reader()
    for option, default, func in CONF:
        result[option] = func(cr.get_value(NAMESPACE, option, default))

        if option == 'directory':
            result[option] = f"{dir}/{result[option]}"

    return result


def install_into_git():
    if (dir := find_git_dir()) is None:
        return "Couldn't find a valid git repo"

    # Write out the config values
    cw = git.Repo(dir).config_writer()
    for option, default, func in CONF:
        cw.set_value(NAMESPACE, option, default)
    cw.release()

    print(f"Initialized nitwit configuration into Git repository in {dir}/.git")

    return None

