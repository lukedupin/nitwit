import os, sys, re, glob

from pathlib import Path
from datetime import datetime

from nitwit.helpers import util


class List:
    def __init__(self):
        self.title = None
        self.date = None
        self.owner = None
        self.active = None
        self.completed = None
        self.ticket_uids = []
        self.notes = []


### Bulk commands for parsing and writing to the filesystem

# Parse all lists
def import_lists( settings, filter_owners=None, active=None, completed=None ):
    lists = []

    # Read in all the lists
    for file in glob.glob(f'{settings["directory"]}/lists/**/**.md', recursive=True):
        info = re.split('/', file)
        owner = re.sub( r'[.]md$', '', info[-2].lower() )
        name = re.sub( r'[.]md$', '', info[-1].lower() )
        if filter_owners is not None and owner not in filter_owners:
            continue

        with open(file) as handle:
            if filter_owners is not None and owner not in filter_owners:
                continue

            if (sprint := parse_sprint( handle, owner )) is not None:
                lists.append( sprint )

    return lists


# Parse all lists
def import_latest_lists( settings, filter_owners=None ):
    lists = []

    # Is there no directory?
    if (latest_dir := get_latest_sprint_date( settings )) is None:
        return lists

    # Read in all the lists
    for file in glob.glob(f'{latest_dir}/**.md', recursive=True):
        info = re.split('/', file)
        owner = re.sub( r'[.]md$', '', info[-1].lower() )
        date = info[-2].lower()
        with open(file) as handle:
            if filter_owners is not None and owner not in filter_owners:
                continue

            if (sprint := parse_sprint( handle, date, owner )) is not None:
                lists.append( sprint )

    return lists


# Export all lists
def export_lists( settings, lists ):
    if (latest_dir := get_latest_sprint_date( settings )) is None:
        latest_dir = f'{settings["directory"]}/_lists/{util.dateToStr()}'

    for sprint in lists:
        Path(latest_dir).mkdir(parents=True, exist_ok=True)

        with open(f"{latest_dir}/{sprint.owner}.md", 'w') as handle:
            export_sprint( handle, sprint )


### Individual parse/export commands

# Parse sprint
def parse_sprint( handle, date, owner ):
    sprint = Sprint( date, owner )

    # Load up the files and go!
    first_line = True
    new_last_pos = handle.tell()
    while True:
        # Create a line, and quit if the line didn't read correctly
        last_pos = new_last_pos
        if (line := handle.readline()) is None or \
           (new_last_pos := handle.tell()) == last_pos:
            break

        # Strip out the line
        line = line.rstrip()

        # Quit now, if this is the first line, give no chance to read again
        if re.search(r'^####', line) is not None:
            handle.seek(last_pos)
            if first_line:
                return None
            else:
                break
        first_line = False

        # Store the title!
        if (ret := re.search(r'^# @([0-9a-zA-Z]+)\s*(.*)', line)) is not None:
            if sprint.owner is not None and sprint.owner != ret.group(1):
                handle.seek( last_pos )
                break

            sprint.owner = ret.group(1)
            sprint.title = ret.group(2)

        # Setup the sub topics
        elif (ret := re.search(r'^\s*[*+-]\s+[$]([^\s]+)', line)):
            sprint.ticket_uids.append( ret.group(1).lower())

        # Add in all the chatter
        #elif re.search(r'^\s*$', line) is None:
        #    sprint.notes.append( line )

    return sprint if sprint.owner is not None else None


# Write out a spring file
def export_sprint( handle, sprint, title_lookup={} ):
    if sprint.title is not None:
        handle.write(f'# {sprint.owner} {sprint.title[:64]}\n')
    else:
        handle.write(f'# @{sprint.owner}\n')
    handle.write('\n')

    # Write out the subitems
    if len(sprint.ticket_uids) > 0:
        for uid in sprint.ticket_uids:
            if (title := title_lookup.get(uid)) is not None:
                handle.write(f'+ ${uid} {title[:64]}\n')
            else:
                handle.write(f'+ ${uid}\n')
        handle.write("\n")

    else:
        handle.write("+ \n\n")

    # Write out the user's notes
    #for note in sprint.notes:
    #    handle.write(f'{note}\n')
