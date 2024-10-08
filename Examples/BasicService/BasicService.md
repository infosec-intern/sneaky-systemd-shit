# Systemd Services

## Description

This sequence of commands sets up a simple "hello world" service with an added configuration.

The service file (`basic.service`) uses:

* The `ExecStart` directive to execute a simple command

## Additional Notes

* The `ExecStart` directive located in the `basic.service.d/hellomars.conf` file will execute
  after the `ExecStart` directive in the `basic.service` unit file
* The `oneshot` type tells systemd to just run the command and not expect a persistence process

## Step by Step

1. Generate the service file

```ini
; https://www.freedesktop.org/software/systemd/man/systemd.service.html
[Unit]
Description=Basic service
Documentation=https://github.com/infosec-intern/sneaky-systemd-shit

[Service]
Type=oneshot
ExecStart=/bin/echo "hello world"
```

2. Install into the systemd user folder and reload the units

```sh
$ mkdir -p ~/.config/systemd/user/
$ ln -s `pwd`/basic.service ~/.config/systemd/user/
$ systemctl --user daemon-reload
```

3. Execute it and check the journal for output

```sh
$ systemctl --user start fake
$ journalctl -e | grep "basic.service" -B1
Jan 21 09:35:42 localhost echo[26493]: hello world
Jan 21 09:35:42 localhost systemd[2006]: basic.service: Succeeded.
```

4. Add in the configuration file and folder

```sh
$ ln -s `pwd`/basic.service.d/ ~/.config/systemd/user/systemd/user
```

```ini
$ systemctl --user cat basic.service
; https://www.freedesktop.org/software/systemd/man/systemd.service.html
[Unit]
Description=Basic service
Documentation=https://github.com/infosec-intern/sneaky-systemd-shit

[Service]
Type=oneshot
ExecStart=/bin/echo "hello world"

# /path/to/basic.service.d/hellomars.conf
[Service]
ExecStart=/bin/echo "hello mars"
```

5. Execute it again and check the journal for output - the `hellomars.conf` file should have executed too

```sh
systemctl --user start fake
$ journalctl -e | grep "basic.service" -B2
Jan 21 09:39:11 localhost echo[26747]: hello world
Jan 21 09:39:11 localhost echo[26748]: hello mars
Jan 21 09:39:11 localhost systemd[2006]: basic.service: Succeeded.
```
