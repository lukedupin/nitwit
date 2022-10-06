import re

from nitwit.storage import tickets as tickets_mod
from nitwit.storage import categories as categories_mod
from nitwit.storage import tags as tags_mod
from nitwit.helpers import settings as settings_mod
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

    categories = categories_mod.import_categories(settings)

    raw_tickets = tickets_mod.import_tickets( settings, filter_owners=settings['username'])
    tickets = {t.uid: t for t in raw_tickets}
    ticket_hits = {}

    # Get diffs of tickets
    change_title = []
    changes = []
    repo = settings_mod.git_repo()
    for ticket in tickets.values():
        handle = settings_mod.read_file_from_repo( ticket.filename, repo)
        existing = tickets_mod.parse_ticket( settings, handle, ticket.uid )
        if existing is not None and len(ticket.notes) == len(existing.notes):
            continue

        offset = len(existing.notes) if existing else 0

        # Store the changes!
        change_title.append( f":{ticket.uid}" )
        changes.append( f":{ticket.uid}   {ticket.title}" )
        changes.append( "" )
        changes += ticket.notes[offset:]
        changes.append( "" )

    # Pull the sprints
    sprints = []
    #sprints = sprints_mod.import_latest_sprints( settings, filter_owners=[settings['username']])
    if len(sprints) != 1:
        pass#return "Couldn't determine current sprint"

    # Get the cats and tags we sub to
    category_names = settings['subscribecategories']
    tag_names = settings['subscribetags']

    # Write out the file
    with open(filename, "w") as handle:
        if len(change_title) > 0:
            handle.write(f"Ticket changes: {' '.join(change_title)}\n\n")
            for line in changes:
                handle.write(f"{line}\n")

        handle.write("\n")
        for line in msg_file.header:
            handle.write(line)

        #handle.write("# My current Sprint:\n")
        #for uid in sprints[0].ticket_uids:
        #    ticket_hits[uid] = True
        #    write_ticket_line( handle, uid, tickets.get(uid))

        # Print out categories
        for category in categories:
            first = True
            for ticket in tickets.values():
                if category.name != ticket.category:
                    continue

                # Print out the header
                if first:
                    handle.write( f"#    ^{category.name.ljust(16)} {util.xstr(category.title)[:48]}\n")
                    first = False

                write_ticket_line( handle, ticket )

            if not first:
                handle.write("#\n")

        # Print out tags
        dog = '''
        for tag_name in tag_names:
            if (tag := tags.get(tag_name)) is None:
                tag = tags_mod.Tag(None, tag_name)

            handle.write(f"# #{tag.name.ljust(16)} {util.xstr(tag.title)[:48]}\n")
            for uid in tickets.keys():
                if uid in ticket_hits:
                    continue

                ticket = tickets[uid]
                if tag.name in ticket.tags and ticket.category in categories:
                    write_ticket_line( handle, uid, ticket )
            handle.write("#\n")
        '''

        # Add the common message
        for line in msg_file.contents:
            handle.write( line )

    return None


def write_ticket_line( handle, ticket ):
    handle.write(f'# %{util.xstr(ticket.uid)}  {util.xstr(ticket.title)[:48]}\n')


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
