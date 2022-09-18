from storage.tickets import Ticket
from storage.tickets import parse_ticket, export_ticket, generate_uid

from storage import 
from helpers import util

import random, os


def handle_gen( parser, options, args, settings ):


    return True


def export_report( handle, tickets ):
    for idx, ticket in enumerate( sorted( tickets, key=lambda x: x.title )):
        if idx > 0:
            handle.write('\r\n\r\n')

        # Write the ticket out
        export_ticket( handle, ticket, include_uid=True )


def parse_report( handle, category ):
    tickets = []

    while not util.is_eof(handle):
        # Parse out multiple tickets
        if (ticket := parse_ticket( handle )) is None:
            continue

        # Create a UID?
        if ticket.uid is None:
            ticket.uid = generate_uid(f'nitwit/_tickets')
            if ticket.uid is None:
                continue

        tickets.append( ticket )
