from nitwit.storage import tickets as tickets_mod
from nitwit.storage import categories as categories_mod
from nitwit.helpers import util

from pathlib import Path
import random, os, re, glob


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
        if ticket.category not in handles:
            handles[category] = open(f"{settings['directory']}/{ticket.category}.md", 'w')

        # Export the ticket data into the files
        tickets_mod.export_ticket( handles[ticket.category], ticket, include_uid=True )

    if len(handles) <= 0:
        return "No reports found. Please create categories or tickets."

    # Close down all the open reports
    print("Generated reports:")
    for key in handles.keys():
        print(f"    {re.sub('^.*/', '', settings['directory'])}/{key}.md")
        handles[key].close()

    return None


def handle_process( parser, options, args, settings ):
    tickets = []

    # Read in all the tickets
    for file in glob.glob(f'{settings["directory"]}/*.md'):
        with open(file) as handle:
            # Loop while we have data to read
            while not util.is_eof( handle ):
                if (ticket := tickets_mod.parse_ticket( settings, handle )) is not None:
                    tickets.append( ticket )

                else:
                    break

    # Export all tickets processed from the report
    tickets_mod.export_tickets( settings, tickets )

    print( f"Processed {len(tickets)} tickets")
    print()

    return handle_gen( parser, options, args, settings )


