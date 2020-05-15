#!/usr/bin/env python3
import argparse
import dbus
from os import environ
from getpass import getuser
import logging
import re


'''
Useful resources
    https://www.freedesktop.org/wiki/Software/systemd/dbus/
    https://dbus.freedesktop.org/doc/dbus-python/tutorial.html
    https://medium.com/@trstringer/talking-to-systemd-through-dbus-with-python-53b903ee88b1
'''

SYS_BUS = dbus.SystemBus()
SYSTEMD = SYS_BUS.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
SYS_MANAGER = dbus.Interface(SYSTEMD, 'org.freedesktop.systemd1.Manager')
LOGIND = SYS_BUS.get_object('org.freedesktop.login1', '/org/freedesktop/login1')
LOGIN_MANAGER = dbus.Interface(LOGIND, 'org.freedesktop.login1.Manager')


def pupy_list_services(service_filter=None):
    '''
        Copied & slightly modified from PupyRAT
        https://github.com/n1nj4sec/pupy/blob/d22bf22900835d1389ec5cfeffdb5fa98d38f798/pupy/packages/linux/all/services.py

        Data returned by dbus' ListUnits()
            The primary unit name as string
            The human readable description string
            The load state (i.e. whether the unit file has been loaded successfully)
            The active state (i.e. whether the unit is currently started or not)
            The sub state (a more fine-grained version of the active state that is specific to the unit type, which the active state is not)
            A unit that is being followed in its state by this unit, if there is any, otherwise the empty string.
            The unit object path
            If there is a job queued for the job unit the numeric job id, 0 otherwise
            The job type as string
            The job object path
    '''
    for unit_name, _, _, _, _, _, unit_object, _, _, _ in SYS_MANAGER.ListUnits():
        if not unit_name.endswith('service') or (service_filter and not re.match(service_filter, unit_name)):
            continue

        service = SYS_BUS.get_object(SYSTEMD.requested_bus_name, unit_object)
        # don't need to do this to change properties and exec a new command
        # but we do need it to view old properties
        unit_props = service.GetAll('org.freedesktop.systemd1.Unit', dbus_interface='org.freedesktop.DBus.Properties')
        svc_props = service.GetAll('org.freedesktop.systemd1.Service', dbus_interface='org.freedesktop.DBus.Properties')

        try:
            exec_start = ' '.join(svc_props.get('ExecStart')[0][1])
        except IndexError:
            exec_start = None

        logging.info('Current unit id: {}'.format(unit_props['Id']))
        logging.info('Current unit name(s): {}'.format(', '.join([name for name in unit_props['Names']])))
        logging.info('Loaded & active? {} {}'.format(unit_props['LoadState'], unit_props['ActiveState']))
        logging.info('Current description: {}'.format(unit_props['Description']))
        logging.info('Current unit location: {}'.format(unit_props['SourcePath']))
        logging.info('Available drop-ins: {}'.format(', '.join([dropin for dropin in unit_props['DropInPaths']])))
        logging.info('Can Start? {}'.format(True if unit_props['CanStart'] == 1 else False))
        logging.info('Can Stop? {}'.format(True if unit_props['CanStop'] == 1 else False))
        logging.info('Service Type: {}'.format(svc_props['Type']))
        logging.info('Current command: {}'.format(exec_start))
        logging.info('')

def start_transient_unit(cmd, **kwargs):
    '''
        dbus API
            StartTransientUnit(s_name, s_mode, props, aux)
    '''
    logging.debug('Running command "%s" via dbus StartTransientUnit', cmd)
    current_user = getuser()

    name = kwargs.get('name')
    if name is None:
        name = 'start-transient-cmd'
    if not name.endswith('.service'):
        name += '.service'

    mode = kwargs.get('mode', 'fail')

    description = kwargs.get('description')
    if description is None:
        description = 'Transient unit run by {}'.format(__file__)

    unit_properties = dbus.Array([
        dbus.Struct(("Type", "simple")),
        dbus.Struct(("Description", description)),
        dbus.Struct(("ExecStart", cmd)),
        dbus.Struct(("User", current_user))
    ])
    aux = dbus.Array([])

    job = SYS_MANAGER.StartTransientUnit(name, mode, unit_properties, aux)
    logging.info(job)

def user_info(user_filter=None):
    '''
        dbus API
            ListUsers(out a(uso) user_list);
    '''
    for _, user_name, user_path in LOGIN_MANAGER.ListUsers():
        if user_filter and user_name != user_filter:
            continue
        user = SYS_BUS.get_object(LOGIND.requested_bus_name, user_path)
        user_props = user.GetAll('org.freedesktop.login1.User', dbus_interface='org.freedesktop.DBus.Properties')

        logging.info('Username: %s', user_props['Name']),
        logging.info('UID=%s', user_props['UID'])
        logging.info('GID: %s', user_props['GID'])
        logging.info('Runtime Path: %s', user_props['RuntimePath'])
        logging.info('Status: %s', user_props['State'])
        logging.info('Sessions:')
        for session in user_props['Sessions']:
            logging.info('  %s: %s', session[0], session[1])
        logging.info('')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    parser = argparse.ArgumentParser(description='Simple cli utility for playing with systemd via dbus')
    subparsers = parser.add_subparsers(title='Actions', description='Possible actions to perform', dest='action')
    list_parser = subparsers.add_parser('list', help='List services')
    list_parser.add_argument('-s', '--service', help='Filter services matching the given name or pattern', default=None)
    run_parser = subparsers.add_parser('run', help='Run a given command as a transient unit')
    run_parser.add_argument('command', help='Command to run')
    run_parser.add_argument('--name', help='Name to assign to the transient unit', default='run-transient-cmd')
    run_parser.add_argument('--description', help='Description to assign to the transient unit', default=None)
    user_parser = subparsers.add_parser('users', help='List user info')
    user_parser.add_argument('-n', '--username', help='Only display information about the user identified by this username')

    args = parser.parse_args()

    if args.action == 'list':
        pupy_list_services(args.service)
    elif args.action == 'run':
        start_transient_unit(args.command, name=args.name, description=args.description)
    elif args.action == 'users':
        user_info(args.username)
    else:
        parser.print_help()
