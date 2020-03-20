# Transient Units

## Description

This section walks through additional methods of generating systemd units outside the normal method of creating `.ini` files.

Since there isn't a file on disk to refer to, systemd calls units created this way "transient units".

* We'll emulate the unit file `basic.service` in all the below examples.

### systemd-run

Systemd comes with a helpful tool for generating transient units: `systemd-run`. This is primarily meant to execute `.service` and `.scope` units, but it can also be used to create transient `.path`, `.timer`, and `.socket` units, which are linked to transient `.service` and `.scope` units.

**Source**: <https://www.freedesktop.org/software/systemd/man/systemd-run.html>

## Step by Step

1. Run a basic `echo` command and check the journal for output

```sh
$ systemd-run echo "hello world"
```

```sh
$ sudo journalctl -b 0 | grep -i "hello world"
Mar 20 20:17:00 systemd[1]: Started /bin/echo hello world.
Mar 20 20:17:00 echo[4461]: hello world
```

### dbus API

## Additional Notes

## Step by Step
