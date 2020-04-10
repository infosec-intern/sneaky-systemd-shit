# DBus

## Description

Dbus is a generic mechanism for communicating with other processes (inter-process communication, or IPC). It allows programs to expose APIs via objects, methods, and properties, and systemd makes heavy use of it. The systemd `Manager` object, and each unit type, have their own APIs, such as `StartUnit()`, `SetEnvironment()`, `ReloadUnit()`, etc. Every action possible with the `systemctl` command is exposed via systemd's dbus API.

**Source**: <https://www.freedesktop.org/wiki/Software/systemd/dbus/>

## Additional Notes

* Unfortunately, systemd's dbus parameters aren't named in an obvious way when doing introspection, so we have to consult the dbus API documentation ([here](https://www.freedesktop.org/wiki/Software/systemd/dbus/)) and look up the function names to understand what systemd is looking for.
* When using the dbus method `LinkUnitFiles` there is no need to reload the systemd configuration via the `systemctl daemon-reload` command. This is also the case when using `systemctl link`, because it uses this method. There is also no need to ensure the relevant folders exist in the path (e.g. `~/.config/systemd/user`). Systemd will create them if necessary
* Interacting with units via dbus frequently requires specifying a service mode. From [the documentation](https://www.freedesktop.org/wiki/Software/systemd/dbus/), "The mode needs to be one of replace, fail, isolate, ignore-dependencies, ignore-requirements."

### busctl

**Source**: <https://www.freedesktop.org/software/systemd/man/busctl.html>

#### Additional Notes

* `busctl` will suggest or auto-complete (using <TAB>) many of the values it needs up until method parameters are required. This is a great way to quickly view the parameter types for a method without using introspection
* A quick way to view units running from non-standard locations  with `busctl` is:

```sh
# Standard user-based locations on my systemd:
#     /usr/lib/
#     /run/user/${UID}
$ busctl --user call org.freedesktop.systemd1 /org/freedesktop/systemd1 org.freedesktop.systemd1.Manager ListUnitFiles --j=short \
      | jq '.data[][][0]' \
      | grep -Ev "/usr/lib/|/run/user/${UID}"
"/home/username/.config/systemd/user/basic.service"
```

```sh
# Standard systemd-based locations:
#     /lib/systemd/system
#     /run/systemd
#     /etc/systemd/system
$ busctl --system call org.freedesktop.systemd1 /org/freedesktop/systemd1 org.freedesktop.systemd1.Manager ListUnitFiles --j=short \
      | jq '.data[][][0]' \
      | grep -Ev "/lib/systemd/system|/run/systemd|/etc/systemd/system"
```

#### Step by Step

1. View the parameters required by the `LinkUnitFiles` method

```sh
$ busctl --user introspect org.freedesktop.systemd1 /org/freedesktop/systemd1 org.freedesktop.systemd1.Manager | grep -E "(NAME|LinkUnitFiles)"
NAME                                      TYPE      SIGNATURE        RESULT/VALUE                             FLAGS
.LinkUnitFiles                            method    asbb             a(sss)                                   -
```

The parameter set shows the input parameters are an array of strings (`as`) and two booleans (`bb`). The first parameter is a list of files to link. The second parameter indicates whether to install this unit in the user's runtime directory at `$XDG_RUNTIME_DIR` (true) or the user's `~/.config/systemd/user` directory (false). The third parameter is a boolean indicating whether to force the link creation or not (consult the Additional Notes for how these were identified).

2. Install the `basic.service` file from the BasicService example into the systemd user folder

```sh
$ busctl --user call org.freedesktop.systemd1 /org/freedesktop/systemd1 org.freedesktop.systemd1.Manager LinkUnitFiles asbb 1 "/tmp/basic.service" false true
a(sss) 1 "symlink" "/home/username/.config/systemd/user/basic.service" "/tmp/basic.service"
```

3. View the parameter types required by the `StartUnit` systemd method

```sh
$ busctl introspect org.freedesktop.systemd1 /org/freedesktop/systemd1 org.freedesktop.systemd1.Manager | grep -E "(NAME|StartUnit )"
NAME                                      TYPE      SIGNATURE        RESULT/VALUE                             FLAGS
.StartUnit                                method    ss               o                                        -
```

The parameter set shows the input parameters are two strings (`ss`). The first parameter is a service name, and the second is a service mode (consult the Additional Notes for how these were identified).

4. Start the unit using `busctl`

```sh
$ busctl --user call org.freedesktop.systemd1 /org/freedesktop/systemd1 org.freedesktop.systemd1.Manager StartUnit "ss" basic.service fail
o "/org/freedesktop/systemd1/job/3132"
```

### gdbus

The `gdbus` program is a command-line tool that provides access to the various DBus APIs available in the system. It is specific to systems with the GNOME display manager installed. The KDE equivalent to this is `qdbus`.

**Source**: <https://www.freedesktop.org/software/gstreamer-sdk/data/docs/latest/gio/gdbus.html>

#### Step by Step

1. View the parameter types required by the `LinkUnitFiles` systemd method

```sh
$ gdbus introspect --session --dest org.freedesktop.systemd1 --object-path /org/freedesktop/systemd1 | grep LinkUnitFiles -A3
      LinkUnitFiles(in  as arg_0,
                    in  b arg_1,
                    in  b arg_2,
                    out a(sss) arg_3);
```

2. Install the `basic.service` file from the BasicService example into the systemd user folder

3. View the parameter types required by the `StartUnit` systemd method

```sh
$ gdbus introspect --session --dest org.freedesktop.systemd1 --object-path /org/freedesktop/systemd1 | grep 'StartUnit(' -A2
      StartUnit(in  s arg_0,
                in  s arg_1,
                out o arg_2);
```

4. Start the unit using `gdbus`

```sh
$ gdbus call --session --dest org.freedesktop.systemd1 --object-path /org/freedesktop/systemd1 --method org.freedesktop.systemd1.Manager.StartUnit basic.service fail
(objectpath '/org/freedesktop/systemd1/job/2769',)
```

### dbus API

**Source**: <https://www.freedesktop.org/wiki/Software/systemd/dbus/>

#### Additional Notes

#### Step by Step
