from optparse import OptionParser

from git import GitCommandError

from nitwit.storage import categories as categories_mod
from nitwit.storage import tags as tags_mod
from nitwit.storage import tickets as tickets_mod
from nitwit.helpers import settings as settings_mod
from nitwit.helpers import util

import random, os, re


def handle_ticket( settings ):
    #usage = "usage: %command [options] arg"
    parser = OptionParser("")
    parser.add_option("-c", "--create", action="store_true", dest="create", help="Create a new item")
    parser.add_option("-a", "--all", action="store_true", dest="all", help="Show all tickets, unaccepted and active")
    parser.add_option("-u", "--unaccepted", action="store_true", dest="unaccepted", help="Show only unaccepted")
    parser.add_option("-i", "--invisible", action="store_true", dest="invisible", help="Show invisible tickets")
    parser.add_option("-b", "--batch", action="store_true", dest="batch", help="Edit all tickets at once")

    (options, args) = parser.parse_args()
    args = args[1:] # Cut away the action name, since its always "Ticket"

    # edit all the tickets
    if options.batch:
        return process_batch( settings, options, args )

    # Create a new ticket
    if options.create:
        name = args[0] if len(args) >= 1 else None
        ticket = tickets_mod.find_ticket_by_uid( settings, name )
        if ticket is None:
            return process_create( settings, options, args )
        else:
            return process_edit( settings, options, args, ticket )

    # Edit a ticket?
    if process_edit( settings, options, args ):
        pass

    # Print out the tickets
    elif process_print( settings, options, args ):
        pass

    else:
        print(f"Couldn't find ticket by {' '.join(args)}")


def is_show_ticket( options, categories, ticket, limit_category, limit_tag ):
    # Handle limited views
    if limit_tag is not None:
        return limit_tag.name in ticket.tags
    elif limit_category is not None:
        return limit_category.name == ticket.category

    # Hack, if we don't know what category they are in, show them.
    if (cat := categories.get( ticket.category )) is None:
        return True

    # Return based on visibility and accepted
    if not options.invisible and not cat.visible:
        return False
    return options.all or util.xbool(options.unaccepted) != cat.accepted


def process_batch( settings, options, args ):
    categories = {x.name: x for x in categories_mod.import_categories( settings, show_invisible=True )}
    tags = {x.name: x for x in tags_mod.import_tags( settings, show_hidden=True )}

    limit_category = categories.get(args[0]) if len(args) > 0 else None
    limit_tag = tags.get(args[0]) if len(args) > 0 else None

    tickets = tickets_mod.import_tickets(settings)
    if len(tickets) <= 0:
        return "No tickets found. Try creating one."

    kill_list = {}

    # Open the temp file to write out tickets
    filename = f"{settings['directory']}/tickets.md"
    with open(filename, "w") as handle:
        for idx, ticket in enumerate(tickets):
            if not is_show_ticket( options, categories, ticket, limit_category, limit_tag ):
                continue

            kill_list[ticket.uid] = ticket
            tickets_mod.export_ticket( settings, handle, ticket, include_uid=True )

            if idx + 1 < len(tickets):
                handle.write("======\n\n")

    # Start the editor
    util.editFile( filename )

    # Wrapp up by parsing
    tickets = []
    try:
        with open(filename) as handle:
            # Loop while we have data to read
            while not util.is_eof(handle):
                if (ticket := tickets_mod.parse_ticket(settings, handle)) is None:
                    break

                if ticket.uid is None:
                    print(f"Creating new ticket: {ticket.title}")
                tickets.append( ticket )
                if ticket.uid in kill_list:
                    del kill_list[ticket.uid]

    except FileNotFoundError:
        return None

    # Remove everything that is now missing
    if (repo := settings_mod.git_repo()) is not None:
        for rm in kill_list.keys():
            try:
                print(f"Removing ticket: {kill_list[rm]}")
                repo.index.move([f'{settings["directory"]}/tickets/{rm}.md', f'{settings["directory"]}/tickets/{rm}.md_'])

            except GitCommandError:
                pass

    # Finally output the updated tickets
    os.remove(filename)
    tickets_mod.export_tickets( settings, tickets )

    return None


def process_create( settings, options, args ):
    ticket = tickets_mod.Ticket()
    if len(args) > 0:
        ticket.title = re.sub('[_-]', ' ', ' '.join(args).capitalize())

    else:
        ticket.title = "New ticket title"
    ticket.category = settings['defaultcategory']
    ticket.owners = [settings['username']]
    ticket.tags = ["tags"]
    ticket.priority = 0
    ticket.difficulty = 0

    # Open the temp file to write out tickets
    tmp = f"{settings['directory']}/tickets.md"
    with open(tmp, "w") as handle:
        tickets_mod.export_ticket( settings, handle, ticket )

    # Start the editor
    util.editFile( tmp )

    # Wrapp up by parsing
    tickets = []
    try:
        with open(tmp) as handle:
            # Loop while we have data to read
            while not util.is_eof(handle):
                uid = tickets_mod.generate_uid( settings['directory'] )
                if (ticket := tickets_mod.parse_ticket(settings, handle, uid=uid)) is None:
                    break

                tickets.append( ticket )
        os.remove(tmp)

    except FileNotFoundError:
        os.remove(tmp)
        print("Failed to create ticket")
        return None

    # Write out the new ticket
    if len(tickets) != 1:
        print("Failed to create ticket")
        return None

    tickets_mod.export_tickets( settings, tickets )
    print(f"Created ticket: {tickets[0].title}")


def process_edit( settings, options, args, ticket=None ):
    if len(args) <= 0:
        return False

    if ticket is None:
        ticket_name = re.sub('^:', '', ' '.join(args))
        ticket = tickets_mod.find_ticket_by_uid( settings, ticket_name )
        if ticket is None:
            return False

    util.editFile( ticket.filename )

    # Reformat the ticket
    if (new_ticket := tickets_mod.find_ticket_by_uid( settings, ticket.uid )) is None:
        return False

    tickets_mod.export_tickets( settings, [new_ticket] )

    return True


def process_print( settings, options, args ):
    categories = {x.name: x for x in categories_mod.import_categories( settings, show_invisible=True )}
    tags = {x.name: x for x in tags_mod.import_tags( settings, show_hidden=True )}

    limit_category = categories.get(args[0]) if len(args) > 0 else None
    limit_tag = tags.get(args[0]) if len(args) > 0 else None

    if len(args) > 0 and not limit_category and not limit_tag:
        return False

    tickets = tickets_mod.import_tickets( settings )

    # Dump the tickets to the screen
    hit = False
    category = None
    for idx, ticket in enumerate(tickets):
        if not is_show_ticket(options, categories, ticket, limit_category, limit_tag):
            continue

        if category != ticket.category:
            category = ticket.category
            print()
            print(f"   ^{category}")
            print()

        print(f'{str(idx+1).ljust(5)} :{ticket.uid.ljust(20)} {util.xstr(ticket.title)[:64]}')
        hit = True

    if not hit:
        print( "No tickets found. Try creating one or rerun: nw tickets -a" )
        return False

    return True

