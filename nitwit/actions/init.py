from nitwit.storage import categories, tags
from nitwit.helpers import util, settings

import random, os, git, configparser


def handle_init( parser, options, args ):
    if (dir := settings.find_git_dir()) is None:
        return "Couldn't find a valid git repo"

    # Write out the config values
    cw = git.Repo(dir).config_writer()
    for option, default, func in settings.CONF:
        cw.set_value(settings.NAMESPACE, option, default)
    cw.release()

    # Write out the global
    config = configparser.ConfigParser()
    config['DEFAULT'] = {k: v for k, v, _ in settings.GLOBAL_CONF}
    with open(f'{dir}/{settings.CONF["directory"]}/config', "w") as handle:
        config.write( handle )

    # Now we can pull our settings and it should have valid data
    if (conf := settings.load_settings()) is None:
        return "Couldn't load settings after initial attempt in Git repo"

    print( f"Initialized nitwit configuration into Git repository in {dir}/.git")

    # Setup the default categories
    cats = []
    for name, active, hidden in settings.CATEGORIES:
        cat = categories.Category()
        cat.active = active
        cat.hidden = hidden
        cats.append( cat )
    categories.export_categories( conf, cats )

    # Setup the default categories
    ts = []
    for name in settings.TAGS:
        tag = tags.Tag()
        tag.name = name
        ts.append( tag )
    tags.export_tags( conf, ts )

    return None


