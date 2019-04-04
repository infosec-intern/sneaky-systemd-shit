# Sneaky systemd Shit
A simple repository for tracking the many ways to turn [systemd](https://www.freedesktop.org/wiki/Software/systemd/) into an offensive tool

## Mindset
I'll be using the [MITRE ATT&CK](https://attack.mitre.org/) framework to guide techniques here,
 and I'll explain the similarities and differences between systemd on Linux and the equivalent technique on Windows, if one exists.

## Basic Components

* [systemctl](https://www.freedesktop.org/software/systemd/man/systemctl.html)
  * Primary means of interacting with systemd. Listing, loading, starting, stopping units all happens through here
* [Unit Files](https://www.freedesktop.org/software/systemd/man/systemd.unit.html)
  * systemd's configuration file format. Every unit file type (service, timer, device, etc.) must follow a similar syntax

## Enterprise Tactics
https://attack.mitre.org/tactics/enterprise/

### Initial Access
Represents the vectors adversaries use to gain an initial foothold within a network.

### Execution
Represents techniques that result in execution of adversary-controlled code on a local or remote system.

### Persistence
Any access, action, or configuration change to a system that gives an adversary a persistent presence on that system.

* [Services](https://www.freedesktop.org/software/systemd/man/systemd.service.htm)
  * systemd's bread and butter. Controls how systemd interacts with processes, including managing daemons
  * Before= and After= in a service file MIGHT be used alongside `shutdown.target` and `local-fs.target`, respectively, to load a file into memory and write to-disk to maintain persistence
    * `local-fs.target` is needed instead of `boot-complete.target` to ensure the system has the filesystem loaded

### Privilege Escalation
The result of actions that allows an adversary to obtain a higher level of permissions on a system or network.

### Defense Evasion
Techniques an adversary may use to evade detection or avoid other defenses.

* [Machinectl](https://www.freedesktop.org/software/systemd/man/machinectl.html)
  * Interact with systemd virtual machines and the container registration manager

### Credential Access
Techniques resulting in access to or control over system, domain, or service credentials that are used within an enterprise environment.

### Discovery
Techniques that allow the adversary to gain knowledge about the system and internal network.

* [systemctl](https://www.freedesktop.org/software/systemd/man/systemctl.html)
  * `systemctl show` will display various properties that systemd is using that may be relevant for assessing a system's posture
  * `systemctl list-units` gives a detailed rundown of the processes systemd is managing along with the descriptions listed in their unit files
  * `systemctl cat <unit>` displays a specific unit file
  * `systemctl --user` modifies the command to use the current user's context instead of the system manager (e.g. `systemctl list-units --user`)
* [Busctl](https://www.freedesktop.org/software/systemd/man/busctl.html) (?)
  * Introspect and monitor the D-Bus bus
  * MIGHT be helpful to monitor or inspect buses of various units

### Lateral Movement
Techniques that enable an adversary to access and control remote systems on a network.

### Collection
Techniques used to identify and gather information, such as sensitive files, from a target network prior to exfiltration.

### Exfiltration
Techniques and attributes that result or aid in the adversary removing files and information from a target network.

### Command and Control
Represents how adversaries communicate with systems under their control within a target network.

