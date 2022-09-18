from nitwit.storage import tickets as tickets_mod
from nitwit.storage import categories as categories_mod
from nitwit.helpers import util

import random, os


def handle_gen( parser, options, args, settings ):
    # Load in all the tickets
    tickets = tickets_mod.import_tickets( settings )
    categories = categories_mod.import_categories( settings )

    handles = {}

    # Load categories
    for category in categories:
        cat = category.name
        if cat not in handles:
            handles[cat] = open(f"{settings['directory']}/{cat}.md", 'w')

    # Open files as needed, and dump tickets into those files
    for ticket in tickets:
        # Pull the category and load the files as needed
        if (category := util.xstr(ticket.category)) == "":
            category = "tickets_report"
        if category not in handles:
            handles[category] = open(f"{settings['directory']}/{category}.md", 'w')

        # Export the ticket data into the files
        tickets_mod.export_ticket( handles[category], ticket, include_uid=True )

    # Close down all the open reports
    for key in handles.keys():
        handles[key].close()

    return None


