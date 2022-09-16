import os, sys, re, glob
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


# Parse all tickets
def all_tickets( dir, filter_uids=None ):
    tickets = []

    # Read in all the tickets
    for file in glob.glob(f'{dir}_tickets/**/meta.md', recursive=True):
        uid = re.split('/', file)[-2].lower()
        with open(file) as handle:
            if filter_uids is not None and uid not in filter_uids:
                continue

            if (ticket := parse_ticket( handle, uid )) is not None:
                tickets.append( ticket )

    return tickets


# Parse all sprints
def all_sprints( dir, filter_owners=None ):
    sprints = []

    # Read in all the sprints
    for file in glob.glob(f'{dir}_sprints/**/meta.md', recursive=True):
        owner = re.split('/', file)[-2].lower()
        with open(file) as handle:
            if filter_owners is not None and owner not in filter_owners:
                continue

            if (sprint := parse_sprint( handle, owner )) is not None:
                sprints.append( sprint )

    return sprints


# Parse all sprints
def latest_sprints( dir, filter_owners=None ):
    sprints = []

    latest_dir = None
    latest_unix = None

    # Read in all the sprints
    for file in glob.glob(f'{dir}_sprints/**/**.md', recursive=True):
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


# Parse all tags
def all_tags( dir ):
    tags = []

    # Read in all the tags
    for file in glob.glob(f'{dir}_tags/**.md', recursive=True):
        info = re.split('/', file)
        name = re.sub( r'[.]md$', '', info[-1].lower() )
        with open(file) as handle:
            if (tag := parse_tag( handle, name )) is not None:
                tags.append( tag )

    return tags


# Parse all tags
def all_categories( dir ):
    categories = []

    # Read in all the categories
    for file in glob.glob(f'{dir}_categories/**.md', recursive=True):
        info = re.split('/', file)
        name = re.sub( r'[.]md$', '', info[-1].lower() )
        with open(file) as handle:
            if (category := parse_category( handle, name )) is not None:
                categories.append( category )

    return categories


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
                handle.write(f'+ {si.name}\r\n')
            else:
                handle.write(f'+ ~~{si.name}~~\r\n')
            # Need to have sub item notes in here also
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
