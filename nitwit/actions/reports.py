from nitwit.storage import tickets as tickets_mod
from nitwit.storage import categories as categories_mod
from nitwit.storage import sprints as sprints_mod
from nitwit.helpers import util
from nitwit.helpers import settings as settings_mod

from pathlib import Path
import random, os, re, glob


def handle_gen( parser, options, args, settings ):
    # Load in all the tickets
    tickets = tickets_mod.import_tickets( settings )
    categories = categories_mod.import_categories( settings )
    sprints = sprints_mod.import_latest_sprints( settings )
    users = settings_mod.get_users( settings )

    handles = {}

    # Sprint variables
    sprint_categories = {x: True for x in settings['sprintcategories']}
    title_lookup = {}

    # Load categories
    for category in categories:
        cat = category.name
        if cat not in handles:
            handles[cat] = open(f"{settings['directory']}/{cat}.md", 'w')

    # Open files as needed, and dump tickets into those files
    for ticket in tickets:
        # Build the ticket title lookup for the spring
        if ticket.category in sprint_categories:
            title_lookup[ticket.uid] = ticket.title

        # Pull the category and load the files as needed
        if ticket.category not in handles:
            handles[ticket.category] = open(f"{settings['directory']}/{ticket.category}.md", 'w')

        # Export the ticket data into the files
        tickets_mod.export_ticket( handles[ticket.category], ticket, include_uid=True )
        handles[ticket.category].write("======\r\n\r\n")

    # Organize the springs
    ticket_hits = {}
    sprint_hits = {}
    sprint_lookup = {u.username: sprints_mod.Sprint(None, u.username) for u in users}
    for sprint in sprints:
        sprint_lookup[sprint.owner] = sprint

    # Write the sprints
    with open(f"{settings['directory']}/sprints.md", "w") as handle:
        for owner in users:
            sprint = sprint_lookup[owner.username]

            # Store info for the ticket dump later
            sprint_hits[owner.username] = True
            for uid in sprint.ticket_uids:
                ticket_hits[uid] = True

            sprints_mod.export_sprint( handle, sprint, title_lookup )
            handle.write("======\r\n\r\n")

        # One last pass to add any users that aren't in the commit log, but have sprints
        for sprint in sprints:
            if sprint.owner not in sprint_hits:
                for uid in sprint.ticket_uids:
                    ticket_hits[uid] = True

                sprints_mod.export_sprint(handle, sprint, title_lookup)
                handle.write("======\r\n\r\n")

        handle.write("# Tickets\r\n\r\n")

        # Dump all the tickets in the sprintcategories git variable
        for cat in settings['sprintcategories']:
            handle.write(f'## {cat}\r\n\r\n')

            for ticket in tickets:
                if ticket.category == cat and ticket.uid not in ticket_hits:
                    handle.write(f'+ ${ticket.uid} {ticket.title[:64]}\r\n')

            handle.write("\r\n")

        handles['sprints'] = handle

    if len(handles) <= 0:
        return "No reports found. Please create categories or tickets."

    # Close down all the open reports
    print("Generated reports:")
    for key in handles.keys():
        print(f"    {re.sub('^.*/', '', settings['directory'])}/{key}.md")
        handles[key].close()

    return None


def handle_consume( parser, options, args, settings ):
    tickets = []

    # Read in all the tickets
    for file in glob.glob(f'{settings["directory"]}/*.md'):
        cat = re.sub('[.]md$', '', file.split('/')[-1] )
        with open(file) as handle:
            # Loop while we have data to read
            while not util.is_eof( handle ):
                if (ticket := tickets_mod.parse_ticket( settings, handle, category=cat )) is None:
                    break

                tickets.append( ticket )

    # Export all tickets processed from the report
    new_count, update_count = tickets_mod.export_tickets( settings, tickets )

    print( f"Consumed {new_count} new tickets")
    print( f"Consumed {update_count} updated tickets")
    print( f"{len(tickets)} total tickets")
    print()

    return handle_gen( parser, options, args, settings )


