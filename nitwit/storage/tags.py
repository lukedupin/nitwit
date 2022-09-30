import os, sys, re, glob, git

from pathlib import Path
from datetime import datetime

from nitwit.storage.parser import parse_content
from nitwit.helpers import settings as settings_mod
from nitwit.helpers import util


class Tag:
    def __init__(self):
        self.filename = None
        self.name = None
        self.title = None
        self.notes = []
        self.hidden = False


### Bulk commands for parsing and writing to the filesystem


def find_tag_by_name( settings, name, show_hidden=False ):
    # Fastest, look for a specific one
    tags = import_tags( settings, filter_names=[util.xstr(name)], show_hidden=show_hidden )
    if len(tags) == 1:
        return tags[0]

    # Attempt an index lookup
    idx = util.xint(name) - 1
    if idx < 0:
        return None

    # Slower, pulling in all tags and picking by index after sorting
    tags = import_tags( settings, show_hidden=show_hidden )
    if idx < len(tags):
        return tags[idx]

    return None


# Parse all tags
def import_tags( settings, filter_names=None, show_hidden=False ):
    tags = []

    # Read in all the tags
    for file in glob.glob(f'{settings["directory"]}/tags/**.md', recursive=True):
        info = re.split('/', file)
        name = re.sub( r'[.]md$', '', info[-1].lower() )
        if filter_names is not None and name not in filter_names:
            continue

        with open(file) as handle:
            if (tag := parse_tag( settings, handle, name )) is not None:
                if show_hidden or not tag.hidden:
                    tags.append( tag )

    return sorted( tags, key=lambda x: x.name.lower() )


# Export all tags
def export_tags( settings, tags ):
    # Setup the base tags
    dir = f'{settings["directory"]}/tags'
    Path(dir).mkdir(parents=True, exist_ok=True)

    # Pull the repo so we can add stuff
    if (repo := settings_mod.git_repo()) is None:
        print("Couldn't find repo")
        return

    for tag in tags:
        with open(f"{dir}/{tag.name}.md", 'w') as handle:
            export_tag( settings, handle, tag )

            repo.index.add([handle.name])


### Individual parse/export commands

# Parse tags
def parse_tag( settings, handle, name=None ):
    if (parser := parse_content( handle )) is None and name is None:
        return None

    tag = Tag()
    tag.filename = handle.name
    tag.notes = parser.notes
    tag.hidden = util.xbool(parser.variables.get('hidden'))

    # Store the name
    tag.name = name
    if name is None and len(parser.tags) > 0:
        tag.name = parser.tags[0]
    if tag.name is None:
        return None

    if parser.title is not None:
        tag.title = parser.title
    else:
        tag.title = util.xstr(tag.name).capitalize()

    return tag


# Write out a spring file
def export_tag( settings, handle, tag, include_name=False ):
    # Write out the title
    if tag.title is not None:
        handle.write(f'# {tag.title}\n\n')
    else:
        handle.write(f'# {tag.name.capitalize()}\n\n')

    # Write my modifiers
    if tag.hidden is not None or include_name:
        if include_name:
            handle.write(f'> #{tag.name}\n')
        if tag.hidden is not None:
            handle.write(f'> $hidden={"true" if tag.hidden else "false"}\n')
        handle.write('\n')

    # Write out the user's notes
    if len(tag.notes) > 0:
        for note in tag.notes:
            handle.write(f'{note}\n')
        handle.write('\n')
