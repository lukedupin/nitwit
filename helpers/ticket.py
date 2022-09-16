import os, sys, re, glob

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
        self.media = []


class Subitem:
    def __init__(self, active, name):
        self.active = active
        self.name = name


# Parse all tickets
def all_tickets( dir ):
    tickets = []

    # Read in all the tickets
    for file in glob.glob(f'{dir}/**/meta.md', recursive=True):
        dirs = re.split('/', file)
        with open(file) as handle:
            if (ticket := parse( handle, dirs[-2].lower())) is not None:
                tickets.append( ticket )

    return tickets


# Pass in an open filehandle and we'll generate a ticket
def parse( handle, uid ):
    ticket = Ticket( uid )

    # Load up the files and go!
    for line in handle.readlines():
        line = line.rstrip()

        # Store the title!
        if ticket.title is None and (ret := re.search(r'^# (.*$)', line)) is not None:
            ticket.title = ret.group(1)
            print(ticket.title)

        # Setup the sub topics
        if (ret := re.search(r'^\w*[0-9]+[.][\t ]*(.*)$', line)):
            clean = ret.group(1)
            active = not re.search(r'^~~', clean) or not re.search(r'~~$', clean)
            si = Subitem( active, re.sub( '~~$', '', re.sub('^~~', '', clean )))
            ticket.subitems.append( si )
            print(f'Adding subtask: {si.name} {"True" if si.active else "False"}')

        # Find an account modifier
        elif re.search(r'^>', line):
            for mod in re.split(' ', line):
                if len(mod) <= 1:
                    continue

                print(f'    {mod}')
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
            ticket.media.append( line )

    return ticket