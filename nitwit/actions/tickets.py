from nitwit.storage import tickets as tickets_mod
from nitwit.helpers import util

import random, os, re


def handle_ticket( parser, options, args, settings ):
    # Create?
    if options.create is not None:
        ticket = tickets_mod.Ticket( None, None, tickets_mod.safe_category(None, settings) )

        titles = []
        for mod in options.create.split(' '):
            if mod[0] == '^':
                ticket.category = tickets_mod.safe_category(mod[1:], settings)
            elif mod[0] == '!':
                ticket.priority = util.xint(mod[1:])
            elif mod[0] == '@':
                ticket.owners.append(mod[1:])
            elif mod[0] == '#':
                ticket.tags.append(mod[1:])
            else:
                titles.append( mod )

        ticket.title = ' '.join(titles)
        tickets_mod.export_tickets( settings, [ticket] )

        print(f'Created ticket in "{ticket.category}" assigned to @{ticket.owners}')

        return None

    # Print out the categories
    if len(args) < 2:
        tickets = tickets_mod.import_tickets( settings )
        if len(tickets) <= 0:
            print( "No tickets found. Try creating one." )

        hidden = {x: True for x in settings["hiddencategories"]}

        # Dump the categories to the screen
        categories = {}
        for ticket in tickets:
            if ticket.category in hidden:
                continue

            if ticket.category not in categories:
                categories[ticket.category] = []

            categories[ticket.category].append( ticket )

        # Sort the categories
        for category in categories.keys():
            if len(categories[category]) > 0:
                print(category)

            for ticket in sorted( categories[category], key=lambda x: x.title ):
                print(f"    ${ticket.uid} {ticket.title[:32]}")

        return None

    # Load up a ticket
    uid = re.sub( '[$]', '', args[1] )
    if len(tickets := tickets_mod.import_tickets( settings, [uid])) == 1:
        os.system(f'{os.environ["EDITOR"]} {tickets[0].filename}')
    else:
        return f"Couldn't find ticket by uid {args[1]}"

    return None