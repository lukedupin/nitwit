import re

from nitwit.storage import sprints as sprints_mod
from nitwit.storage import tickets as tickets_mod


class MsgFile:
    def __init__(self):
        self.contents = []
        self.new_files = []
        self.matched = []
        self.deleted = []


def handle_prepare_commit( settings, filename ):
    msg_file = process_msg_file( filename )

    # Pull the sprints
    sprints = sprints_mod.import_latest_sprints( settings, filter_owners=[settings['username']])
    if len(sprints) != 1:
        pass#return "Couldn't determine current sprint"

    sprint_lookup = {}# {uid: True for uid in sprints[0].ticket_uids}

    # Get the cats and tags we sub to
    categories = settings['subscribecategories']
    tags = settings['subscribetags']

    # Write out the file
    with open(filename, "w") as handle:
        handle.write("# Sprint:\n")

        # Load up the tickets
        for ticket in tickets_mod.import_tickets( settings ):
            if ticket.uid not in sprint_lookup:
                continue

            handle.write(f"#    ${ticket.uid} {ticket.title[:48]}")
        handle.write("#\n")

        # Add the common message
        for line in msg_file.contents:
            print(line)
            handle.write( line )

    return None


def process_msg_file( filename ):
    msg_file = MsgFile()

    with open( filename ) as handle:
        msg_file.contents = handle.readlines()

        # Process the files
        for line in msg_file.contents:
            if (match := re.search('#\+new file:\w+(.*)$', line)) is not None:
                msg_file.new_files.append( match.group(1))
            if (match := re.search('#\+modified:\w+(.*)$', line)) is not None:
                msg_file.matched.append(match.group(1))
            if (match := re.search('#\+deleted:\w+(.*)$', line)) is not None:
                msg_file.deleted.append(match.group(1))

    return msg_file
