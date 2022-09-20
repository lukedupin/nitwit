import os, sys, re, glob

from pathlib import Path
from datetime import datetime

from nitwit.helpers import util


class Tag:
    def __init__(self, filename, name):
        self.filename = filename
        self.name = name
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
def parse_tag( handle, name ):
    tag = Tag( handle.name, name )

    # Load up the files and go!
    for idx, line in enumerate( handle.readlines()):
        line = line.rstrip()

        # Store the title!
        if idx == 0 and tag.title is None and \
           (ret := re.search(r'^# (.*$)', line)) is not None:
            tag.title = ret.group(1)

        # Add in all the chatter
        else:
            tag.notes.append( line )

    return tag


# Write out a spring file
def export_tag( handle, tag ):
    if tag.title is not None:
        handle.write(f'# {tag.title}\n')
        handle.write('\n')

    # Write out the user's notes
    for note in tag.notes:
        handle.write(f'{note}\n')