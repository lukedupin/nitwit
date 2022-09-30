import os, sys, re, glob

from pathlib import Path
from datetime import datetime

from nitwit.storage.parser import parse_content
from nitwit.helpers import util


class List:
    def __init__(self):
        self.title = None
        self.name = None
        self.date = None
        self.owner = None
        self.active = None
        self.completed = None
        self.ticket_uids = []
        self.notes = []


### Bulk commands for parsing and writing to the filesystem

# Parse all lists
def import_lists( settings, filter_owners=None, filter_names=None, active=None, completed=None ):
    lists = []

    # Read in all the lists
    for file in glob.glob(f'{settings["directory"]}/lists/**/**.md', recursive=True):
        info = re.split('/', file)
        name = info[-2].lower()
        owner = re.sub( r'[.]md$', '', info[-1].lower() )
        if filter_owners is not None and owner not in filter_owners:
            continue

        with open(file) as handle:
            if filter_owners is not None and owner not in filter_owners:
                continue
            if filter_names is not None and name not in filter_names:
                continue

            if (lst := parse_list( settings, handle, name, owner )) is not None:
                if active is not None and util.xbool(lst.active) != active:
                    continue
                if completed is not None and util.xbool(lst.completed) != completed:
                    continue
                lists.append( lst )

    return lists


# Export all lists
def export_lists( settings, lists ):
    # Setup the base tags
    dir = f'{settings["directory"]}/lists'
    Path(dir).mkdir(parents=True, exist_ok=True)

    for lst in lists:
        list_dir = f'{dir}/{lst.name}'
        Path(list_dir).mkdir(parents=True, exist_ok=True)

        with open(f"{list_dir}/{lst.owner}.md", 'w') as handle:
            export_list( settings, handle, lst )


### Individual parse/export commands

# Parse list
def parse_list( settings, handle, name=None, owner=None ):
    if (parser := parse_content( handle )) is None and \
       (name is None or owner is None):
        return None

    lst = List()

    # Store the name
    lst.name = name
    if name is None and parser.name is not None:
        lst.name = parser.name
    if lst.name is None:
        return None

    # Store the owner
    lst.owner = owner
    if owner is None and len(parser.owners) > 0:
        lst.owner = parser.owners[0]
    if lst.owner is None:
        return None

    # store teh variables
    for key in ('active', 'completed'):
        if (value := parser.variables.get(key)) is not None:
            lst.__setattr__(key, util.xbool(value))

    lst.filename = handle.name
    lst.title = util.xstr(parser.title)
    lst.date = parser.date
    lst.notes = parser.notes
    lst.ticket_uids = parser.ticket_uids

    return lst


# Write out a spring file
def export_list( settings, handle, lst, title_lookup={} ):
    if lst.title is not None:
        handle.write(f'# @{lst.owner} {util.xstr(lst.title)[:64]}\n')
    else:
        handle.write(f'# @{lst.owner}\n')
    handle.write('\n')

    # Write out the subitems
    if len(lst.ticket_uids) > 0:
        for ticket_uid in lst.ticket_uids:
            active = '' if ticket_uid.active else '~~'
            if (title := title_lookup.get(ticket_uid.uid)) is not None:
                handle.write(f'+ {active}:{ticket_uid.uid} {title[:64]}{active}\n')
            else:
                handle.write(f'+ {active}:{ticket_uid.uid}{active}\n')
        handle.write("\n")

    else:
        handle.write("+ \n\n")

    # Write out the user's notes
    for note in lst.notes:
        handle.write(f'{note}\n')
