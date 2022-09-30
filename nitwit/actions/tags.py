from optparse import OptionParser

from git import GitCommandError

from nitwit.storage import tags as tags_mod
from nitwit.helpers import settings as settings_mod
from nitwit.helpers import util

import random, os, re


def handle_tag( settings ):
    #usage = "usage: %command [options] arg"
    parser = OptionParser("")
    parser.add_option("-c", "--create", action="store_true", dest="create", help="Create a new item")
    parser.add_option("-a", "--all", action="store_true", dest="all", help="Edit all the tags at once")
    parser.add_option("-b", "--batch", action="store_true", dest="batch", help="Edit all tags at once")

    (options, args) = parser.parse_args()
    args = args[1:] # Cut away the action name, since its always "Tag"

    # Edit all the tags
    if options.batch:
        return process_batch( settings, args, options )

    # Create a new tag
    if options.create:
        tag = tags_mod.find_tag_by_name( settings, ' '.join(args), show_hidden=options.all)
        if tag is None:
            return process_create( settings, args, options )
        else:
            return process_edit( settings, args, options, tag )

    # Edit a tag?
    if len(args) > 0:
        return process_edit( settings, args, options )

    # Print out the tags
    return process_print( settings, args, options )


def process_print( settings, args, options ):
    tags = sorted( tags_mod.import_tags( settings, show_hidden=options.all ), key=lambda x: x.name )
    if len(tags) <= 0:
        print( "No tags found. Try creating one." )

    # Dump the tags to the screen
    print("Tags")
    for idx, tag in enumerate(tags):
        print(f'{str(idx+1).ljust(5)} #{tag.name.ljust(20)} {util.xstr(tag.title)[:64]}')

    return None


def process_batch( settings, args, options ):
    tags = tags_mod.import_tags(settings, show_hidden=options.all)
    if len(tags) <= 0:
        return "No tags found. Try creating one."

    kill_list = {}

    # Open the temp file to write out tags
    filename = f"{settings['directory']}/tags.md"
    with open(filename, "w") as handle:
        for idx, tag in enumerate(tags):
            kill_list[tag.name] = True
            tags_mod.export_tag( settings, handle, tag, include_name=True )

            if idx + 1 < len(tags):
                handle.write("======\n\n")

    # Start the editor
    util.editFile( filename )

    # Wrapp up by parsing
    tags = []
    try:
        with open(filename) as handle:
            # Loop while we have data to read
            while not util.is_eof(handle):
                if (tag := tags_mod.parse_tag(settings, handle)) is None:
                    break

                tags.append( tag )
                if tag.name in kill_list:
                    del kill_list[tag.name]

    except FileNotFoundError:
        return None

    # Remove everything that is now missing
    if (repo := settings_mod.git_repo()) is not None:
        for rm in kill_list.keys():
            try:
                repo.index.move([f'{settings["directory"]}/tags/{rm}.md', f'{settings["directory"]}/tags/{rm}.md_'])

            except GitCommandError:
                pass

    # Finally output the updated tags
    os.remove(filename)
    tags_mod.export_tags( settings, tags )

    return None


def process_create( settings, args, options ):
    tag = tags_mod.Tag()
    if len(args) > 0:
        tag.name = args[0]
        tag.title = re.sub('[_-]', ' ', ' '.join(args).capitalize())

    else:
        tag.name = "tag_title"
        tag.title = re.sub('[_-]', ' ', tag.name.capitalize())

    # Open the temp file to write out tags
    tmp = f"{settings['directory']}/tags.md"
    with open(tmp, "w") as handle:
        tags_mod.export_tag( settings, handle, tag, include_name=True )

    # Start the editor
    util.editFile( tmp )

    # Wrapp up by parsing
    tags = []
    try:
        with open(tmp) as handle:
            # Loop while we have data to read
            while not util.is_eof(handle):
                if (tag := tags_mod.parse_tag(settings, handle)) is None:
                    break

                tags.append( tag )
        os.remove(tmp)

    except FileNotFoundError:
        os.remove(tmp)
        print("Failed to create tag")
        return None

    # Write out the new tag
    if len(tags) != 1:
        print("Failed to create tag")
        return None

    tags_mod.export_tags( settings, tags )
    print(f"Created tag: {tags[0].name}")


def process_edit( settings, args, options, tag=None ):
    if tag is None:
        tag_name = ' '.join(args)
        tag = tags_mod.find_tag_by_name( settings, tag_name, show_hidden=options.all )
        if tag is None:
            print(f"Couldn't find tag by: {tag_name}")
            return None

    util.editFile( tag.filename )