from optparse import OptionParser

from git import GitCommandError

from nitwit.storage.parser import Parser, parse_mods, parse_content, write_category_tickets
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
    parser.add_option("--cat", "--category", "--categories", action="store_true", dest="categories", help="Edit all tickets relative to categories")
    parser.add_option("--tag", "--tags", action="store_true", dest="tags", help="Edit all tickets relative to tags")
    parser.add_option("--user", "--username", "--usernames", action="store_true", dest="usernames", help="Edit all tickets relative to usernames")

    (options, args) = parser.parse_args()
    args = args[1:] # Cut away the action name, since its always "Ticket"

    # edit all the tickets
    if options.batch:
        return process_batch( settings, options, args )

    if options.categories:
        return process_categories( settings, options, args )

    if options.tags:
        return process_tags( settings, options, args )

    if options.usernames:
        return process_usernames( settings, options, args )

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


def process_categories( settings, options, args ):
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


def process_tags( settings, options, args ):
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


def process_usernames( settings, options, args ):
    pass