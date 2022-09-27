from datetime import datetime

from nitwit.helpers import util

from pathlib import Path
import os, sys, re, glob, random


class Parser:
    def __init__(self):
        self.uid = None
        self.title = None
        self.category = None
        self.priority = None
        self.owners = []
        self.tags = []
        self.subitems = []
        self.notes = []

    def has_content(self):
        return self.uid is not None or \
               self.title is not None or \
               self.category is not None or \
               self.priority is not None or \
               len(self.owners) > 0 or \
               len(self.tags) > 0 or \
               len(self.subitems) > 0 or \
               len(self.notes) > 0


class SubItem:
    def __init__(self, clean):
        self.active = not re.search(r'^~~', clean) or not re.search(r'~~$', clean)
        self.name = re.sub('~~$', '', re.sub('^~~', '', clean))
        self.notes = []


def generate_uid( base_dir ):
    for _ in range(32):
        uid = hex(random.randint(0, 1048576) & 0xFFFFF)[2:].rjust(5, '0')
        if not os.path.exists(f'{base_dir}/{uid}'):
            return uid

    return None


# Pass in an open filehandle and we'll generate a ticket
def parse_content( handle ):
    result = Parser()

    # Load up the files and go!
    new_last_pos = handle.tell()
    while True:
        # Create a line, and quit if the line didn't read correctly
        last_pos = new_last_pos
        if (line := handle.readline()) is None or \
           (new_last_pos := handle.tell()) == last_pos:
            break

        # Strip out the line
        line = line.rstrip()

        print( line )

        # Quit now, if this is the first line, give no chance to read again
        if re.search(r'^======', line) is not None:
            break

        # Store a new ticket?
        if (ret := re.search(r'^\s*# (.*$)', line)) is not None:
            if result.has_content():
                handle.seek(last_pos)
                break

            result.title = ret.group(1)

        # Setup the sub topics, they are numbers
        elif (ret := re.search(r'^\s*[0-9]+[.][\s]+(.*)$', line)):
            result.subitems.append( SubItem( ret.group(1)))

        # Find an account modifier
        elif re.search(r'^>', line):
            for mod in re.split(' ', line):
                if len(mod) <= 1:
                    continue

                if mod[0] == '$' and result.uid is None:
                    result.uid = mod[1:]

                elif mod[0] == '^':
                    result.category = mod[1:]
                elif mod[0] == '!':
                    result.priority = util.xint( mod[1:] )
                elif mod[0] == '@':
                    result.owners.append( mod[1:] )
                elif mod[0] == '#':
                    result.tags.append( mod[1:] )

        # Add in all the chatter
        elif re.search(r'^\s*$', line) is None:
            result.notes.append( line )

    return result