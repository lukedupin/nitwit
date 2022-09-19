from nitwit.storage import categories, tags
from nitwit.helpers import util, settings

import random, os, git


def handle_init( parser, options, args ):
    if (dir := settings.find_git_dir()) is None:
        return "Couldn't find a valid git repo"

    # Write out the config values
    cw = git.Repo(dir).config_writer()
    for option, default, func in settings.CONF:
        cw.set_value(settings.NAMESPACE, option, default)
    cw.release()

    # Now we can pull our settings and it should have valid data
    if (conf := settings.load_settings()) is None:
        return "Couldn't load settings after initial attempt in Git repo"

    print( f"Initialized nitwit configuration into Git repository in {dir}/.git")

    # Setup the default categories
    cats = [categories.Category( None, cat ) for cat in settings.CATEGORIES]
    categories.export_categories( conf, cats )

    # Setup the default categories
    ts = [tags.Tag( None, tag ) for tag in settings.TAGS]
    tags.export_tags( conf, ts )

    return None


