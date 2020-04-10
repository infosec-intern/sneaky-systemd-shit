# Transient Units

## Description

This section walks through additional methods of generating systemd units outside the normal method of creating `.ini` files. Since there isn't a file on disk to refer to, systemd calls units created this way "transient units".

Both of these methods require either root access or interactive authentication (AFAICT via Polkit) to work. This seems to be an attempt to disallow scripts from creating/running units without apporpriate permissions, but I'm still investigating ways of getting around it.

## systemd-run

Systemd comes with a helpful tool for generating transient units: `systemd-run`. This is primarily meant to execute `.service` and `.scope` units, but it can also be used to create transient `.path`, `.timer`, and `.socket` units, which are linked to transient `.service` and `.scope` units. During execution, transient units can be accessed with the same tools that normal units can be accessed with; namely, `systemctl`. In fact, during execution, unit files are placed in the `/run/systemd/transient/` directory for the lifespan of the service.

**Source**: <https://www.freedesktop.org/software/systemd/man/systemd-run.html>

### Step by Step

1. Run a basic `echo` command and check the journal for output

```sh
$ systemd-run --description="Basic Service" --service-type=oneshot echo "hello world"
Running as unit: run-u19010.service
```

```sh
$ journalctl -u run-u19010.service
<snip>
Apr 03 15:30:18 localhost systemd[1]: Starting Basic Service...
Apr 03 15:30:18 localhost echo[21535]: hello world
Apr 03 15:30:18 localhost systemd[1]: run-u19010.service: Succeeded.
Apr 03 15:30:18 localhost systemd[1]: Started Basic Service.
```

2. Run the `sleep` command and view it with `systemctl` and the temporary files backing it

```sh
$ systemd-run sleep 100
Running as unit: run-u19305.service
```

```sh
$ systemctl status run-u19305
● run-u19305.service - /usr/bin/sleep 100
   Loaded: loaded (/run/systemd/transient/run-u19305.service; transient)
Transient: yes
   Active: active (running) since Fri 2020-04-03 15:33:23 MDT; 5s ago
 Main PID: 21622 (sleep)
    Tasks: 1 (limit: 4915)
   Memory: 152.0K
   CGroup: /system.slice/run-u19305.service
           └─21622 /usr/bin/sleep 100

Apr 03 15:33:23 colossus systemd[1]: Started /usr/bin/sleep 100.
```

```sh
$ cat /run/systemd/transient/run-u19305.service
# This is a transient unit file, created programmatically via the systemd API. Do not edit.
[Unit]
Description=/usr/bin/sleep 100

[Service]
ExecStart=
ExecStart=@/usr/bin/sleep "/usr/bin/sleep" "100"
```

## DBus

Refer to [../DBus/Dbus.md] for more information on systemd's dbus API.

### Step by Step

```sh
# TODO: figure out what "no such device or address" refers to
$ busctl --user call org.freedesktop.systemd1 /org/freedesktop/systemd1 org.freedesktop.systemd1.Manager StartTransientUnit "ssa(sv)a(sa(sv))" transient.service replace 2 Type as 1 simple ExecStart as 1 "/bin/touch /tmp/test.txt" 0
No such device or address
```

```sh
# TODO: figure out what "no such device or address" refers to
 gdbus call --session --dest org.freedesktop.systemd1 --object-path /org/freedesktop/systemd1 --method org.freedesktop.systemd1.Manager.StartTransientUnit "transient.service" "replace" "[('Type',<'simple'>),('ExecStart',<'/bin/echo hello'>)]" []
Error: GDBus.Error:System.Error.ENXIO: No such device or address
```
