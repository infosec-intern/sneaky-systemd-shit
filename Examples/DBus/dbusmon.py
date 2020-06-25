#!/usr/bin/env python3
import argparse
import logging

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

'''
Useful resources
    https://www.freedesktop.org/wiki/Software/systemd/dbus/
    https://dbus.freedesktop.org/doc/dbus-python/tutorial.html
    https://trstringer.com/python-systemd-dbus/
'''

def _set_args():
    parser = argparse.ArgumentParser(description='Simple cli utility for monitoring systemd signals using DBus')
    bus_type = parser.add_mutually_exclusive_group(required=False)
    bus_type.add_argument('--session', action='store_const', const='session', dest='bus')
    bus_type.add_argument('--system', action='store_const', const='system', dest='bus')
    bus_type.set_defaults(bus='system')
    args = parser.parse_args()
    return args

def _set_bus(bus_type: str):
    ''' Instantiate the apporpriate systemd manager based on the given bus type '''
    DBusGMainLoop(set_as_default=True)
    if bus_type == 'system':
        bus = dbus.SystemBus()
    elif bus_type == 'session':
        bus = dbus.SessionBus()
    else:
        raise RuntimeError("Unknown bus type '%s'" % bus)
    logging.debug("Instantiated %s bus" % bus_type)
    systemd = bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
    manager = dbus.Interface(systemd, 'org.freedesktop.systemd1.Manager')
    return (bus, systemd, manager)

def print_jobnew(job_id: dbus.UInt32, object_path: dbus.ObjectPath, unit_name: dbus.String):
    logging.info("Job %d ran unit '%s': %s", job_id, object_path, unit_name)

def print_signal(*args):
    logging.info("Generic signal handler: %s", args)

def set_signal_handlers(bus, systemd, manager, generic=True):
    SYSTEMD_SIGNALS = ('UnitNew', 'UnitRemoved', 'JobNew', 'JobRemoved', 'StartupFinished', 'UnitFilesChanged', 'Reloading')
    # subscribe to its DBus signals
    manager.Subscribe()
    # listen to the signals and react accordingly
    for signal in SYSTEMD_SIGNALS:
        handler_name = "handle_{}".format(str(signal).lower())

        print(handler_name)
        # match = bus.add_signal_receiver(
        #     handler, signal_name=signal, bus_name=manager.bus_name, dbus_interface=manager._dbus_interface, path=systemd.object_path
        # )
        # logging.info("Subscribing to '%s' signals on bus '%s' (%s)", match._member, match._interface, match.sender)
    # finally, set a catch-all handler for other signals that may be missed
    if generic:
        match = bus.add_signal_receiver(
            print_signal, signal_name=None, bus_name=manager.bus_name, dbus_interface=manager._dbus_interface, path=systemd.object_path
        )
        logging.info("Set generic signal handler on bus '%s' (%s)", match._interface, match.sender)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    args = _set_args()
    # instantiate necessary objects for the desired systemd bus
    bus, systemd, manager = _set_bus(args.bus)
    set_signal_handlers(bus, systemd, manager)
    loop = GLib.MainLoop()
    loop.run()
