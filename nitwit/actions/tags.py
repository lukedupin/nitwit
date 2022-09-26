
from optparse import OptionParser

from nitwit.storage import tags as tags_mod
from nitwit.helpers import util

import random, os, re


def handle_tag( settings ):
    # Configure the usage
    #usage = "usage: %command [options] arg"
    parser = OptionParser("")
    parser.add_option("-c", "--create", dest="create", help="Create a new item")
    parser.add_option("-a", "--all", action="store_true", dest="all")

    (options, args) = parser.parse_args()

    if options.all:
        return process_all( settings )

    # Print out the tags
    if len(args) < 2:
        tags = tags_mod.import_tags( settings )
        if len(tags) <= 0:
            print( "No tags found. Try creating one." )

        # Dump the tags to the screen
        print("Tags")
        for tag in tags:
            print(f'    #{tag.name.ljust(24)} {util.xstr(tag.title)[:64]}')

        return None

    # Get the tag name
    tag_name = args[1].lower()

    # Either creator or edit a tag
    tags = tags_mod.import_tags( settings, filter_names=[tag_name] )
    if len(tags) <= 0:
        tag = tags_mod.Tag( None, tag_name )
        tag.title = re.sub('[_-]', ' ', tag.name.capitalize())
        tags_mod.export_tags( settings, [tag] )
        print(f"Created tag #{tag.name}")

    else:
        os.system(f'{os.environ["EDITOR"]} {tags[0].filename}')

    return None


def process_all( settings ):
    tags = tags_mod.import_tags(settings)
    if len(tags) <= 0:
        return "No tags found. Try creating one."

    # Open the temp file to write out tags
    filename = f"{settings['directory']}/tags.md"
    with open(filename, "w") as handle:
        for tag in tags:
            print(tag.name)
            tags_mod.export_tag( handle, tag, include_name=True )

    # Start the editor
    os.system(f'{os.environ["EDITOR"]} {filename}')

    # Wrapp up by parsing
    tags = []
    try:
        with open(filename) as handle:
            # Loop while we have data to read
            while not util.is_eof(handle):
                if (tag := tags_mod.parse_tag(handle, None)) is None:
                    break

                if tag.name is None:
                    return f"Error in tag: {tag.title}"
                tags.append( tag )

    except FileNotFoundError:
        return None

    # Finallly output the updated tags
    os.remove(filename)
    tags_mod.export_tags( settings, tags )

    return None
