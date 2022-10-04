from optparse import OptionParser

from git import GitCommandError

from nitwit.actions import bulk
from nitwit.storage import lists as lists_mod
from nitwit.storage import tickets as tickets_mod
from nitwit.storage import categories as categories_mod
from nitwit.helpers import settings as settings_mod
from nitwit.helpers import util

import random, os, re


def handle_list( settings ):
    #usage = "usage: %command [options] arg"
    parser = OptionParser("")
    parser.add_option("-c", "--create", action="store_true", dest="create", help="Create a new item")
    parser.add_option("-a", "--active", action="store_true", dest="active", help="Show all lists, not just active ones")
    parser.add_option("-e", "--everyone", action="store_true", dest="everyone", help="Show all lists, not just lists you're on")

    (options, args) = parser.parse_args()
    args = args[1:] # Cut away the action name, since its always "List"

    # Create a new lst
    if options.create:
        return process_create( settings, args, options )

    # Edit a lst?
    if len(args) > 0:
        return process_edit( settings, args, options )

    # Print out the lists
    return process_print( settings, args, options )


def process_print( settings, args, options ):
    owners = [settings['username']] if not options.everyone else None
    active = True if not options.active else None
    lists = lists_mod.import_lists( settings, filter_owners=owners, active=active )
    if len(lists) <= 0:
        print( "No lists found. Try creating one." )

    # Dump the lists to the screen
    print("Lists")
    for idx, lst in enumerate(lists):
        print(f'{str(idx+1).ljust(5)} %{lst.name.ljust(20)} {util.xstr(lst.title)[:64]}')

    return None


def process_batch( settings, args, options ):
    lists = lists_mod.import_lists(settings, show_hidden=options.all)
    if len(lists) <= 0:
        return "No lists found. Try creating one."

    kill_list = {}

    # Open the temp file to write out lists
    filename = f"{settings['directory']}/lists.md"
    with open(filename, "w") as handle:
        for idx, lst in enumerate(lists):
            kill_list[lst.name] = True
            lists_mod.export_lst( settings, handle, lst, include_name=True )

            if idx + 1 < len(lists):
                handle.write("======\n\n")

    # Start the editor
    util.editFile( filename )

    # Wrapp up by parsing
    lists = []
    try:
        with open(filename) as handle:
            # Loop while we have data to read
            while not util.is_eof(handle):
                if (lst := lists_mod.parse_lst(settings, handle)) is None:
                    break

                lists.append( lst )
                if lst.name in kill_list:
                    del kill_list[lst.name]

    except FileNotFoundError:
        return None

    # Remove everything that is now missing
    if (repo := settings_mod.git_repo()) is not None:
        for rm in kill_list.keys():
            try:
                repo.index.move([f'{settings["directory"]}/lists/{rm}.md', f'{settings["directory"]}/lists/{rm}.md_'])

            except GitCommandError:
                pass

    # Finally output the updated lists
    os.remove(filename)
    lists_mod.export_lists( settings, lists )

    return None


def process_create( settings, args, options ):
    lst_name = ' '.join(args)
    if (lst := lists_mod.find_lst_by_name(settings, lst_name)) is None:
        lst = lists_mod.List()
        lst.date = util.timeNow( 6 * 7 * 24 * 3600 * 1000 ).strftime("%02Y-%02m-%02d")
        lst.owner = settings['username']

        if len(args) > 0:
            lst.name = args[0]
            lst.title = re.sub('[_-]', ' ', ' '.join(args[1:]).capitalize())

        else:
            lst.name = f"sprint_{lst.date}"
            lst.title = re.sub('[_-]', ' ', lst.name.capitalize())


    process_edit( settings, args, options, lst )
    print(f"Created list")
    return None


def process_edit( settings, args, options, lst=None ):
    if lst is None:
        lst_name = ' '.join(args)
        lst = lists_mod.find_lst_by_name( settings, lst_name )
        if lst is None:
            print(f"Couldn't find lst by: {lst_name}")
            return None

    tickets = tickets_mod.import_tickets( settings )
    categories = categories_mod.import_categories( settings, show_invisible=True )

    # Used for friendly named tickets and limiting overlapping tickets
    title_lookup = {x.uid: x.title for x in tickets}
    list_ticket_uids = {x.uid: True for x in lst.ticket_uids}

    # Open the temp file to write out lists
    tmp = f"{settings['directory']}/lists.md"
    with open(tmp, "w") as handle:
        lists_mod.export_list(settings, handle, lst, title_lookup=title_lookup, include_name=True)

        handle.write("\n###### Tickets ######\n\n")

        bulk.write_category_tickets(handle, categories, [x for x in tickets if x.uid not in list_ticket_uids],
                                    show_invisible=False,
                                    include_empty=False)

    # Start the editor
    util.editFile(tmp)

    # Wrapp up by parsing
    lists = []
    try:
        with open(tmp) as handle:
            # Loop while we have data to read
            while not util.is_eof(handle):
                if (lst := lists_mod.parse_list(settings, handle)) is None:
                    break

                lists.append(lst)
        os.remove(tmp)

    except FileNotFoundError:
        os.remove(tmp)
        print("Failed to create lst")
        return None

    # Write out the new lst
    if len(lists) <= 0:
        print("Failed to edit lst")
        return None

    lists_mod.export_lists(settings, lists)
    return None