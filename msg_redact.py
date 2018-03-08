#!/usr/bin/env python
from twilio.rest import Client
from datetime import date, datetime
import argparse
import re
import os
from time import sleep

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Delete or redact Twilio message content and obfuscate phone numbers.')
    parser.add_argument('-v','--verbose', action='count', default=0, help='Control output of messages while processing')
    filters = parser.add_argument_group(title='Filters', description='Selectively determine which messages are to be processed')
    filters.add_argument('-b','--begin', dest='begin_date', type=lambda d: datetime.strptime(d, '%Y-%m-%d'), help='The start date to process from YYYY-MM-DD')
    filters.add_argument('-e','--end', dest='end_date', type=lambda d: datetime.strptime(d, '%Y-%m-%d'), default=date.today(), help='The date to finish processing up to YYYY-MM-DD (defaults to current date)')
    filters.add_argument('-f','--from', dest='from_number', help='Only messages sent FROM a given phone number')
    filters.add_argument('-t','--to', dest='to_number', help='Only messages sent TO a given phone number')
    filters.add_argument('-s','--sid', default=[], action='append', help='Specify the message SID to process (can use multiple times)')

    actions = parser.add_argument_group(title='Actions', description='Processing actions that can be applied')
    actions.add_argument('-m','--message-redact', dest='body', action='store_true', help='Redact messages by removing the body')
    actions.add_argument('-u','--unhide-body', dest='unhide', action='store_true', help='Unhide message bodies')
    #actions.add_argument('-m','--body', const='', dest='body', nargs='?', action='store', help='Redact messages with an optional body')
    actions.add_argument('-p','--phone-mask', dest='phone', default='XXXXXX', const='', nargs='?', action='store', help='Show/Mask numbers with a block string')
    actions.add_argument('-r','--reverse-mask', dest='reverse', action='store_true', help='Mask at front rather than back')
    actions.add_argument('-d','--delete', action='store_true', help='Delete messages rather than redact')
    actions.add_argument('-n','--dry-run', action='store_true', dest='dry_run', help='Skip making any changes')
    args = parser.parse_args()
    if args.verbose >3:
        print(args)
    if args.delete and (args.body or args.phone):
        parser.error('Cannot delete and redact at the same time!')

    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    token = os.environ['TWILIO_AUTH_TOKEN']
    client = Client(account_sid, token)
    redacted = 0
    deleted = 0
    found = 0
    processed = 0
    print('fetching messages')

    messages = client.messages.list(to=args.to_number, from_=args.from_number, date_sent_after=args.begin_date, date_sent_before=args.end_date)
    for msg in messages:
        print('\rfetched={} processed={} redacted={} deleted={}'.format(found, processed, redacted, deleted), end='', flush=True)
        found = found +1
        newbody = '***HIDDEN***'
        if args.unhide:
            newbody = msg.body
        if args.body:
            newbody = '***REDACTED***'
        fl = max(0, len(msg.from_) - len(args.phone))
        tl = max(0, len(msg.to) - len(args.phone))
        if args.reverse:
            newfrom = args.phone + msg.from_[0-fl:]
            newto = args.phone + msg.to[0-tl:]
        else:
            newfrom = msg.from_[:fl] + args.phone
            newto = msg.to[:tl] + args.phone

        if args.verbose >= 1:
            print('{} {}'.format(msg.date_sent, msg.sid), end=' ')
        if len(args.sid) > 0 and msg.sid not in args.sid:
            if args.verbose >=1:
                print('--- SKIPPING ---')
            continue
        if args.verbose >= 2:
            print('\tfrom={} to={}'.format(newfrom, newto), end=' ')
        if args.verbose >= 3:
            print('\tbody={}'.format(newbody))
        elif args.verbose > 0:
            print()
        processed = processed+1
        if args.dry_run:
            if args.verbose >=1:
                print('--- DRYRUN ---')
            continue
        if args.delete is True:
            msg.delete()
            deleted = deleted+1
            if args.verbose >=1:
                print('--- DELETED ---')
        elif args.body:
            # API only allows update to a blank body, and cannot change phone numbers
            msg.update(body='')
            redacted = redacted+1
            if args.verbose >=1:
                print('--- UPDATED ---')
    print('\ncomplete!')
