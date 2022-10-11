import os, sys, re, glob

from pathlib import Path
from datetime import datetime

from nitwit.storage.parser import parse_content
from nitwit.helpers import util


class List:
    def __init__(self):
        self.title = None
        self.name = None
        self.owner = None
        self.date = None
        self.active = True
        self.ticket_uids = []
        self.notes = []


### Bulk commands for parsing and writing to the filesystem

def find_lst_by_name( settings, name, filter_owners=None, active=True):
    # Fastest, look for a specific one
    lists = import_lists( settings,
                          filter_names=[util.xstr(name)],
                          filter_owners=filter_owners,
                          active=active )
    if len(lists) == 1:
        return lists[0]

    # Attempt an index lookup
    idx = util.xint(name) - 1
    if idx < 0:
        return None

    # Slower, pulling in all tags and picking by index after sorting
    lists = import_lists( settings, filter_owners=filter_owners, active=active )
    if idx < len(lists):
        return lists[idx]

    return None


# Parse all lists
def import_lists( settings, filter_owners=None, filter_names=None, active=True ):
    lists = []

    # Read in all the lists
    for file in glob.glob(f'{settings["directory"]}/lists/**/**.md', recursive=True):
        info = re.split('/', file)
        name = info[-2].lower()
        owner = re.sub( r'[.]md$', '', info[-1].lower() )
        if filter_names is not None and name not in filter_names:
            continue

        with open(file) as handle:
            if filter_owners is not None and owner not in filter_owners:
                continue

            if (lst := parse_list( settings, handle, name, owner )) is None:
                continue

            if active is not None and util.xbool(lst.active) != active:
                continue

            lists.append( lst )

    return sorted( lists, key=lambda x: (not x.active, x.name) )


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
    if name is None and parser.list is not None:
        lst.name = parser.list
    if lst.name is None:
        return None

    # Store the owner
    lst.owner = owner
    if owner is None and len(parser.owners) > 0:
        lst.owner = parser.owners[0]
    if lst.owner is None:
        return None

    # store teh variables
    for key in ('active', ):
        if (value := parser.variables.get(key)) is not None:
            lst.__setattr__(key, util.xbool(value))
    for key in ('date', ):
        if (value := parser.variables.get(key)) is not None:
            lst.__setattr__(key, util.xstr(value))

    lst.filename = handle.name
    lst.title = util.xstr(parser.title)
    lst.notes = parser.notes
    lst.ticket_uids = parser.ticket_uids

    return lst


# Write out a spring file
def export_list( settings, handle, lst, title_lookup={}, include_name=False ):
    if lst.title is not None:
        handle.write(f'# {util.xstr(lst.title)[:64]}\n')
    else:
        handle.write(f'# {util.xstr(lst.name)}\n')
    handle.write('\n')

    # Write out the mods
    if include_name:
        handle.write(f'> %{lst.name}\n')
    if lst.date is not None:
        handle.write(f'> $date={lst.date}\n')
    handle.write(f'> $active={util.xbool(lst.active)}\n\n')

    handle.write(f'> @{lst.owner}\n\n')

    # Write out the subitems
    if len(lst.ticket_uids) > 0:
        for ticket_uid in lst.ticket_uids:
            active = '' if ticket_uid.active else '~~'
            if (title := title_lookup.get(ticket_uid.uid)) is not None:
                handle.write(f'* {active}:{ticket_uid.uid} {title[:64]}{active}\n')
            else:
                handle.write(f'* {active}:{ticket_uid.uid}{active}\n')
        handle.write("\n")

    # Write out the user's notes
    for note in lst.notes:
        handle.write(f'{note}\n')
