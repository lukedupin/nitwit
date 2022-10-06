from optparse import OptionParser

from git import GitCommandError

from nitwit.storage.parser import Parser, parse_mods, parse_content, write_category_tickets
from nitwit.storage import tickets as tickets_mod
from nitwit.storage import categories as categories_mod
from nitwit.helpers import settings as settings_mod
from nitwit.helpers import util

import random, os, re


def handle_category( settings ):
    #usage = "usage: %command [options] arg"
    parser = OptionParser("")
    parser.add_option("-c", "--create", action="store_true", dest="create", help="Create a new item")
    parser.add_option("-b", "--batch", action="store_true", dest="batch", help="Edit all categories at once")
    parser.add_option("-i", "--invisible", action="store_true", dest="invisible", help="Show invisible tickets")

    (options, args) = parser.parse_args()
    args = args[1:] # Cut away the action name, since its always "Category"

    # Edit all the categories
    if options.batch:
        return process_batch( settings, options, args )

    # Create a new category
    if options.create:
        category = categories_mod.find_category_by_name( settings, ' '.join(args), show_invisible=True)
        if category is None:
            return process_create( settings, options, args )
        else:
            return process_edit( settings, options, args, category )

    # Edit a category?
    if len(args) > 0:
        return process_edit( settings, options, args )

    # Print out the categories
    return process_print( settings, options, args )


def process_print( settings, options, args ):
    categories = categories_mod.import_categories( settings, show_invisible=True )
    if len(categories) <= 0:
        print( "No categories found. Try creating one." )

    # Dump the categories to the screen
    print("Categories")
    for idx, category in enumerate(categories):
        print(f'{str(idx+1).ljust(5)} ^{category.name.ljust(20)} {util.xstr(category.title)[:64]}')

    return None


def process_batch( settings, options, args ):
    categories = categories_mod.import_categories(settings, show_invisible=True )
    if len(categories) <= 0:
        return "No categories found. Try creating one."

    kill_list = {}

    # Open the temp file to write out categories
    filename = f"{settings['directory']}/categories.md"
    with open(filename, "w") as handle:
        for idx, category in enumerate(categories):
            kill_list[category.name] = True
            categories_mod.export_category( settings, handle, category, include_name=True )

            if idx + 1 < len(categories):
                handle.write("======\n\n")

    # Start the editor
    util.editFile( filename )

    # Wrapp up by parsing
    categories = []
    try:
        with open(filename) as handle:
            # Loop while we have data to read
            while not util.is_eof(handle):
                if (category := categories_mod.parse_category(settings, handle)) is None:
                    break

                categories.append( category )
                if category.name in kill_list:
                    del kill_list[category.name]

    except FileNotFoundError:
        return None

    # Remove everything that is now missing
    if (repo := settings_mod.git_repo()) is not None:
        for rm in kill_list.keys():
            try:
                repo.index.move([f'{settings["directory"]}/categories/{rm}.md', f'{settings["directory"]}/categories/{rm}.md_'])

            except GitCommandError:
                pass

    # Finally output the updated categories
    os.remove(filename)
    categories_mod.export_categories( settings, categories )

    return None


def process_create( settings, options, args ):
    category = categories_mod.Category()
    if len(args) > 0:
        category.name = args[0]
        category.title = re.sub('[_-]', ' ', ' '.join(args).capitalize())

    else:
        category.name = "category_title"
        category.title = re.sub('[_-]', ' ', category.name.capitalize())

    # Open the temp file to write out categories
    tmp = f"{settings['directory']}/categories.md"
    with open(tmp, "w") as handle:
        categories_mod.export_category( settings, handle, category, include_name=True )

    # Start the editor
    util.editFile( tmp )

    # Wrapp up by parsing
    categories = []
    try:
        with open(tmp) as handle:
            # Loop while we have data to read
            while not util.is_eof(handle):
                if (category := categories_mod.parse_category(settings, handle)) is None:
                    break

                categories.append( category )
        os.remove(tmp)

    except FileNotFoundError:
        os.remove(tmp)
        print("Failed to create category")
        return None

    # Write out the new category
    if len(categories) != 1:
        print("Failed to create category")
        return None

    categories_mod.export_categories( settings, categories )
    print(f"Created category: {categories[0].name}")


def process_edit( settings, options, args, category=None ):
    if category is None:
        category_name = ' '.join(args)
        category = categories_mod.find_category_by_name( settings, category_name, show_invisible=True )
        if category is None:
            print(f"Couldn't find category by: {category_name}")
            return None

    util.editFile( category.filename )

    # Re-export
    if (new_cat := categories_mod.find_category_by_name( settings, category.name, show_invisible=True )) is None:
        return None

    categories_mod.export_categories( settings, [new_cat] )