from datetime import datetime

from nitwit.storage import categories as categories_mod
from nitwit.storage.parser import parse_content
from nitwit.helpers import settings as settings_mod
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

    def has_content(self):
        return self.uid is not None or self.title is not None


def generate_uid( base_dir ):
    for _ in range(32):
        uid = hex(random.randint(0, 1048576) & 0xFFFFF)[2:].rjust(5, '0')
        if not os.path.exists(f'{base_dir}/{uid}.md'):
            return uid

    return None


### Bulk commands for parsing and writing to the filesystem


def find_ticket_by_uid( settings, uid ):
    # Fastest, look for a specific one
    tickets = import_tickets( settings, filter_uids=[util.xstr(uid)] )
    if len(tickets) == 1:
        return tickets[0]

    # Attempt an index lookup
    idx = util.xint(uid) - 1
    if idx < 0:
        return None

    # Slower, pulling in all tags and picking by index after sorting
    tickets = import_tickets( settings )
    if idx < len(tickets):
        return tickets[idx]

    return None


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

    return sorted( tickets, key=lambda x: (x.category.lower(), x.title.lower()) )


# Export all tickets
def export_tickets( settings, tickets ):
    new_count = 0
    update_count = 0

    repo = settings_mod.git_repo()

    # Setup the base ticket directory
    dir = f'{settings["directory"]}/tickets'
    Path(dir).mkdir(parents=True, exist_ok=True)

    for ticket in tickets:
        if ticket.uid is None:
            ticket.uid = generate_uid( settings['directory'] )
            new_count += 1

        filename = f"{dir}/{ticket.uid}.md"

        # Hash before we write
        before = util.sha256sum( filename )
        with open(filename, 'w') as handle:
            export_ticket( settings, handle, ticket )

        # Check if anything changed
        if before != util.sha256sum( filename ):
            update_count += 1

        repo.index.add([filename])

    return new_count, update_count


### Individual parse/export commands


# Pass in an open filehandle and we'll generate a ticket
def parse_ticket( settings, handle, uid=None ):
    if (parser := parse_content( handle )) is None:
        return None

    return to_ticket( settings, parser, uid, handle.name )


def to_ticket( settings, parser, uid=None, filename=None ):
    # Make sure we have valid content
    if parser is None or not parser.has_content():
        return None

    ticket = Ticket()

    # Store the name
    ticket.uid = uid
    if uid is None and parser.uid is not None:
        ticket.uid = parser.uid

    # store teh variables
    for key in ('priority', 'difficulty'):
        if (value := parser.variables.get(key)) is not None:
            ticket.__setattr__(key, util.xint(value))

    ticket.filename = filename
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
        if ticket.uid is None:
            ticket.uid = generate_uid( settings['directory'] )
        ret = handle.write(f'> :{ticket.uid}\n')
    if ticket.category is not None:
        ret = handle.write(f'> ^{categories_mod.safe_category( settings, ticket.category )}\n')
    if len(ticket.owners) > 0:
        owner_dict = {f"@{x}": True for x in ticket.owners}
        ret = handle.write(f'> {" ".join(owner_dict.keys())}\n')
    if len(ticket.tags) > 0:
        tags_dict = {f"#{x}": True for x in ticket.tags}
        ret = handle.write(f'> {" ".join(tags_dict.keys())}\n')
    for key in ('priority', 'difficulty'):
        if (value := ticket.__getattribute__(key)) is not None:
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
