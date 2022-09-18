import os, sys, re, glob

from pathlib import Path
from datetime import datetime

from nitwit.helpers import util


class Category:
    def __init__(self, filename, name):
        self.filename = filename
        self.name = name
        self.title = None
        self.notes = []


### Bulk commands for parsing and writing to the filesystem

# Parse all tags
def import_categories( base_dir, filter_names=None ):
    categories = []

    # Read in all the categories
    for file in glob.glob(f'{base_dir}/_categories/**.md', recursive=True):
        info = re.split('/', file)
        name = re.sub( r'[.]md$', '', info[-1].lower() )
        if filter_names is not None and name not in filter_names:
            continue

        with open(file) as handle:
            if (category := parse_category( handle, name )) is not None:
                categories.append( category )

    return categories


# Export all sprints
def export_categories( base_dir, categories ):
    for category in categories:
        dir = f"{base_dir}/_categories"
        Path(dir).mkdir(parents=True, exist_ok=True)

        with open(f"{dir}/{category.name}.md", 'w') as handle:
            export_category( handle, category )


### Individual parse/export commands


# Parse tags
def parse_category( handle, name ):
    category = Category( handle.name, name )

    # Load up the files and go!
    for idx, line in enumerate( handle.readlines()):
        line = line.rstrip()

        # Store the title!
        if idx == 0 and category.title is None and \
           (ret := re.search(r'^# (.*$)', line)) is not None:
            category.title = ret.group(1)

        # Add in all the chatter
        else:
            category.notes.append( line )

    return category


# Write out a spring file
def export_category( handle, category ):
    if category.title is not None:
        handle.write(f'# {category.title}\r\n')
        handle.write('\r\n')

    # Write out the user's notes
    for note in category.notes:
        handle.write(f'{note}\r\n')
