import os, sys, re, glob

from pathlib import Path
from datetime import datetime

from helpers import util

class Ticket:
    def __init__(self, uid):
        self.uid = uid
        self.title = None
        self.category = None
        self.priority = None
        self.owners = []
        self.tags = []
        self.subitems = []
        self.notes = []


class Sprint:
    def __init__(self, date, owner):
        self.title = None
        self.date = date
        self.owner = owner
        self.ticket_uids = []
        self.notes = []


class Tag:
    def __init__(self, name):
        self.name = None
        self.title = None
        self.notes = []


class Category:
    def __init__(self, name):
        self.name = None
        self.title = None
        self.notes = []


class Subitem:
    def __init__(self, clean):
        self.active = not re.search(r'^~~', clean) or not re.search(r'~~$', clean)
        self.name = re.sub('~~$', '', re.sub('^~~', '', clean))
        self.notes = []


### Bulk commands for parsing and writing to the filesystem

# Parse all tickets
def import_tickets( base_dir, filter_uids=None ):
    tickets = []

    # Read in all the tickets
    for file in glob.glob(f'{base_dir}_tickets/**/meta.md', recursive=True):
        uid = re.split('/', file)[-2].lower()
        with open(file) as handle:
            if filter_uids is not None and uid not in filter_uids:
                continue

            if (ticket := parse_ticket( handle, uid )) is not None:
                tickets.append( ticket )

    return tickets


# Export all tickets
def export_tickets( base_dir, tickets ):
    for ticket in tickets:
        dir = f"{base_dir}/{ticket.uid}"
        Path(dir).mkdir(parents=True, exist_ok=True)

        with open(f"{dir}/meta.md", 'w') as handle:
            export_ticket( handle, ticket )


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


# Parse all tags
def import_tags( base_dir ):
    tags = []

    # Read in all the tags
    for file in glob.glob(f'{base_dir}_tags/**.md', recursive=True):
        info = re.split('/', file)
        name = re.sub( r'[.]md$', '', info[-1].lower() )
        with open(file) as handle:
            if (tag := parse_tag( handle, name )) is not None:
                tags.append( tag )

    return tags


# Export all sprints
def export_tags( base_dir, tags ):
    for tag in tags:
        dir = f"{base_dir}"
        Path(dir).mkdir(parents=True, exist_ok=True)

        with open(f"{dir}/{tag.name}.md", 'w') as handle:
            export_sprint( handle, tag )


# Parse all tags
def import_categories( base_dir ):
    categories = []

    # Read in all the categories
    for file in glob.glob(f'{base_dir}_categories/**.md', recursive=True):
        info = re.split('/', file)
        name = re.sub( r'[.]md$', '', info[-1].lower() )
        with open(file) as handle:
            if (category := parse_category( handle, name )) is not None:
                categories.append( category )

    return categories


# Export all sprints
def export_categories( base_dir, categories ):
    for category in categories:
        dir = f"{base_dir}"
        Path(dir).mkdir(parents=True, exist_ok=True)

        with open(f"{dir}/{category.name}.md", 'w') as handle:
            export_sprint( handle, category )


### Individual parse/export commands


# Pass in an open filehandle and we'll generate a ticket
def parse_ticket( handle, uid ):
    ticket = Ticket( uid )

    # Load up the files and go!
    for idx, line in enumerate( handle.readlines()):
        line = line.rstrip()

        # Store the title!
        if idx == 0 and ticket.title is None and \
           (ret := re.search(r'^# (.*$)', line)) is not None:
            ticket.title = ret.group(1)

        # Setup the sub topics
        elif (ret := re.search(r'^\w*[0-9]+[.][\t ]+(.*)$', line)):
            ticket.subitems.append( Subitem( ret.group(1)))

        # Find an account modifier
        elif re.search(r'^>', line):
            for mod in re.split(' ', line):
                if len(mod) <= 1:
                    continue

                if mod[0] == '^':
                    ticket.category = mod[1:]
                elif mod[0] == '!':
                    ticket.priority = util.xint( mod[1:] )
                elif mod[0] == '@':
                    ticket.owners.append( mod[1:] )
                elif mod[0] == '#':
                    ticket.tags.append( mod[1:] )

        # Add in all the chatter
        else:
            ticket.notes.append( line )

    return ticket


# Pass in an open filehandle and we'll generate a ticket
def export_ticket( handle, ticket ):
    handle.write(f'# {ticket.title}\r\n\r\n')

    # Write out the configuration options
    ret = None
    if ticket.category is not None:
        ret = handle.write(f'> ^{ticket.category}\r\n')
    if len(ticket.owners) > 0:
        ret = handle.write(f'> @{" @".join(ticket.owners)}\r\n')
    if len(ticket.tags) > 0:
        ret = handle.write(f'> #{" #".join(ticket.tags)}\r\n')
    if ticket.priority is not None:
        ret = handle.write(f'> !{util.xint(ticket.priority)}\r\n')
    if ret is not None:
        handle.write('\r\n')

    # Write out the subitems
    if len(ticket.subitems) > 0:
        for si in ticket.subitems:
            if si.active:
                handle.write(f'1. {si.name}\r\n')
            else:
                handle.write(f'1. ~~{si.name}~~\r\n')

            for note in si.notes:
                handle.write(f'{note}\r\n')
        handle.write("\r\n")

    # Write out the user's notes
    for note in ticket.notes:
        handle.write(f'{note}\r\n')


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


# Parse tags
def parse_tag( handle, name ):
    tag = Tag( name )

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
        handle.write(f'# {tag.title}\r\n')
        handle.write('\r\n')

    # Write out the user's notes
    for note in tag.notes:
        handle.write(f'{note}\r\n')


# Parse tags
def parse_category( handle, name ):
    category = Category( name )

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
