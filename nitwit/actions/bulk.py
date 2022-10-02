from optparse import OptionParser

from git import GitCommandError
from nitwit.actions import usage

from nitwit.storage.parser import Parser, parse_mods
from nitwit.storage import tickets as tickets_mod
from nitwit.storage import categories as categories_mod
from nitwit.storage import tags as tags_mod
from nitwit.helpers import settings as settings_mod
from nitwit.helpers import util

import random, os, re


def handle_bulk( settings ):
    #usage = "usage: %command [options] arg"
    parser = OptionParser("")
    parser.add_option("-i", "--invisible", action="store_true", dest="invisible", help="Show invisible tickets")
    #parser.add_option("-c", "--create", action="store_true", dest="create", help="Create a new item")
    #parser.add_option("-b", "--batch", action="store_true", dest="batch", help="Edit all categories at once")

    (options, args) = parser.parse_args()
    args = args[1:] # Cut away the action name, since its always "Category"

    # Return the len
    if len(args) <= 0:
        pass

    # Edit all the categories
    elif args[0] == "categories" or args[0] == 'category':
        return handle_categories( settings, options, args )

    elif args[0] == 'tags' or args[0] == 'tag':
        return handle_tags( settings, options, args )

    return usage.detail_bulk()


def handle_categories( settings, options, args ):
    # Load in all the tickets
    tickets = tickets_mod.import_tickets( settings )
    categories = categories_mod.import_categories( settings, show_invisible=True )

    filename = f"{settings['directory']}/bulk_categories.md"

    # Load up the file
    with open(filename, "w") as handle:
        write_category_tickets( handle, categories, tickets, options.invisible )

    util.editFile( filename )

    ticket_updates = []

    # Consume the file
    category = None
    with open(filename) as handle:
        for line in handle.readlines():
            line = line.rstrip()

            # Detect the category
            if (match := re.search(r'^#\s*\^(\w+)', line)) is not None:
                category = util.first( categories, lambda x: x.name == match.group(1) )
                continue

            if category is None or \
               re.search(r'======', line) is not None:
                continue

            # Pull ticket data
            if (match := re.search(r'^\s*[*]\s*(.*)$', line)) is not None:
                parse = Parser()
                parse.title = parse_mods( parse, match.group(1) )

                # Attempt to just find the ticket, if all that fails,
                if (ticket := util.first( tickets, lambda x: x.uid == parse.uid )) is not None:
                    pass
                elif (ticket := util.first(tickets, lambda x: x.title == parse.title)) is not None:
                    pass
                elif parse.title is not None:
                    ticket = tickets_mod.to_ticket( settings, parse, uid="hack" )
                    ticket.uid = None

                # Everything failed, this isn't a valid ticket line
                else:
                    continue

                # Convert this ticket to this category, and add it to the update list
                ticket.category = category.name
                ticket_updates.append( ticket )

    # Remove the temp file
    os.remove(filename)
    tickets_mod.export_tickets( settings, ticket_updates )

    return None


def handle_tags( settings, options, args ):
    # Load in all the tickets
    tickets = tickets_mod.import_tickets( settings )
    tags = tags_mod.import_tags( settings, show_hidden=True )
    categories = categories_mod.import_categories( settings )

    filename = f"{settings['directory']}/bulk_tags.md"

    # Setup my dictionaries
    ticket_updates = {}
    tickets_missed = {x.uid: x for x in tickets}

    # Load up the file
    with open(filename, "w") as handle:
        for tag in tags:
            handle.write(f"# #{tag.name.ljust(20)} {tag.title}\n\n")

            if not options.invisible and tag.hidden:
                continue

            # Write out the tickets
            valid = None
            for ticket in tickets:
                if tag.name in ticket.tags:
                    valid = handle.write(f'* :{ticket.uid}  {ticket.title[:64]}\n')

                    # Clean up missed tickets
                    ticket_updates[ticket.uid] = ticket
                    if ticket.uid in tickets_missed:
                        del tickets_missed[ticket.uid]
            if valid is not None:
                handle.write('\n')

        if len(tickets_missed) > 0:
            handle.write("\n###### Tickets without tags ######\n\n")
            write_category_tickets( handle, categories, tickets_missed.values(), options.invisible, include_empty=False )

    util.editFile( filename )

    # Clear out all tags and setup the updates
    for ticket in tickets:
        ticket.tags = []

    # Consume the file
    tag = None
    with open(filename) as handle:
        for line in handle.readlines():
            line = line.rstrip()

            # Detect the tag
            if (match := re.search(r'^#\s*\#(\w+)', line)) is not None:
                tag = util.first( tags, lambda x: x.name == match.group(1) )
                continue

            if tag is None or \
               re.search(r'======', line) is not None:
                continue

            if re.search(r'######', line) is not None:
                break

            # Pull ticket data
            if (match := re.search(r'^\s*[*]\s*(.*)$', line)) is not None:
                parse = Parser()
                parse.title = parse_mods( parse, match.group(1) )

                # Attempt to just find the ticket, if all that fails,
                if (ticket := util.first( tickets, lambda x: x.uid == parse.uid )) is not None:
                    pass
                elif (ticket := util.first(tickets, lambda x: x.title == parse.title)) is not None:
                    pass
                elif parse.title is not None:
                    ticket = tickets_mod.to_ticket( settings, parse, uid="hack" )
                    ticket.uid = None

                # Everything failed, this isn't a valid ticket line
                else:
                    continue

                # Convert this ticket to this tag, and add it to the update list
                ticket.tags.append( tag.name )
                if ticket.uid is None:
                    ticket_updates[tickets_mod.generate_uid(settings['directory'])] = ticket
                else:
                    ticket_updates[ticket.uid] = ticket

    # Remove the temp file
    os.remove(filename)
    tickets_mod.export_tickets( settings, ticket_updates.values() )

    return None


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

