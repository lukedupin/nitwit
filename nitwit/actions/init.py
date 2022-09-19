from nitwit.storage import categories, tags
from nitwit.helpers import util, settings

import random, os, git


def handle_init( parser, options, args ):
    if (ret := settings.install_into_git()) is not None:
        return ret

    # Now we can pull our settings and it should have valid data
    if (conf := settings.load_settings()) is None:
        return "Couldn't load settings after initial attempt in Git repo"

    # Setup the default categories
    cats = [categories.Category( None, cat ) for cat in settings.CATEGORIES]
    categories.export_categories( conf, cats )

    # Setup the default categories
    ts = [tags.Tag( None, tag ) for tag in settings.TAGS]
    tags.export_tags( settings, ts )

    return None


