import re

from nitwit.storage import sprints as sprints_mod
from nitwit.storage import tickets as tickets_mod
from nitwit.storage import tags as tags_mod
from nitwit.helpers import util


class MsgFile:
    def __init__(self):
        self.header = []
        self.contents = []

        self.new_files = []
        self.matched = []
        self.deleted = []


def handle_prepare_commit( settings, filename ):
    msg_file = process_msg_file( filename )

    tags = {tag.name: tag for tag in tags_mod.import_tags( settings )}
    tickets = {t.uid: t for t in tickets_mod.import_tickets(settings)}
    ticket_hits = {}

    # Pull the sprints
    sprints = sprints_mod.import_latest_sprints( settings, filter_owners=[settings['username']])
    if len(sprints) != 1:
        pass#return "Couldn't determine current sprint"

    # Get the cats and tags we sub to
    categories = settings['subscribecategories']
    tag_names = settings['subscribetags']
    hidden_categories = {x: True for x in settings['hiddencategories']}

    # Write out the file
    with open(filename, "w") as handle:
        handle.write("\n")
        for line in msg_file.header:
            handle.write(line)

        handle.write("# My current Sprint:\n")
        for uid in sprints[0].ticket_uids:
            ticket_hits[uid] = True
            write_ticket_line( handle, uid, tickets.get(uid))

        handle.write("#\n")

        # Print out categories
        #for cat in categories: for uid in tickets.keys():

        # Print out tags
        for tag_name in tag_names:
            if (tag := tags.get(tag_name)) is None:
                tag = tags_mod.Tag(None, tag_name)

            handle.write(f"# #{tag.name.ljust(16)} {util.xstr(tag.title)[:48]}\n")
            for uid in tickets.keys():
                if uid in ticket_hits:
                    continue

                ticket = tickets[uid]
                if tag.name in ticket.tags and ticket.category not in hidden_categories:
                    write_ticket_line( handle, uid, ticket )
            handle.write("#\n")

        # Add the common message
        for line in msg_file.contents:
            handle.write( line )

    return None


def write_ticket_line( handle, uid, ticket ):
    title = ""
    cat = ""
    if ticket is not None:
        title = ticket.title
        cat = f'^{ticket.category}'

    handle.write(f'#       ${uid}  {cat.ljust(16)} {title[:48]}\n')

def process_msg_file( filename ):
    msg_file = MsgFile()
    content = False

    with open( filename ) as handle:
        msg_file.header = []
        msg_file.contents = []
        for line in handle.readlines():
            # Store the data!
            if line.rstrip() != "":
                content |= re.search('^# Changes', line ) is not None
                if not content:
                    msg_file.header.append( line )
                else:
                    msg_file.contents.append( line )

        # Process the files
        for line in msg_file.contents:
            if (match := re.search('#\+new file:\w+(.*)$', line)) is not None:
                msg_file.new_files.append( match.group(1))
            if (match := re.search('#\+modified:\w+(.*)$', line)) is not None:
                msg_file.matched.append(match.group(1))
            if (match := re.search('#\+deleted:\w+(.*)$', line)) is not None:
                msg_file.deleted.append(match.group(1))

    return msg_file
