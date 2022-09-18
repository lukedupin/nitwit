from nitwit.storage import tickets as tickets_mod
from nitwit.storage import categories as categories_mod
from nitwit.helpers import util

import random, os


def handle_gen( parser, options, args, settings ):
    # Load in all the tickets
    tickets = tickets_mod.import_tickets( settings['directory'] )
    categories = categories_mod.import_categories( settings['directory'] )

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


def export_report( handle, tickets ):
    for idx, ticket in enumerate( sorted( tickets, key=lambda x: x.title )):
        if idx > 0:
            handle.write('\r\n\r\n')

        # Write the ticket out
        tickets_mod.export_ticket( handle, ticket, include_uid=True )


def parse_report( handle, category ):
    tickets = []

    while not util.is_eof(handle):
        # Parse out multiple tickets
        if (ticket := tickets_mod.parse_ticket( handle )) is None:
            continue

        # Create a UID?
        if ticket.uid is None:
            ticket.uid = tickets_mod.generate_uid(f'nitwit/_tickets')
            if ticket.uid is None:
                continue

        tickets.append( ticket )
