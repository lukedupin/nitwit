def detail_generic():
    print('''
Nitwit usage:
    init        Initialize a new nitwit ticket directory inside git
    
    ticket      Interface with tickets
    tag         Manipulate tags which are used to group tickets
    category    Configure categories which manage tickets as through the system
    list        Manage lists of tickets which are used to focus priority
    
    help        Get more detailed information about each section
''')


def detail_ticket():
    print('''
Ticket usage:
    init        Initialize a new nitwit ticket directory inside git

    ticket      Interface with tickets
    tag         Manipulate tags which are used to group tickets
    category    Configure categories which manage tickets as through the system
    list        Manage lists of tickets which are used to focus priority

    help        Get more detailed information about each section
''')


def detail_tag():
    print('''
Tag usage:
    nw tag [-c | -i | -b] [--create | --invisible | --batch] <tagname>

DESCRIPTION
    View / edit / create/ delete tags.
    
    Empty               Display all currently active tags
    -i | --invisible    Include invisible tags
    -c | --create       Creates a new tag by the given name
    -b | --batch        Batch edit all tags
    <tagname>           Edit a single tag
''')


def detail_category():
    pass


def detail_list():
    pass


def show_usage( detail=None ):
    if detail == "ticket":
        detail_ticket()
    elif detail == "tag":
        detail_tag()
    elif detail == "category":
        detail_category()
    elif detail == "list":
        detail_list()

    else:
        detail_generic()
