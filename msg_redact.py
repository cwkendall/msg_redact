#!/usr/bin/env python
from twilio.rest import Client
from datetime import date, datetime
import argparse
import re
import os
import sys
from time import sleep

print('****************************************************************************************')
print('*** This source code is provided as an EXAMPLE and comes with NO WARRANTY.           ***')
print('*** It can modify your account and make IRREVERISBLE changes that support cannot fix ***')
print('*** Therefore it should not be used in production without your own extensive testing ***')
print('*** Please refer to the Twilio Terms of Service: https://www.twilio.com/legal/tos    ***')
print('****************************************************************************************')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Delete or redact Twilio message content. Default action is to print messages only')
    parser.add_argument('-v','--verbose', action='count', default=0, help='Control messages display: 1=date/sids, 2=numbers, 3=bodies')
    filters = parser.add_argument_group(title='Filters', description='Selectively determine which messages are to be processed')
    filters.add_argument('-b','--begin', dest='begin_date', type=lambda d: datetime.strptime(d, '%Y-%m-%d'), help='The start date to process from YYYY-MM-DD')
    filters.add_argument('-e','--end', dest='end_date', type=lambda d: datetime.strptime(d, '%Y-%m-%d'), default=date.today(), help='The date to finish processing up to YYYY-MM-DD (defaults to current date)')
    filters.add_argument('-f','--from', dest='from_number', help='Only messages sent FROM a given phone number')
    filters.add_argument('-t','--to', dest='to_number', help='Only messages sent TO a given phone number')
    filters.add_argument('-s','--sid', default=[], action='append', help='Specify the message SID to process (can use multiple times)')

    actions = parser.add_argument_group(title='Actions', description='Processing actions that can be applied')
    actions.add_argument('--message-redact', dest='body', action='store_true', help='Redact messages by removing the body')
    actions.add_argument('-u','--unhide-body', dest='unhide', action='store_true', help='Unhide message bodies')
    #actions.add_argument('-m','--body', const='', dest='body', nargs='?', action='store', help='Redact messages with an optional body')
    actions.add_argument('-p','--phone-mask', dest='phone', default='XXXXXX', const='', nargs='?', action='store', help='Show/Mask numbers with a block string')
    actions.add_argument('-r','--reverse-mask', dest='reverse', action='store_true', help='Mask at front rather than back')
    actions.add_argument('--delete', action='store_true', help='Delete messages rather than redact')
    actions.add_argument('-n','--dry-run', action='store_true', dest='dry_run', help='Skip making any changes')
    actions.add_argument('-y','--yes', action='store_true', dest='yes_all', help='Process all messages without a prompt (MAKE SURE YOU WANT THIS)')
    args = parser.parse_args()

    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    token = os.environ['TWILIO_AUTH_TOKEN']
    if args.verbose >3:
        print(args)
    if args.delete and args.body:
        parser.error('Cannot delete and redact at the same time! Exiting')
    if args.delete or args.body:
        print('You have selected to {} one or more records. *** THIS ACTION CANNOT BE UNDONE *** '.format('DELETE' if args.delete else 'REDACT'))
        sid_enter = input('Please enter your account SID to confirm this action: ')
        if sid_enter != account_sid:
            print('This action does not have your consent! Aborting')
            sys.exit(0)

    client = Client(account_sid, token)
    redacted = 0
    deleted = 0
    found = 0
    processed = 0
    print('fetching messages')

    messages = client.messages.list(to=args.to_number, from_=args.from_number, date_sent_after=args.begin_date, date_sent_before=args.end_date)
    if args.yes_all:
        confirm = 'y'
    for msg in messages:
        print('\rfetched={} processed={} redacted={} deleted={}\t'.format(found, processed, redacted, deleted), end='', flush=True)
        sleep(0.01)
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
            print('from={} to={}'.format(newfrom, newto), end=' ')
        if args.verbose >= 3:
            print('body={}'.format(newbody))
        elif args.verbose > 0:
            print()
        processed = processed+1
        if args.dry_run:
            if args.verbose >=1:
                print('--- DRYRUN NO CHANGES MADE ---')
            continue
        if args.delete is True:
            if not args.yes_all:
                confirm = input('Are you sure you want to delete the above message (y/n)? ')
            if confirm[:1] == 'y':
                msg.delete()
                deleted = deleted+1
                if args.verbose >=1:
                    print('--- DELETED MESSAGE ---')
        elif args.body:
            if not args.yes_all:
                confirm = input('Are you sure you want to redact the above message (y/n)? ')
            if confirm[:1] == 'y':
                # API only allows update to a blank body, and cannot change phone numbers
                msg.update(body='')
                redacted = redacted+1
                if args.verbose >=1:
                    print('--- MESSAGE UPDATED (REMOVED BODY) ---')
    print('\rfetched={} processed={} redacted={} deleted={}'.format(found, processed, redacted, deleted), flush=True)
    print('complete!')
