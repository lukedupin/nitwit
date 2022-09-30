import os, sys, re, glob

from pathlib import Path
from datetime import datetime

from nitwit.storage.parser import parse_content
from nitwit.helpers import settings as settings_mod
from nitwit.helpers import util


class Category:
    def __init__(self):
        self.filename = None
        self.name = None
        self.title = None
        self.accepted = True
        self.visible = True
        self.notes = []


### Bulk commands for parsing and writing to the filesystem

def safe_category( settings, category, categories=None ):
    # Clean up the category, check for empty, we can just exit now
    category = util.xstr(category).lower()
    if category == "":
        return settings['defaultcategory']

    # Were we given categories?
    if categories is not None:
        for c in categories:
            if c.name == category:
                return category

    # Lookup by filesystem?
    for file in glob.glob(f"{settings['directory']}/categories/**.md", recursive=True):
        info = re.split('/', file)
        if re.sub( r'[.]md$', '', info[-1].lower() ) == category:
            return category

    # Finally, just return the default category
    return settings['defaultcategory']


# Parse all tags
def import_categories( settings, filter_names=None, show_invisible=False ):
    categories = []

    # Read in all the categories
    for file in glob.glob(f"{settings['directory']}/categories/**.md", recursive=True):
        info = re.split('/', file)
        name = re.sub( r'[.]md$', '', info[-1].lower() )
        if filter_names is not None and name not in filter_names:
            continue

        with open(file) as handle:
            if (category := parse_category( settings, handle, name )) is not None:
                if show_invisible or not category.visible:
                    categories.append( category )

    return categories


# Export all sprints
def export_categories( settings, categories ):
    # Create the categories
    dir = f"{settings['directory']}/categories"
    Path(dir).mkdir(parents=True, exist_ok=True)

    repo = settings_mod.git_repo()

    for category in categories:
        with open(f"{dir}/{category.name}.md", 'w') as handle:
            export_category( settings, handle, category )

            repo.index.add( [handle.name] )


### Individual parse/export commands


# Parse tags
def parse_category( settings, handle, name ):
    if (parser := parse_content( handle )) is None and name is None:
        return None

    category = Category()
    category.filename = handle.name
    category.notes = parser.notes
    category.accepted = util.xbool(parser.variables.get('accepted'))
    category.visible = util.xbool(parser.variables.get('visible'))

    # Store the name
    category.name = name
    if name is None and parser.category is not None:
        category.name = parser.category
    if category.name is None:
        return None

    if parser.title is not None:
        category.title = parser.title
    else:
        category.title = util.xstr(category.name).capitalize()

    return category


# Write out a spring file
def export_category( settings, handle, category, include_name=False ):
    # Write out the title
    if category.title is not None:
        handle.write(f'# {category.title}\n\n')
    else:
        handle.write(f'# {category.name.capitalize()}\n\n')

    # Write my modifiers
    if category.accepted is not None or category.visible is not None or include_name:
        if include_name:
            handle.write(f'> #{category.name}\n')
        if category.accepted is not None:
            handle.write(f'> $accepted={"true" if category.accepted else "false"}\n')
        if category.visible is not None:
            handle.write(f'> $visible={"true" if category.visible else "false"}\n')
        handle.write('\n')

    # Write out the user's notes
    for note in category.notes:
        handle.write(f'{note}\n')
