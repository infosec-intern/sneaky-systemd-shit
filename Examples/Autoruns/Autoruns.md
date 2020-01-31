# Systemd Autoruns

## Description

This section walks through various methods of automatically executing code,
much like Windows "Autoruns" registry entries.

## Target Wants

In systemd, targets are unit files which are "used for grouping units and as well-known synchronization points during start-up".
For systemd to know which unit files a specific target activates, it uses the `Wants` and `Requires` directives in the target's unit file,
or `<target>.wants/` and `<target>.requires/` directories with links to the units to activate.

These directories are easy places to store symbolic links to attacker-controlled unit files, especially service files which will then activate
once the specified target is executed. The following walkthrough will detail identifying the default target and placing a service file
in its `.wants/` directory to execute a command during the boot process.

**Source**: <https://www.freedesktop.org/software/systemd/man/systemd.target.html>

### Additional Notes

* Root access is required to write into the default target's `.wants/` directories
* Unit files can be anywhere on the filesystem - they only must be linked into the appropriate directory

### Step by Step

1. Generate the service file

```ini
$ cat autorun.service
; https://www.freedesktop.org/software/systemd/man/systemd.service.html
[Unit]
Description=Basic service
Documentation=https://github.com/infosec-intern/sneaky-systemd-shit

[Service]
Type=oneshot
ExecStart=/bin/echo "autoruns ftw"
```

2. Identify the default target

```sh
$ systemctl get-default
graphical.target
```

3. Identify the default target's `.wants/` directories

```sh
$ find / -type d -name graphical.target.wants -exec ls -ld {} \;
drwxr-xr-x 2 root root 4096 Dec 20 09:30 /etc/systemd/system/graphical.target.wants
drwxr-xr-x 2 root root 4096 Dec 20 09:11 /usr/lib/systemd/system/graphical.target.wants
```

4. Install the service

```sh
$ sudo ln -s `pwd`/autorun.service /etc/systemd/system/graphical.target.wants
$
```

5. Reboot the system to trigger the target and check the journal for output

```sh
$ journalctl -b 0 | grep -i "echo"
Jan 31 04:34:05 localhost echo[1566]: autoruns ftw
```
