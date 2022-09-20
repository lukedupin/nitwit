import os, sys, re, glob

from pathlib import Path
from datetime import datetime

from nitwit.helpers import util


class Sprint:
    def __init__(self, date, owner):
        self.title = None
        self.date = date
        self.owner = owner
        self.ticket_uids = []
        self.notes = []


### Bulk commands for parsing and writing to the filesystem

# Return the latest sprint date
def get_latest_sprint_date( settings ):
    latest_dir = None
    latest_unix = None

    # Read in all the sprints
    for file in glob.glob(f'{settings["directory"]}_sprints/**/'):
        info = re.split('/', file)
        unix = util.timeToUnix( datetime.strptime( info[-2], '%Y-%m-%d'))
        if util.xint( latest_unix) < unix:
            latest_dir = '/'.join( info[0:-1])
            latest_unix = unix

    return latest_dir


# Parse all sprints
def import_sprints( settings, filter_owners=None ):
    sprints = []

    # Read in all the sprints
    for file in glob.glob(f'{settings["directory"]}_sprints/**/meta.md', recursive=True):
        owner = re.split('/', file)[-2].lower()
        with open(file) as handle:
            if filter_owners is not None and owner not in filter_owners:
                continue

            if (sprint := parse_sprint( handle, owner )) is not None:
                sprints.append( sprint )

    return sprints


# Parse all sprints
def import_latest_sprints( settings, filter_owners=None ):
    sprints = []

    # Is there no directory?
    if (latest_dir := get_latest_sprint_date( settings )) is None:
        return sprints

    # Read in all the sprints
    for file in glob.glob(f'{latest_dir}/**.md', recursive=True):
        info = re.split('/', file)
        owner = re.sub( r'[.]md$', '', info[-1].lower() )
        date = info[-2].lower()
        with open(file) as handle:
            if filter_owners is not None and owner not in filter_owners:
                continue

            if (sprint := parse_sprint( handle, date, owner )) is not None:
                sprints.append( sprint )

    return sprints


# Export all sprints
def export_sprints( settings, sprints ):
    for sprint in sprints:
        dir = f"{settings['directory']}/{sprint.date}"
        Path(dir).mkdir(parents=True, exist_ok=True)

        with open(f"{dir}/{sprint.owner}.md", 'w') as handle:
            export_sprint( handle, sprint )


### Individual parse/export commands

# Parse sprint
def parse_sprint( handle, date, owner ):
    sprint = Sprint( date, owner )

    # Load up the files and go!
    last_pos = handle.tell()
    while (line := handle.readline()) is not None and \
            (new_last_pos := handle.tell()) != last_pos:
        last_pos = new_last_pos

        # Strip out the line
        line = line.rstrip()

        # Did we reach the end of a multi read ticket?
        if re.search(r'^======', line) is not None:
            break

        # Auto break processing
        if re.search(r'^####', line) is not None:
            return None

        # Store the title!
        if (ret := re.search(r'^# @([0-9a-zA-Z]+)[ ]*(.*)', line)) is not None:
            sprint.owner = ret.group(1)
            sprint.title = ret.group(2)

        # Setup the sub topics
        elif (ret := re.search(r'^\w*[*+-][\t ]+[$](.*)$', line)):
            sprint.ticket_uids.append( ret.group(1).lower())

        # Add in all the chatter
        elif re.search(r'^\w*$', line) is None:
            sprint.notes.append( line )

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
        handle.write("+ \n")
        handle.write("\n")

    # Write out the user's notes
    for note in sprint.notes:
        handle.write(f'{note}\n')
