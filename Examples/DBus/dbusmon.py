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
    parser.add_argument("--fallback", action='store_true', help="Create a generic fallback handler for signals")
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

def get_properties(object_path: str, interface: str):
    '''
    Get the properties of the provided object's interface.
    Typically, the interface would be something like 'org.freedesktop.systemd1.Job' to retrieve the job's ID and unit path
    '''
    # shorthand method that skips dbus.Interface() instantiation. Ugly IMO though
    #   proxy = bus.get_object(systemd.requested_bus_name, object_path)
    #   properties = proxy.get_dbus_method('GetAll', dbus_interface='org.freedesktop.DBus.Properties')(interface)
    proxy = bus.get_object(systemd.requested_bus_name, object_path)
    properties_iface = dbus.Interface(proxy, 'org.freedesktop.DBus.Properties')
    return properties_iface.GetAll(interface)

def get_unittype(unit_id: str):
    return str(unit_id.split(".")[-1]).capitalize()

def print_jobnew(job_id: dbus.UInt32, job_path: dbus.ObjectPath, unit_name: dbus.String):
    try:
        # sometimes a Job ID will not exist when querying its properties this way...
        #   job_properties = get_properties(job_path, 'org.freedesktop.systemd1.Job')
        #   _, unit_path = job_properties['Unit']
        # so we'll use the systemd Manager object to grab our unit path instead - it will always return a value if a unit is loaded
        unit_path = systemd.get_dbus_method('GetUnit', dbus_interface='org.freedesktop.systemd1.Manager')(unit_name)
        unit_properties = get_properties(unit_path, 'org.freedesktop.systemd1.Unit')
        # real_unit_path displays path to actual file on filesystem
        # unit_path displays systemd object path - always starts with '/org/freedesktop/systemd1/unit/'
        real_unit_path = unit_properties.get('FragmentPath')
        unit_type = get_unittype(unit_name)
        sub_properties = get_properties(unit_path, "org.freedesktop.systemd1.{}".format(unit_type))
        if unit_type == 'Service':
            _, cli, _, _, _, _, _, _, _, _  = sub_properties.get('ExecStart', [])[0]
            logging.info("Job %d ran '%s': \"%s\"", job_id, real_unit_path, ' '.join(cli))
        else:
            logging.info("Job %d ran unit '%s': %s @ '%s'", job_id, job_path, unit_name, real_unit_path)
    except dbus.exceptions.DBusException as err:
        logging.exception("Couldn't print info for signal JobNew '%s' (%s): %s", job_id, unit_name, err)

def print_jobremoved(job_id: dbus.UInt32, job_path: dbus.ObjectPath, unit_name: dbus.String, result: dbus.String):
    try:
        if result == 'done':
            logging.info("Job %d finished with unit '%s'", job_id, unit_name)
        else:
            logging.info("Received signal 'JobRemoved': %s %s %s %s", job_id, job_path, unit_name, result)
    except dbus.exceptions.DBusException as err:
        logging.exception("Couldn't print info for signal JobRemoved '%s' (%s): %s", job_id, unit_name, err)

def print_reloading(active: bool):
    logging.info("Started reloading" if active else "Finished reloading")

def print_startupfinished(firmware, loader, kernel, initrd, userspace, total):
    logging.info("Received signal 'StartupFinished': %s, %s, %s, %s, %s, %s", firmware, loader, kernel, initrd, userspace, total)

def print_unitnew(unit_id: dbus.UInt32, unit_path: dbus.ObjectPath):
    unit_properties = get_properties(unit_path, 'org.freedesktop.systemd1.Unit')
    real_unit_path = unit_properties.get('FragmentPath')
    unit_type = get_unittype(unit_properties['Id'])
    sub_properties = get_properties(unit_path, "org.freedesktop.systemd1.{}".format(unit_type))
    if unit_type == 'Service':
        _, cli, _, _, _, _, _, _, _, _  = sub_properties.get('ExecStart', [])[0]
        logging.info("Created new unit '%s': \"%s\"", real_unit_path, ' '.join(cli))
    else:
        logging.info("Received signal 'UnitNew': %s %s", unit_id, unit_path)

def print_unitremoved(unit_id: dbus.UInt32, unit_path: dbus.ObjectPath):
    unit_properties = get_properties(unit_path, 'org.freedesktop.systemd1.Unit')
    real_unit_path = unit_properties.get('FragmentPath')
    logging.info("Removed unit '%s'", real_unit_path)

def print_unitfileschanged():
    logging.info("Received signal 'UnitFilesChanged'")

def print_signal(*args):
    logging.info("Generic signal handler: %s", args)

def set_signal_handlers(bus, systemd, manager, generic=True):
    SYSTEMD_SIGNALS = {
        # these two signals run into infinite loops when not using the fallback handler ... not sure why
        # 'UnitNew': print_unitnew,
        # 'UnitRemoved': print_unitremoved,
        'JobNew': print_jobnew,
        'JobRemoved': print_jobremoved,
        'StartupFinished': print_startupfinished,
        'UnitFilesChanged': print_unitfileschanged,
        'Reloading': print_reloading
    }
    # subscribe to its DBus signals
    manager.Subscribe()
    # listen to the signals and react accordingly
    for signal, handler in SYSTEMD_SIGNALS.items():
        match = bus.add_signal_receiver(
            handler, signal_name=signal, bus_name=manager.bus_name, dbus_interface=manager._dbus_interface, path=systemd.object_path
        )
        logging.info("Subscribing to '%s' signals on bus '%s' (%s)", match._member, match._interface, match.sender)
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
    set_signal_handlers(bus, systemd, manager, generic=args.fallback)
    loop = GLib.MainLoop()
    loop.run()
