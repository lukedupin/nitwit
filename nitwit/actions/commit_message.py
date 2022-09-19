from nitwit.storage import sprints as sprints_mod
from nitwit.storage import tickets as tickets_mod


def handle_prepare_commit( settings, filename ):
    sprints = sprints_mod.import_latest_sprints( settings, filter_owners=[settings['username']])
    if len(sprints) != 1:
        return "Couldn't determin current sprint"

    return None