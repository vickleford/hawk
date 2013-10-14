"""
A tool for applying your YAML configuration of "profiles" containing 
checks and alarms to a series of entites to be monitored. Also
has some supplementary features to help get some necessary arguments.

Copyright 2013 Victor Watkins <vic.watkins@rackspace.com>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


import argparse
from rackspace_monitoring.providers import get_driver
from rackspace_monitoring.types import Provider
from keyring import get_password, set_password
from getpass import getpass
from config import config


def setpass(driver, args):
    password = getpass("API Key: ")
    set_password('hawk', args.account, password)


def list_entities(driver, args):
    row = '{:<15}{:<40}{:<40}'
    print(row.format('ID', 'Label', 'Agent ID'))
    for ent in driver.list_entities():
        print(row.format(ent.id, ent.label, ent.agent_id))
        
        
def list_notifications(driver, args):
    print("Notification Plans")
    row = '{:<20}{:<60}'
    rowb = '{:<20}{:<60}'
    for np in driver.list_notification_plans():
        print(row.format('ID', 'Label'))
        print(row.format(np.id[:19], np.label))
        # because you know this will get cluttered up
        print(rowb.format('OK', ' '.join(np.ok_state)))
        print(rowb.format('WARN', ' '.join(np.warning_state)))
        print(rowb.format('CRIT', ' '.join(np.critical_state)))
        print
              
    print("Notifications")
    row = '{:<20}{:<40}{:<20}'
    print(row.format('ID', 'Label', 'Type'))
    for n in driver.list_notifications():
        print(row.format(n.id, n.label, n.type))
        print('{:<20}{:<60}'.format('Details', n.details))
        print


def make_notification(driver, args):
    payload = { 'type': args.type,
                'label': args.label
              }
              
    if args.type == 'email':
        payload.update({'details': { 'address': args.detail }})
    elif args.type == 'webhook':
        payload.update({'details': { 'url': args.detail }})
    elif args.type == 'pagerduty':
        payload.update({'details': { 'wtfgoeshere': args.detail }})
        
    if args.who:
        payload.update({'who': args.who})
    if args.why:
        payload.update({'why': args.why})
        
    driver.create_notification(**payload)
    
    
def make_notification_plan(driver, args):
    payload = { 'label': args.label }
    
    if args.ok:
        payload.update({'ok_state': args.ok})
    if args.warning:
        payload.update({'warning_state': args.warning})
    if args.critical:
        payload.update({'critical_state': args.critical})
    
    if args.who:
        payload.update({'who': args.who})
    if args.why:
        payload.update({'why': args.why})
        
    driver.create_notification_plan(**payload)


def apply(driver, args):
    alarms = config[args.profile]['alarms']
    checks = config[args.profile]['checks']
    
    for ent in args.ents:
        try:
            e = driver.get_entity(ent)
        except:
            continue
            
        for check in checks:
            payload = checks[check]
            
            if args.who:
                payload.update({'who': args.who})
            if args.why:
                payload.update({'why': args.why})
                
            try:
                chk = driver.create_check(e, **payload)
            except Exception as err:
                print "in check", check, ": ", err
                print payload
                continue
            
            if check in alarms:
                alarm_payload = alarms[check]
                
                alarm_payload.update({'check_id': chk.id, 'notification_plan_id': args.plan})
                
                if args.who:
                    alarm_payload.update({'who': args.who})
                if args.why:
                    alarm_payload.update({'why': args.why})
                
                try:
                    driver.create_alarm(e, **alarm_payload)
                except Exception as err:
                    print "in alarm for check", check, ": ", err
                    print alarm_payload
                    continue

                
def hose(driver, args):
    for ent in args.ents:
        try:
            e = driver.get_entity(ent)
        except:
            continue
            
        for a in driver.list_alarms(e):
            driver.delete_alarm(a)
            
        for c in driver.list_checks(e):
            driver.delete_check(c)
            
            
def lstoks(driver, args):
    tmpl = '{:<26}{:<71}'
    for tok in driver.list_agent_tokens():
        try:
            print(tmpl.format(tok.label[:25], tok.id))
        except TypeError:
            print(tmpl.format('(no label)', tok.id))


def mktok(driver, args):
    payload = {}
    
    if args.who:
        payload.update({'who': args.who})
    if args.why:
        payload.update({'why': args.why})
        
    driver.create_agent_token(label=args.label)
    
    
def rmtok(driver, args):
    token = driver.get_agent_token(args.token_id)
    payload = {}
    
    if args.who:
        payload.update({'who': args.who})
    if args.why:
        payload.update({'why': args.why})
        
    driver.delete_agent_token(token, **payload)
    

def spawn():
    parser = argparse.ArgumentParser(description="Manage your Rackspace Cloud Monitors.")
    parser.add_argument('--who', default=None, help='Who is making the change (for auditing)')
    parser.add_argument('--why', default=None, help='Why the change is being made (for auditing)')
    parser.add_argument('account', help="Account name to manage")
    subparsers = parser.add_subparsers()
    
    parser_pw = subparsers.add_parser('passwd', help='Set or update password for account')
    parser_pw.set_defaults(func=setpass)
    
    parser_lsents = subparsers.add_parser('list-entities', help='')
    parser_lsents.set_defaults(func=list_entities)
    
    parser_lsnots = subparsers.add_parser('list-notifications', help='')
    parser_lsnots.set_defaults(func=list_notifications)

    parser_mknot = subparsers.add_parser('create-notification', help='Notifications are steps MaaS takes when your alarms are tripped')
    parser_mknot.add_argument('label', help='What to call your notification')
    parser_mknot.add_argument('type', choices=['email', 'pagerduty', 'webhook'])
    parser_mknot.add_argument('detail', help='Email address, URI for webhook, or pagerduty details')
    parser_mknot.set_defaults(func=make_notification)
    
    parser_mknp = subparsers.add_parser('create-notification-plan', help='Notification plans tell MaaS what notifications to run when your alarms are tripped')
    parser_mknp.add_argument('label', help='What to call your notification plan')
    parser_mknp.add_argument('--ok', nargs='+', help='Notification ID(s) to run when alarm changes to OK')
    parser_mknp.add_argument('--warning', nargs='+', help='Notification ID(s) to run when alarm changes to WARNING')
    parser_mknp.add_argument('--critical', nargs='+', help='Notification ID(s) to run when alarm changes to CRITICAL')
    parser_mknp.set_defaults(func=make_notification_plan)
    
    parser_ap = subparsers.add_parser('apply', help='Apply a configured profile to one or more entity IDs')
    parser_ap.add_argument('profile', help='Name of profile from config to apply')
    parser_ap.add_argument('ents', nargs='+', help='Entity IDs to apply profile to')
    parser_ap.add_argument('-p', '--plan', default='npTechnicalContactsEmail', help='Notification Plan ID to use when these alarms are tripped')
    parser_ap.set_defaults(func=apply)
    
    parser_ho = subparsers.add_parser('hose', help='Hose all the checks and alarm on one or more entity IDs')
    parser_ho.add_argument('ents', nargs='+', help='Entity IDs to erase checks and alarms on')
    parser_ho.set_defaults(func=hose)
    
    parser_lstoks = subparsers.add_parser('list-tokens', help='List monitoring agent tokens')
    parser_lstoks.set_defaults(func=lstoks)
    
    parser_mktok = subparsers.add_parser('create-token', help='Create a monitoring agent token')
    parser_mktok.add_argument('-l', '--label', default=None, help='Label your new monitoring agent token')
    parser_mktok.set_defaults(func=mktok)
    
    parser_rmtok = subparsers.add_parser('delete-token', help='Delete a monitoirng agent token')
    parser_rmtok.add_argument('token_id', help='Token ID to delete')
    parser_rmtok.set_defaults(func=rmtok)

    args = parser.parse_args()

    Cls = get_driver(Provider.RACKSPACE)
    driver = Cls(args.account, get_password('hawk', args.account))
    
    args.func(driver, args)