import os, git
import re

from nitwit.helpers import util


## Defines the configuration section of the git file
NAMESPACE = 'nitwit'
CONF = [
    ('directory',           'examples', util.xstr),
    ('defaultcategory',     'pending', util.xstr),
    ('subscribecategories', 'accepted', lambda x: util.xstr(x).split(',')),
    ('subscribetags',       'bug,crash', lambda x: util.xstr(x).split(',')),
    ('sprintcategories',    'pending,accepted,testing', lambda x: util.xstr(x).split(',')),
    ('hiddencategories',    'trash,completed', lambda x: util.xstr(x).split(',')),
]
CATEGORIES = [
    'pending',
    'accepted',
    'testing',
    'completed',
    'trash'
]
TAGS = [
    'bug',
    'crash',
    'feature',
]

class User:
    def __init__(self):
        self.name = None
        self.username = None
        self.email = None

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

    # Pull the user information
    for key in ('email', 'name'):
        result[key] = cr.get_value('user', key)

    # Load the username
    result['username'] = re.sub('@.*$', '', result['email'])

    return result


def get_users( settings ):
    if (dir := find_git_dir()) is None:
        return None

    users = {}
    emails = {
        'noreply@github.com': True,
    }
    for repo in git.Repo(dir).iter_commits():
        if repo.committer.email in emails:
            continue

        # Create a new user
        user = User()
        user.name = repo.committer.name
        user.username = re.sub("@.*$", '', repo.committer.email)
        user.email = repo.committer.email
        users[user.username] = user
        emails[user.email] = True

    myself = []
    if settings['username'] in users:
        myself.append( users[settings['username']])
        del users[settings['username']]

    return myself + [users[x] for x in users.keys()]

