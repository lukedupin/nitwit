import os, sys, re

import util


class Ticket:
    def __int__(self, uid):
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


# Pass in an open filehandle and we'll generate a ticket
def parse( handle, uid ):
    ticket = Ticket( uid )

    # Load up the files and go!
    for line in handle.readlines():
        line = line.chomp()

        # Store the title!
        if ticket.title is None and (ret := re.search(r'^# (.*$)', line)) is not None:
            ticket.title = ret.group(1)
            print(ticket.title)

        # Setup the sub topics
        if (ret := re.search(r'^[ ]*([0-9]+[.].*)', line)):
            clean = ret.group(1)
            active = re.search(r'^~~', clean) and re.search(r'~~$', clean)
            si = Subitem( active, re.sub( r'~~$', '', re.sub(r'^~~', '', clean )))
            ticket.subitems.append( active, si )

        # Find an account modifier
        elif re.search(r'^>', line):
            for mod in re.split(r'[ ]+'):
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