from nitwit.storage import sprints as sprints_mod
from nitwit.storage import tickets as tickets_mod
from nitwit.helpers import util

import random, os


def handle_sprints( parser, options, args, settings ):
    tickets = {t.uid: t for t in tickets_mod.import_tickets( settings )}

    # Print out the sprints
    if len(args) < 2:
        sprints = sprints_mod.import_latest_sprints( settings, filter_owners=[settings['username']])
        if len(sprints) != 1:
            print( "No sprints found. Try creating one." )

        # Dump the sprints to the screen
        print("My active tickets")
        for uid in sprints[0].ticket_uids:
            title = ""
            cat = ""
            if (ticket := tickets.get(uid)) is not None:
                title = ticket.title
                cat = f'^{ticket.category}'

            print(f'    ${uid}  {cat.ljust(16)} {title[:64]}')

        return None

    # Get the sprint name
    sprint_name = args[1].lower()

    # Either creator or edit a sprint
    sprints = sprints_mod.import_sprints( settings, filter_names=[sprint_name] )
    if len(sprints) <= 0:
        sprint = sprints_mod.Sprint( None, sprint_name )
        sprint.title = sprint.name.capitalize()
        sprints_mod.export_sprints( settings, [sprint] )
        print(f"Created sprint #{sprint.name}")

    else:
        os.system(f'{os.environ["EDITOR"]} {sprints[0].filename}')


    return None