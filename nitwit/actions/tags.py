from nitwit.storage import tags as tags_mod
from nitwit.helpers import util

import random, os


def handle_tag( parser, options, args, settings ):
    # Print out the tags
    if len(args) < 2:
        tags = tags_mod.import_tags( settings['directory'] )
        if len(tags) <= 0:
            print( "No tags found. Try creating one." )

        # Dump the tags to the screen
        for tag in tags:
            print(f'#{tag.name}')

        return None

    # Get the tag name
    tag_name = args[1].lower()

    # Either creator or edit a tag
    tags = tags_mod.import_tags( settings['directory'], filter_names=[tag_name] )
    if len(tags) <= 0:
        tag = tags_mod.Tag( None, tag_name )
        tag.title = tag.name.capitalize()
        tags_mod.export_tags( settings['directory'], [tag] )
        print(f"Created tag #{tag.name}")

    else:
        os.system(f'{os.environ["EDITOR"]} {tags[0].filename}')

    return None