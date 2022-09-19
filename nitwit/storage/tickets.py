from datetime import datetime

from nitwit.helpers import util

from pathlib import Path
import os, sys, re, glob, random


class Ticket:
    def __init__(self, filename, uid, category):
        self.filename = filename
        self.uid = uid
        self.title = None
        self.category = category
        self.priority = None
        self.owners = []
        self.tags = []
        self.subitems = []
        self.notes = []


class SubItem:
    def __init__(self, clean):
        self.active = not re.search(r'^~~', clean) or not re.search(r'~~$', clean)
        self.name = re.sub('~~$', '', re.sub('^~~', '', clean))
        self.notes = []


### Bulk commands for parsing and writing to the filesystem

# Parse all tickets
def import_tickets( settings, filter_uids=None ):
    tickets = []

    # Read in all the tickets
    for file in glob.glob(f'{settings["directory"]}/_tickets/**/meta.md', recursive=True):
        uid = re.split('/', file)[-2].lower()
        with open(file) as handle:
            if filter_uids is not None and uid not in filter_uids:
                continue

            if (ticket := parse_ticket( settings, handle, uid )) is not None:
                tickets.append( ticket )

    return sorted( tickets, key=lambda x: x.title )


# Export all tickets
def export_tickets( settings, tickets ):
    new_count = 0
    update_count = 0

    for ticket in tickets:
        if ticket.uid is None:
            ticket.uid = generate_uid( settings['directory'] )
            new_count += 1

        dir = f"{settings['directory']}/_tickets/{ticket.uid}"
        Path(dir).mkdir(parents=True, exist_ok=True)
        filename = f"{dir}/meta.md"

        # Hash before we write
        before = util.sha256sum( filename )
        with open(f"{dir}/meta.md", 'w') as handle:
            export_ticket( handle, ticket )

        # Check if anything changed
        if before != util.sha256sum( filename ):
            update_count += 1

    return new_count, update_count


### Individual parse/export commands

def generate_uid( base_dir ):
    for _ in range(32):
        uid = hex(random.randint(0, 1048576) & 0xFFFFF)[2:]
        if not os.path.exists(f'{base_dir}/{uid}'):
            return uid

    return None


# Pass in an open filehandle and we'll generate a ticket
def parse_ticket( settings, handle, uid=None, category=None ):
    if category is None:
        category = settings['defaultcategory']
    ticket = Ticket( handle.name, uid, category )

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

        # Store a new ticket?
        if ticket.title is None and (ret := re.search(r'^\w*# (.*$)', line)) is not None:
            ticket.title = ret.group(1)

        # Setup the sub topics, they are numbers
        elif (ret := re.search(r'^\w*[0-9]+[.][\t ]+(.*)$', line)):
            ticket.subitems.append( SubItem( ret.group(1)))

        # Find an account modifier
        elif re.search(r'^>', line):
            for mod in re.split(' ', line):
                if len(mod) <= 1:
                    continue

                if mod[0] == '$' and ticket.uid is None:
                    ticket.uid = mod[1:]

                elif mod[0] == '^':
                    ticket.category = mod[1:]
                elif mod[0] == '!':
                    ticket.priority = util.xint( mod[1:] )
                elif mod[0] == '@':
                    ticket.owners.append( mod[1:] )
                elif mod[0] == '#':
                    ticket.tags.append( mod[1:] )

        # Add in all the chatter
        elif re.search(r'^\w*$', line) is None:
            ticket.notes.append( line )

    return ticket if ticket.title is not None else None


# Pass in an open filehandle and we'll generate a ticket
def export_ticket( handle, ticket, include_uid=False ):
    handle.write(f'# {ticket.title}\r\n\r\n')

    # Write out the configuration options
    ret = None
    if include_uid:
        ret = handle.write(f'> ${ticket.uid}\r\n')
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
    if len(ticket.notes) > 0:
        for note in ticket.notes:
            handle.write(f'{note}\r\n')
        handle.write("\r\n")
