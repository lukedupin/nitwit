from datetime import datetime

from nitwit.storage import categories as categories_mod
from nitwit.storage.parser import parse_content
from nitwit.helpers import util

from pathlib import Path
import os, sys, re, glob, random


class Ticket:
    def __init__(self):
        self.filename = None
        self.uid = None
        self.title = None
        self.category = None
        self.priority = None
        self.difficulty = None
        self.owners = []
        self.tags = []
        self.subitems = []
        self.notes = []


def generate_uid( base_dir ):
    for _ in range(32):
        uid = hex(random.randint(0, 1048576) & 0xFFFFF)[2:].rjust(5, '0')
        if not os.path.exists(f'{base_dir}/{uid}.md'):
            return uid

    return None


### Bulk commands for parsing and writing to the filesystem

# Parse all tickets
def import_tickets( settings, filter_uids=None ):
    tickets = []

    # Read in all the tickets
    for file in glob.glob(f'{settings["directory"]}/tickets/**.md', recursive=True):
        info = re.split('/', file)
        uid = re.sub( r'[.]md$', '', info[-1].lower() )
        if filter_uids is not None and uid not in filter_uids:
            continue

        with open(file) as handle:
            if (ticket := parse_ticket( settings, handle, uid )) is not None:
                tickets.append( ticket )

    return sorted( tickets, key=lambda x: x.title.lower() )


# Export all tickets
def export_tickets( settings, tickets ):
    new_count = 0
    update_count = 0

    for ticket in tickets:
        if ticket.uid is None:
            ticket.uid = generate_uid( settings['directory'] )
            new_count += 1

        dir = f'{settings["directory"]}/tickets'
        Path(dir).mkdir(parents=True, exist_ok=True)
        filename = f"{dir}/{ticket.uid}.md"

        # Hash before we write
        before = util.sha256sum( filename )
        with open(filename, 'w') as handle:
            export_ticket( settings, handle, ticket )

        # Check if anything changed
        if before != util.sha256sum( filename ):
            update_count += 1

    return new_count, update_count


### Individual parse/export commands


# Pass in an open filehandle and we'll generate a ticket
def parse_ticket( settings, handle, uid=None ):
    if (parser := parse_content( handle )) is None and uid is None:
        return None

    ticket = Ticket()

    # Store the name
    ticket.uid = uid
    if uid is None and parser.uid is not None:
        ticket.uid = parser.uid
    if ticket.uid is None:
        return None

    # store teh variables
    for key in ('priority', 'difficulty'):
        if (value := parser.variables.get(key)) is not None:
            ticket.__setattr__(key, util.xint(value))

    ticket.filename = handle.name
    ticket.title = util.xstr(parser.title)
    ticket.category = categories_mod.safe_category( settings, parser.category )

    ticket.subitems = parser.subitems
    ticket.notes = parser.notes
    ticket.owners = parser.owners
    ticket.tags = parser.tags

    return ticket


# Pass in an open filehandle and we'll generate a ticket
def export_ticket( settings, handle, ticket, include_uid=False ):
    handle.write(f'# {ticket.title}\n\n')

    # Write out the configuration options
    ret = None
    if include_uid:
        ret = handle.write(f'> ${ticket.uid}\n')
    if ticket.category is not None:
        ret = handle.write(f'> ^{categories_mod.safe_category( settings, ticket.category )}\n')
    if len(ticket.owners) > 0:
        ret = handle.write(f'> @{" @".join(ticket.owners)}\n')
    if len(ticket.tags) > 0:
        ret = handle.write(f'> #{" #".join(ticket.tags)}\n')
    for key in ('priority', 'difficulty'):
        if (value := handle.__getattribute__(key)) is not None:
            ret = handle.write(f'> ${key}={value}\n')
    if ret is not None:
        handle.write('\n')

    # Write out the subitems
    if len(ticket.subitems) > 0:
        for si in ticket.subitems:
            if si.active:
                handle.write(f'1. {si.name}\n')
            else:
                handle.write(f'1. ~~{si.name}~~\n')

            for note in si.notes:
                handle.write(f'{note}\n')
        handle.write("\n")

    # Write out the user's notes
    if len(ticket.notes) > 0:
        for note in ticket.notes:
            handle.write(f'{note}\n')
        handle.write("\n")
