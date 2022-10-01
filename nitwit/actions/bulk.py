from optparse import OptionParser

from git import GitCommandError
from nitwit.actions import usage

from nitwit.storage import tickets as tickets_mod
from nitwit.storage import categories as categories_mod
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
    elif args[0] == "categories":
        handle_categories( settings )
        pass

    elif args[0] == 'tags':
        pass

    return usage.detail_bulk()

def handle_categories( settings, options, args ):
    # Load in all the tickets
    tickets = tickets_mod.import_tickets( settings )
    categories = categories_mod.import_categories( settings, show_invisible=True )

    filename = f"{settings['directory']}/bulk_categories.md"

    # Load up the file
    with open(filename, "w") as handle:
        for category in categories:
            handle.write(f"# ^{category.name}\n\n")

            if not options.invisible and not category.visible:
                continue

            valid = None
            for ticket in tickets:
                if ticket.category == category.name:
                    valid = handle.write(f'* :{ticket.uid}    {ticket.title[:64]}\n')

            if valid is not None:
                handle.write('\n')

    util.editFile( filename )

    # Consume the file
    category = None
    with open(filename) as handle:
        for line



    return None


def handle_consume( parser, options, args, settings ):
    categories = categories_mod.import_categories( settings )

    tickets = []

    # Read in all the tickets
    for category in categories:
        try:
            with open(f'{settings["directory"]}/{category.name}.md') as handle:
                # Loop while we have data to read
                while not util.is_eof( handle ):
                    if (ticket := tickets_mod.parse_ticket( settings, handle, category=category.name )) is None:
                        break

                    tickets.append( ticket )

        except FileNotFoundError:
            continue

    # Export all tickets processed from the report
    new_count, update_count = tickets_mod.export_tickets( settings, tickets )

    print( f"Consumed {new_count} new tickets")
    print( f"Consumed {update_count} updated tickets")
    print( f"{len(tickets)} total tickets")
    print()

    sprints = []

    # Read in the sprint
    with open(f'{settings["directory"]}/sprints.md') as handle:
        # Loop while we have data to read
        while not util.is_eof(handle):
            if (sprint := sprints_mod.parse_sprint( handle, None, None )) is None:
                break

            sprints.append( sprint )

    # Export all sprints
    sprints_mod.export_sprints( settings, sprints )

    return handle_gen( parser, options, args, settings )


