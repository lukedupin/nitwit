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

# Parse all sprints
def import_sprints( base_dir, filter_owners=None ):
    sprints = []

    # Read in all the sprints
    for file in glob.glob(f'{base_dir}_sprints/**/meta.md', recursive=True):
        owner = re.split('/', file)[-2].lower()
        with open(file) as handle:
            if filter_owners is not None and owner not in filter_owners:
                continue

            if (sprint := parse_sprint( handle, owner )) is not None:
                sprints.append( sprint )

    return sprints


# Parse all sprints
def import_latest_sprints( base_dir, filter_owners=None ):
    sprints = []

    latest_dir = None
    latest_unix = None

    # Read in all the sprints
    for file in glob.glob(f'{base_dir}_sprints/**/**.md', recursive=True):
        info = re.split('/', file)
        unix = util.timeToUnix( datetime.strptime( info[-2], '%Y-%m-%d'))
        if util.xint( latest_unix) < unix:
            latest_dir = '/'.join( info[0:-1])
            latest_unix = unix

    if latest_dir is None:
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
def export_sprints( base_dir, sprints ):
    for sprint in sprints:
        dir = f"{base_dir}/{sprint.date}"
        Path(dir).mkdir(parents=True, exist_ok=True)

        with open(f"{dir}/{sprint.owner}.md", 'w') as handle:
            export_sprint( handle, sprint )


### Individual parse/export commands

# Parse sprint
def parse_sprint( handle, date, owner ):
    sprint = Sprint( date, owner )

    # Load up the files and go!
    for idx, line in enumerate( handle.readlines()):
        line = line.rstrip()

        # Store the title!
        if idx == 0 and sprint.title is None and \
           (ret := re.search(r'^# (.*$)', line)) is not None:
            sprint.title = ret.group(1)

        # Setup the sub topics
        elif (ret := re.search(r'^\w*[*+-][\t ]+[$](.*)$', line)):
            sprint.ticket_uids.append( ret.group(1).lower())

        # Add in all the chatter
        else:
            sprint.notes.append( line )

    return sprint


# Write out a spring file
def export_sprint( handle, sprint ):
    if sprint.title is not None:
        handle.write(f'# {sprint.title}\r\n')
        handle.write('\r\n')

    # Write out the subitems
    if len(sprint.ticket_uids) > 0:
        for uid in sprint.ticket_uids:
            handle.write(f'* ${uid}\r\n')
        handle.write("\r\n")

    # Write out the user's notes
    for note in sprint.notes:
        handle.write(f'{note}\r\n')
