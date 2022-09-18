from nitwit.storage import tickets as tickets_mod
from nitwit.helpers import util

import random, os


def handle_ticket( parser, options, args, settings ):
    # Print out the categories
    if len(args) < 2:
        tickets = tickets_mod.import_tickets( settings['directory'] )
        if len(tickets) <= 0:
            print( "No tickets found. Try creating one." )

        # Dump the categories to the screen
        categories = {}
        for ticket in tickets:
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

    return None