from datetime import datetime

from nitwit.helpers import util

from pathlib import Path
import os, sys, re, glob, random


class Parser:
    def __init__(self):
        self.uid = None
        self.title = None
        self.category = None
        self.list = None
        self.date = None
        self.owners = []
        self.tags = []
        self.subitems = []
        self.notes = []
        self.ticket_uids = []
        self.variables = {}

    def has_content(self):
        return self.uid is not None or \
               self.title is not None or \
               self.category is not None or \
               self.list is not None or \
               self.date is not None or \
               len(self.owners) > 0 or \
               len(self.tags) > 0 or \
               len(self.subitems) > 0 or \
               len(self.notes) > 0 or \
               len(self.ticket_uids) > 0 or \
               len(self.variables) > 0


class TicketUid:
    def __init__(self):
        self.uid = None
        self.active = True

    @staticmethod
    def parse( line ):
        if (ret := re.search(r'[*+-]\s*(~?):(\w+)', line)) is not None:
            tuid = TicketUid()
            tuid.active = ret.group(1) != '~'
            tuid.uid = ret.group(2)
            return tuid

        if (ret := re.search(r'[*+-]\s*~~:(\w+)', line)) is not None:
            tuid = TicketUid()
            tuid.active = False
            tuid.uid = ret.group(1)
            return tuid

        return None


class SubItem:
    def __init__(self):
        self.name = ""
        self.active = True

    @staticmethod
    def parse( line ):
        if (ret := re.search(r'^\s*[0-9]+[.][\s]+(.*)$', line)) is not None:
            clean = ret.group(1)

            sub_item = SubItem()
            sub_item.active = not re.search(r'^~~', clean) or not re.search(r'~~$', clean)
            sub_item.name = re.sub('~~$', '', re.sub('^~~', '', clean))
            return sub_item

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

        # Ignore this
        if re.search(r'^======', line) is not None:
            continue

        # Quit?
        if re.search(r'^######', line) is not None:
            handle.seek(last_pos)
            if result.has_content():
                return result
            else:
                return None

        # Title?
        if (ret := re.search(r'^\s*# (.*$)', line)) is not None:
            if result.has_content():
                handle.seek(last_pos)
                break

            result.title = ret.group(1)

        # Ticket UIDS
        elif (ticket_uid := TicketUid.parse(line)) is not None:
            result.ticket_uids.append( ticket_uid )

        # Setup the sub topics, they are numbers
        elif (sub_item := SubItem.parse( line )) is not None:
            result.subitems.append( sub_item )

        # Find an account modifier
        elif re.search(r'^>', line):
            parse_mods( result, line )

        # Add in all the chatter
        elif re.search(r'^\s*$', line) is None:
            result.notes.append( line )

    return result


def parse_mods( result, line ):
    ary = re.split(r'\s+', line)

    # Iterate through using indexes so we can delete matches as we go through
    for idx in reversed(range(len(ary))):
        mod = ary[idx]
        if len(mod) <= 1:
            continue

        # Detect the modification
        if mod[0] == ':' and result.uid is None:
            result.uid = mod[1:]
        elif mod[0] == '@':
            result.owners.append(mod[1:])
        elif mod[0] == '#':
            result.tags.append(mod[1:])
        elif mod[0] == '^':
            result.category = mod[1:]
        elif mod[0] == '%':
            result.list = mod[1:]
        elif mod[0] == '$' and \
             (match := re.search(r'([^=]+)=([^\s]+)', mod[1:])) is not None:
                result.variables[match.group(1).lower()] = match.group(2).lower()
        else:
            continue

        # Delete the entry that was "consumed"
        del ary[idx]

    remains = ' '.join(ary)
    return remains if re.search(r'[^\w]', remains) is not None else None


def write_category_tickets( handle, categories, tickets, show_invisible=False, include_empty=True ):
    for category in categories:
        valid = None
        if include_empty:
            handle.write(f"# ^{category.name.ljust(20)} {category.title}\n\n")

        if not show_invisible and not category.visible:
            continue

        # Write out the tickets
        for ticket in tickets:
            if ticket.category != category.name:
                continue

            # Write out the header later if we haven't yet?
            if not include_empty and valid is None:
                handle.write(f"# ^{category.name.ljust(20)} {category.title}\n\n")

            # Write out the ticket
            valid = handle.write(f'* :{ticket.uid}  {ticket.title[:64]}\n')
        if valid is not None:
            handle.write('\n')

