from nitwit.storage import categories as categories_mod
from nitwit.helpers import util

import random, os


def handle_category( parser, options, args, settings ):
    # Print out the categories
    if len(args) < 2:
        categories = categories_mod.import_categories( settings['directory'] )
        if len(categories) <= 0:
            print( "No categories found. Try creating one." )

        # Dump the categories to the screen
        for category in categories:
            print(f'#{category.name}')

        return None

    # Get the category name
    category_name = args[1].lower()

    # Either creator or edit a category
    categories = categories_mod.import_categories( settings['directory'], filter_names=[category_name] )
    if len(categories) <= 0:
        category = categories_mod.Category( None, category_name )
        category.title = category.name.capitalize()
        categories_mod.export_categories( settings['directory'], [category] )
        print(f"Created category #{category.name}")

    else:
        os.system(f'{os.environ["EDITOR"]} {categories[0].filename}')

    return None