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
        self.parent = ""
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


def find_category_by_name( settings, name, show_invisible=False ):
    # Fastest, look for a specific one
    categories = import_categories( settings, filter_names=[util.xstr(name)], show_invisible=True )
    if len(categories) == 1:
        return categories[0]

    # Attempt an index lookup
    idx = util.xint(name) - 1
    if idx < 0:
        return None

    # Slower, pulling in all categories and picking by index after sorting
    categories = import_categories( settings, show_invisible=show_invisible )
    if idx < len(categories):
        return categories[idx]

    return None


def category_parent_chain( parent, categories ):
    chain = []
    while parent is not None:
        next_parent = None

        # Look for a matching parent
        for cat in categories:
            if cat.name == parent:
                next_parent = cat.parent
                chain.insert( 0, cat )
                break
        parent = next_parent

    return chain


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
                if show_invisible or category.visible:
                    categories.append( category )
    categories = sorted( categories, key=lambda x: x.name.lower() )

    # Build the parent chain
    sorted_cat = []
    while len(categories) > 0:
        longest_chain = []
        for cat in categories:
            chain = category_parent_chain( cat.name, categories )
            if len(longest_chain) < len(chain):
                longest_chain = chain

        if len(longest_chain) <= 0:
            break

        # Remove matches
        for idx in reversed(range(len(categories))):
            if any([categories[idx].name == x.name for x in longest_chain]):
                del categories[idx]

        # Add the longest chain and continue to the next one
        sorted_cat += longest_chain

    return sorted_cat


# Export all categories
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
def parse_category( settings, handle, name=None ):
    if (parser := parse_content( handle )) is None and name is None:
        return None

    category = Category()
    category.filename = handle.name
    category.notes = parser.notes
    category.accepted = util.xbool(parser.variables.get('accepted'))
    category.visible = util.xbool(parser.variables.get('visible'))
    category.parent = util.xstr(parser.variables.get('parent'))

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
    new_line = None
    if include_name:
        new_line = handle.write(f'> ^{category.name}\n')
    if category.accepted is not None:
        new_line = handle.write(f'> $accepted={"true" if category.accepted else "false"}\n')
    if category.visible is not None:
        new_line = handle.write(f'> $visible={"true" if category.visible else "false"}\n')
    if category.parent is not None:
        new_line = handle.write(f'> $parent={category.parent}\n')
    if new_line is not None:
        handle.write('\n')

    # Write out the user's notes
    for note in category.notes:
        handle.write(f'{note}\n')
