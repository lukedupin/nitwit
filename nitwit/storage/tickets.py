from datetime import datetime

from nitwit.helpers import util

from pathlib import Path
import os, sys, re, glob, random


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


class SubItem:
    def __init__(self, clean):
        self.active = not re.search(r'^~~', clean) or not re.search(r'~~$', clean)
        self.name = re.sub('~~$', '', re.sub('^~~', '', clean))
        self.notes = []


### Bulk commands for parsing and writing to the filesystem

# Parse all tickets
def import_tickets( base_dir, filter_uids=None ):
    tickets = []

    # Read in all the tickets
    for file in glob.glob(f'{base_dir}/_tickets/**/meta.md', recursive=True):
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


### Individual parse/export commands

def generate_uid( base_dir ):
    for _ in random(32):
        uid = hex(random.randint(0, 1048576) & 0xFFFFF)[2:]
        if not os.path.exists(f'{base_dir}/{uid}'):
            return uid

    return None


# Pass in an open filehandle and we'll generate a ticket
def parse_ticket( handle, uid=None ):
    ticket = Ticket( uid )

    # Load up the files and go!
    last_pos = handle.tell()
    while (line := handle.readline()) is not None:
        line = line.rstrip()

        # Store a new ticket?
        if (ret := re.search(r'^\w*# (.*$)', line)) is not None:
            # Are we starting another ticket? Reset the handler and exit
            if ticket.title is not None:
                handle.seek( last_pos )
                break

            # Store the title
            ticket.title = ret.group(1)

        # Store the last position
        if last_pos == handle.tell():
            break
        last_pos = handle.tell()

        # Don't start until we have a title, this removes white space
        if ticket.title is None:
            continue

        # Setup the sub topics, they are numbers
        if (ret := re.search(r'^\w*[0-9]+[.][\t ]+(.*)$', line)):
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
        else:
            ticket.notes.append( line )

    return ticket


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
    for note in ticket.notes:
        handle.write(f'{note}\r\n')