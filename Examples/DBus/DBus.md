# DBus

Dbus is a generic mechanism for communicating with other processes (inter-process communication, or IPC) both local and remote. It allows programs to expose APIs via objects, methods, and properties, and systemd makes heavy use of it. The systemd `Manager` object, and each unit type, have their own APIs, such as `StartUnit()`, `SetEnvironment()`, `ReloadUnit()`, etc. Every action possible with the `systemctl` command is exposed via systemd's dbus API.

**Source**: <https://www.freedesktop.org/wiki/Software/systemd/dbus/>

## Description

### gdbus

**Source**: <https://developer.gnome.org/gio/unstable/gdbus.html>

#### Additional Notes

* Unfortunately, systemd's dbus parameters aren't named in an obvious way when doing introspection, so we have to consult the dbus API documentation ([here](https://www.freedesktop.org/wiki/Software/systemd/dbus/)) to understand what systemd is looking for.
* Interacting with units via dbus frequently requires specifying a service mode. From [the documentation](https://www.freedesktop.org/wiki/Software/systemd/dbus/), "The mode needs to be one of replace, fail, isolate, ignore-dependencies, ignore-requirements."

#### Step by Step

1. Install the `basic.service` file from the BasicService example into the systemd user folder and reload the units

```sh
$ mkdir -p ~/.config/systemd/user/
$ ln -s `pwd`../BasicService/basic.service ~/.config/systemd/user/
$ systemctl --user daemon-reload
```

2. View the parameters required by the `StartUnit` systemd method

```sh
$ gdbus introspect --session --dest org.freedesktop.systemd1 --object-path /org/freedesktop/systemd1 | grep 'StartUnit(' -A2
      StartUnit(in  s arg_0,
                in  s arg_1,
                out o arg_2);
```

The parameter set shows the first two values are input parameters (indicated by `in`) of type string (indicated by the `s`). The first parameter is a service name, and the second is a service mode (consult the documentation or Additional Notes for how these were identified).

3. Start the unit using `gdbus`

```sh
$ gdbus call --session --dest org.freedesktop.systemd1 --object-path /org/freedesktop/systemd1 --method org.freedesktop.systemd1.Manager.StartUnit basic.service fail
(objectpath '/org/freedesktop/systemd1/job/2769',)
```

### busctl

**Source**: <>

#### Additional Notes

#### Step by Step

### dbus API

**Source**: <https://www.freedesktop.org/wiki/Software/systemd/dbus/>

#### Additional Notes

#### Step by Step
