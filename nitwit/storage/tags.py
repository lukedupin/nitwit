import os, sys, re, glob

from pathlib import Path
from datetime import datetime

from nitwit.storage.parser import parse_content
from nitwit.helpers import util


class Tag:
    def __init__(self):
        self.filename = None
        self.name = None
        self.title = None
        self.notes = []


### Bulk commands for parsing and writing to the filesystem

# Parse all tags
def import_tags( settings, filter_names=None ):
    tags = []

    # Read in all the tags
    for file in glob.glob(f'{settings["directory"]}/_tags/**.md', recursive=True):
        info = re.split('/', file)
        name = re.sub( r'[.]md$', '', info[-1].lower() )
        if filter_names is not None and name not in filter_names:
            continue

        with open(file) as handle:
            if (tag := parse_tag( handle, name )) is not None:
                tags.append( tag )

    return tags


# Export all sprints
def export_tags( settings, tags ):
    for tag in tags:
        dir = f'{settings["directory"]}/_tags'
        Path(dir).mkdir(parents=True, exist_ok=True)

        with open(f"{dir}/{tag.name}.md", 'w') as handle:
            export_tag( handle, tag )


### Individual parse/export commands

# Parse tags
def parse_tag( handle, name=None ):
    if (parser := parse_content( handle )) is None and name is None:
        return None

    tag = Tag()
    tag.filename = handle.name
    tag.notes = parser.notes

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
def export_tag( handle, tag, include_name=False ):
    if tag.title is not None:
        handle.write(f'# {tag.title}\n')
    else:
        handle.write(f'# {tag.name.capitalize()}\n')
    handle.write('\n')

    if include_name:
        handle.write(f'> #{tag.name}\n')
        handle.write('\n')

    # Write out the user's notes
    for note in tag.notes:
        handle.write(f'{note}\n')