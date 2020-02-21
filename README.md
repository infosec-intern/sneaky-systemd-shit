# Sneaky systemd Shit

A simple repository for tracking the many ways to turn [systemd](https://www.freedesktop.org/wiki/Software/systemd/) into an offensive tool

## Mindset

I'll be using the [MITRE ATT&CK](https://attack.mitre.org/) framework to guide techniques here,
 and I'll explain the similarities and differences between systemd on Linux and the equivalent technique on Windows, if one exists.

## The Goods

* [Examples/BasicService](Examples/BasicService/BasicService.md)
* [Examples/Autoruns](Examples/Autoruns/Autoruns.md)
* [Examples/BindShell](Examples/BindShell/BindShell.md)
* [Examples/NetcatWithoutTheE](Examples/NetcatWithoutTheE/NetcatWithoutTheE.md)
* [Examples/ProxyInitialization](Examples/ProxyInitialization/ProxyInitialization.md)
* [Examples/ScheduledReverseShell](Examples/ScheduledReverseShell/ScheduledReverseShell.md)
* [Examples/TmpFiles](Examples/TmpFiles/TmpFiles.md)
* [Examples/VimShell](Examples/VimShell/VimShell.md)

## Basic Components

* [systemctl](https://www.freedesktop.org/software/systemd/man/systemctl.html)
  * Primary means of interacting with systemd. Listing, loading, starting, stopping units all happens through here
* [Units](https://www.freedesktop.org/software/systemd/man/systemd.unit.html)
  * systemd's configuration file format. Every unit file type (service, timer, device, etc.) must follow a similar syntax
  * Can be created dynamically at runtime via API calls - these are called transient units
    * Exist only while running - get destroyed when deactivated or the system shuts down
    * <https://www.freedesktop.org/wiki/Software/systemd/ControlGroupInterface/>

## Enterprise Tactics

<https://attack.mitre.org/tactics/enterprise/>

### Initial Access

Represents the vectors adversaries use to gain an initial foothold within a network.

### Execution

Represents techniques that result in execution of adversary-controlled code on a local or remote system.

* [Unit Hooking](https://www.freedesktop.org/software/systemd/man/systemd.unit.html#Description)
  * It's possible to hook into unit files without modifying the units themselves a couple ways:
    * wants: A directory, `foo.service.wants/` in one of the unit search directories will implicitly add units from the directory as `Wants=` directives
    * requires: Same as above, but with `foo.service.requires/` and the `Requires=` directive
    * drop-ins: A drop-in directory can also be created (`foo.service.d/`) to load .conf files into the unit
      * These must be placed in the same directory that the service is in, so system-level and user-level cannot intermingle

### Persistence

Any access, action, or configuration change to a system that gives an adversary a persistent presence on that system.

* [Services](https://www.freedesktop.org/software/systemd/man/systemd.service.htm)
  * systemd's bread and butter. Controls how systemd interacts with processes, including managing daemons
  * Before= and After= in a service file MIGHT be used alongside `shutdown.target` and `local-fs.target`, respectively, to load a file into memory and write to-disk to maintain persistence
    * `local-fs.target` is needed instead of `boot-complete.target` to ensure the system has the filesystem loaded
* User-Mode
  * Many systemd commands can use the `--user` flag to stay within the current user's context and not trigger an admin password prompt
  * The following workflow would allow someone with only user permissions to execute code
    1. Link a unit file from an arbitrary location to `$HOME/.config/systemd/user`
    2. `systemctl --user daemon-reload` to reload the list of unit files in the user's context
    3. `systemctl --user start $SERVICE` to run the code in the `ExecStart=` directive

### Privilege Escalation

The result of actions that allows an adversary to obtain a higher level of permissions on a system or network.

* [systemd-run]
  * It's possible to invoke a root shell without using `sudo` or `su` to switch accounts.
  This is an easy way to escalate privileges without tripping simple CLI detections
    * The `auditd` module will still log a `USER_AUTH:res=success` message with the `acct` field indicating the username of the escalating account
      and a `SERVICE_START` message with the unit name `run-u[0-9]+`

  ```sh
  $ systemd-run --shell
  # whoami
  root
  ```

### Defense Evasion

Techniques an adversary may use to evade detection or avoid other defenses.

* [Machinectl](https://www.freedesktop.org/software/systemd/man/machinectl.html)
  * Interact with systemd virtual machines and the container registration manager
  * Part of the `systemd-container` package on Ubuntu
  * Available in a default install of Arch Linux
  * Privileged login required to access a shell

  ```sh
  $ machinectl --uid=1001 shell
  ==== AUTHENTICATING FOR org.freedesktop.machine1.host-shell ===
  Authentication is required to acquire a shell on the local host.
  Authenticating as: ,,, (privileged)
  Password:
  ==== AUTHENTICATION COMPLETE ===
  Connected to the local host. Press ^] three times within 1s to exit session.
  $ id
  uid=1001(unprivileged) gid=1001(unprivileged) groups=1001(unprivileged)
  $
  ```

* [Refuse Unit Deactivation](https://www.freedesktop.org/software/systemd/man/systemd.unit.html#RefuseManualStart=)
  * A couple Unit directives, `RefuseManualStart=` and `RefuseManualStop=`, give the unit writer control over whether a normal user can start/stop a given unit
    * Super interesting for anti-analysis
* [systemd-detect-virt](https://www.freedesktop.org/software/systemd/man/systemd-detect-virt.html)
  * Detect if systemd is running in a VM. Also done in the [ConditionVirtualization](https://www.freedesktop.org/software/systemd/man/systemd.unit.html#ConditionVirtualization=) option of unit files.
    Example below is in a new Ubuntu 16.04.6 server on Digital Ocean:

  ```sh
  $ systemd-detect-virt
  kvm
  ```

  * Another method for detecting virtualization is using `gdbus`:
    * This comes from a blog post by the systemd developers: <http://0pointer.de/blog/projects/detect-virt.html>

  ```sh
  $ gdbus call --system --dest org.freedesktop.systemd1 --object-path /org/freedesktop/systemd1 --method org.freedesktop.DBus.Properties.Get org.freedesktop.systemd1.Manager Virtualization
  (<'kvm'>,)
  ```

* [ConditionSecurity](https://www.freedesktop.org/software/systemd/man/systemd.unit.html#ConditionSecurity=)
  * Enable or disable (by negating with `!`) a unit from running if a given security technology is deployed on the system
  * All `Condition*` options in unit files have an equivalent `Assert*` option that fails loudly if the condition is not met.
    This is probably not too useful to hiding on a system (easier to get caught) but could be used by security tools to loudly
    show they were disabled

### Credential Access

Techniques resulting in access to or control over system, domain, or service credentials that are used within an enterprise environment.

### Discovery

Techniques that allow the adversary to gain knowledge about the system and internal network.

* [systemctl](https://www.freedesktop.org/software/systemd/man/systemctl.html)
  * `systemctl show` will display various properties that systemd is using that may be relevant for assessing a system's posture
  * `systemctl list-units` gives a detailed rundown of the processes systemd is managing along with the descriptions listed in their unit files
  * `systemctl cat <unit>` displays a specific unit file
  * `systemctl --user` modifies the command to use the current user's context instead of the system manager (e.g. `systemctl list-units --user`)
  * `systemd-analyze unit-paths` displays the current list of paths that systemd units are loaded from
  * `systemd-analyze --user unit-paths` displays the current list of paths that a regular user can use to load systemd units
    * If this is not available, `systemctl` can be substituted like below:

    ```sh
    $ for p in $(systemctl --user show -p UnitPath | cut -d= -f2); do echo $p; done
    /home/privileged/.config/systemd/user
    /etc/systemd/user
    /run/user/1000/systemd/user
    /run/systemd/user
    /home/privileged/.local/share/systemd/user
    /usr/local/share/systemd/user
    /usr/share/systemd/user
    /usr/local/lib/systemd/user
    /usr/lib/systemd/user
    ```

  * `systemd-path` displays a list of paths with human-readable purposes (e.g. temporary: /tmp)
* [Busctl](https://www.freedesktop.org/software/systemd/man/busctl.html) (?)
  * Introspect and monitor the D-Bus bus
  * MIGHT be helpful to monitor or inspect buses of various units
  * Based on code in PupyRAT, units can be injected/started directly on the bus
* [Unit Conditions](https://www.freedesktop.org/software/systemd/man/systemd.unit.html#ConditionArchitecture=)
  * systemd will silently check to see if certain conditions about the running system are met before starting a unit
  * Could be good for fingerprinting, identifying VMs (see Defense Evasion), identifying security features, or limiting execution to specific hosts

### Lateral Movement

Techniques that enable an adversary to access and control remote systems on a network.

### Collection

Techniques used to identify and gather information, such as sensitive files, from a target network prior to exfiltration.

* Show running processes with cgroups

```sh
$ alias psc='ps xawf -eo pid,user,cgroup,args'
$
```

### Exfiltration

Techniques and attributes that result or aid in the adversary removing files and information from a target network.

### Command and Control

Represents how adversaries communicate with systems under their control within a target network.

#### DNS

* [systemd-resolve](https://www.freedesktop.org/software/systemd/man/systemd-resolved.html)
  * Can be used to perform DNS tunneling just like `nslookup.exe` is used on Windows systems

  ```sh
  $ systemd-resolve --protocol dns --type mx google.com
    google.com. IN MX    20 alt1.aspmx.l.google.com
    google.com. IN MX    30 alt2.aspmx.l.google.com
    google.com. IN MX    40 alt3.aspmx.l.google.com
    google.com. IN MX    10 aspmx.l.google.com
    google.com. IN MX    50 alt4.aspmx.l.google.com

    -- Information acquired via protocol DNS in 6.9ms.
    -- Data is authenticated: no
  ```
